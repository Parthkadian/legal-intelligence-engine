from pathlib import Path
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


LEGAL_PRIORITY_TERMS = {
    "termination", "terminate", "liability", "liable", "damages", "penalty",
    "confidential", "confidentiality", "disclosure", "nda",
    "payment", "payments", "fees", "invoice", "pricing", "compensation",
    "breach", "default", "obligation", "obligations", "duty", "duties",
    "indemnity", "indemnify", "warranty", "warranties",
    "jurisdiction", "governing", "law", "court", "arbitration",
    "notice", "timeline", "delivery", "services", "vendor", "client",
    "employee", "employment", "contract", "agreement", "policy", "privacy"
}


class LegalExplainer:
    def __init__(self, model_dir: str | None = None):
        project_root = Path(__file__).resolve().parent.parent
        self.model_dir = Path(model_dir) if model_dir else project_root / "models" / "bert_model"

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
        self.model.to(self.device)
        self.model.eval()

    def _clean_token(self, token: str) -> str:
        token = token.replace("##", "")
        token = token.strip()
        token = re.sub(r"^[^\w]+|[^\w]+$", "", token)
        return token

    def _is_valid_token(self, token: str) -> bool:
        if not token:
            return False

        token_lower = token.lower()

        invalid_tokens = {
            "[cls]", "[sep]", "[pad]", "cls", "sep", "pad",
            "the", "and", "for", "are", "was", "were", "has", "had",
            "this", "that", "with", "from", "into", "upon", "than",
            "your", "their", "shall", "hereby", "thereof", "whereas",
            "between", "subject", "about", "would", "could", "should",
            "such", "which", "whose", "whom", "been", "being", "have",
            "having", "will", "under", "over", "into", "very"
        }

        if token_lower in invalid_tokens:
            return False

        if len(token_lower) < 4:
            return False

        if token_lower.isdigit():
            return False

        if re.fullmatch(r"[_\W]+", token_lower):
            return False

        return True

    def _boost_score(self, word: str, score: float, text_lower: str) -> float:
        word_lower = word.lower()
        boosted = score

        if word_lower in LEGAL_PRIORITY_TERMS:
            boosted *= 1.35

        if word_lower in text_lower:
            boosted *= 1.05

        if len(word_lower) >= 8:
            boosted *= 1.03

        return boosted

    def explain(self, text: str, top_k: int = 8) -> list:
        if not text or not text.strip():
            return [{"word": "content", "score": 1.0}]

        try:
            encoded = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256
            )

            input_ids = encoded["input_ids"].to(self.device)
            attention_mask = encoded["attention_mask"].to(self.device)

            embeddings = self.model.get_input_embeddings()(input_ids)
            embeddings = embeddings.detach().clone().requires_grad_(True)

            outputs = self.model(
                inputs_embeds=embeddings,
                attention_mask=attention_mask
            )

            pred_idx = outputs.logits.argmax(dim=-1)
            selected_logit = outputs.logits[0, pred_idx]
            self.model.zero_grad()
            selected_logit.backward()

            grads = embeddings.grad
            if grads is None:
                raise ValueError("Gradients are None.")

            token_scores = grads.norm(dim=-1).squeeze(0).detach().cpu().tolist()
            tokens = self.tokenizer.convert_ids_to_tokens(input_ids.squeeze(0))
            text_lower = text.lower()

            items = []
            for token, score in zip(tokens, token_scores):
                token = self._clean_token(token)

                if not self._is_valid_token(token):
                    continue

                boosted_score = self._boost_score(token, float(score), text_lower)
                items.append({"word": token.lower(), "score": boosted_score})

            merged = {}
            for item in items:
                word = item["word"]
                merged[word] = max(merged.get(word, 0.0), item["score"])

            ranked = sorted(
                [{"word": k, "score": round(v, 4)} for k, v in merged.items()],
                key=lambda x: x["score"],
                reverse=True
            )

            ranked = self._postprocess_ranked_words(ranked, text, top_k)

            if ranked:
                return ranked[:top_k]

            raise ValueError("No ranked explanation tokens found.")

        except Exception:
            return self._fallback_keywords(text, top_k=top_k)

    def _postprocess_ranked_words(self, ranked: list, text: str, top_k: int) -> list:
        text_lower = text.lower()
        final_items = []
        used = set()

        for item in ranked:
            word = item["word"]

            if word in used:
                continue

            if not self._is_valid_token(word):
                continue

            if word.endswith("ing") and len(word) > 10:
                pass

            used.add(word)
            final_items.append(item)

        
        legal_items = [item for item in final_items if item["word"] in LEGAL_PRIORITY_TERMS]
        non_legal_items = [item for item in final_items if item["word"] not in LEGAL_PRIORITY_TERMS]

        combined = legal_items + non_legal_items

        
        generic_words = {
            "agreement", "contract", "document", "party", "parties",
            "terms", "service", "services", "policy"
        }

        if any(item["word"] in LEGAL_PRIORITY_TERMS - generic_words for item in combined):
            combined = [
                item for item in combined
                if item["word"] not in generic_words
                or item["word"] in {"agreement", "contract"}
            ]

        if not combined:
            return self._fallback_keywords(text, top_k)

        return combined[:top_k]

    def _fallback_keywords(self, text: str, top_k: int = 8) -> list:
        text_lower = text.lower()

        words = re.findall(r"\b[a-zA-Z]{4,}\b", text_lower)
        stopwords = {
            "this", "that", "with", "from", "have", "will", "shall", "agreement",
            "party", "parties", "document", "legal", "under", "thereof", "whereas",
            "which", "their", "such", "hereby", "between", "subject", "terms",
            "into", "upon", "your", "these", "those", "being", "been", "also",
            "would", "could", "should", "there", "about", "after", "before",
            "during", "while", "where", "when"
        }

        freq = {}
        for word in words:
            if word not in stopwords and len(word) >= 4:
                base_score = freq.get(word, 0) + 1
                if word in LEGAL_PRIORITY_TERMS:
                    base_score += 2
                freq[word] = base_score

        ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        results = [{"word": w, "score": float(s)} for w, s in ranked[:top_k]]

        if results:
            return results

        
        emergency_terms = []
        for term in sorted(LEGAL_PRIORITY_TERMS):
            if term in text_lower:
                emergency_terms.append({"word": term, "score": 1.0})
            if len(emergency_terms) >= top_k:
                break

        if emergency_terms:
            return emergency_terms

        return [{"word": "content", "score": 1.0}]


_EXPLAINER = None


def get_explainer():
    global _EXPLAINER
    if _EXPLAINER is None:
        _EXPLAINER = LegalExplainer()
    return _EXPLAINER


def explain_text(text: str, top_k: int = 8) -> list:
    return get_explainer().explain(text, top_k=top_k)