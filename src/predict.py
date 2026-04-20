import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax

# Replace generic LABEL_0, LABEL_1 ... with recruiter-friendly names
LABEL_MAP = {
    0: "Employment Contract",
    1: "Non-Disclosure Agreement (NDA)",
    2: "Service Agreement",
    3: "Privacy Policy",
    4: "Vendor Agreement"
}


class LegalDocumentPredictor:
    def __init__(self, model_name: str | None = None):
        # Use Hugging Face model repo instead of local folder
        self.model_name = model_name or os.getenv(
            "HF_MODEL_NAME",
            "appster777/legal-doc-classifier"
        )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

        config = self.model.config
        self.id2label = getattr(config, "id2label", None)

        # If model config has missing / generic labels, use better business labels
        if not self.id2label or len(self.id2label) == 0:
            num_labels = getattr(config, "num_labels", 2)
            if num_labels == len(LABEL_MAP):
                self.id2label = LABEL_MAP
            else:
                self.id2label = {i: f"Class_{i}" for i in range(num_labels)}
        else:
            # Clean labels if model still stores LABEL_0 style names
            cleaned_id2label = {}
            num_labels = getattr(config, "num_labels", len(self.id2label))

            for i in range(num_labels):
                raw_label = self.id2label.get(i, f"LABEL_{i}")
                if str(raw_label).startswith("LABEL_") and i in LABEL_MAP:
                    cleaned_id2label[i] = LABEL_MAP[i]
                else:
                    cleaned_id2label[i] = str(raw_label)

            self.id2label = cleaned_id2label

        self.labels = [self.id2label[i] for i in sorted(self.id2label.keys())]

    def predict(self, text: str) -> dict:
        if not text or not text.strip():
            return {
                "label": "Unknown",
                "confidence": 0.0,
                "top_predictions": [],
                "probabilities": {}
            }

        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256
        )

        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = self.model(**encoded)
            probs = softmax(outputs.logits, dim=-1).cpu().numpy()[0]

        pred_idx = int(probs.argmax())
        pred_label = self.id2label.get(pred_idx, f"Class_{pred_idx}")
        pred_conf = float(probs[pred_idx])

        probabilities = {
            self.id2label.get(i, f"Class_{i}"): round(float(prob), 6)
            for i, prob in enumerate(probs)
        }

        sorted_probs = sorted(
            probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_predictions = [
            {
                "label": label,
                "confidence": round(confidence, 4)
            }
            for label, confidence in sorted_probs[:3]
        ]

        return {
            "label": pred_label,
            "confidence": round(pred_conf, 4),
            "top_predictions": top_predictions,
            "probabilities": probabilities
        }


_PREDICTOR = None


def get_predictor() -> LegalDocumentPredictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = LegalDocumentPredictor()
    return _PREDICTOR


def predict(text: str) -> dict:
    return get_predictor().predict(text)