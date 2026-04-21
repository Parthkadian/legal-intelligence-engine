import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax

LABEL_MAP = {
    0: "Employment Contract",
    1: "Non-Disclosure Agreement (NDA)",
    2: "Service Agreement",
    3: "Privacy Policy",
    4: "Vendor Agreement"
}

class LegalDocumentPredictor:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv(
            "HF_MODEL_NAME",
            "appster777/legal-doc-classifier"
        )

        # 🔥 FORCE CPU (important for Render)
        self.device = torch.device("cpu")

        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        print("Loading model...")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )

        self.model.to(self.device)
        self.model.eval()

        config = self.model.config
        self.id2label = getattr(config, "id2label", None)

        if not self.id2label or len(self.id2label) == 0:
            num_labels = getattr(config, "num_labels", 2)
            if num_labels == len(LABEL_MAP):
                self.id2label = LABEL_MAP
            else:
                self.id2label = {i: f"Class_{i}" for i in range(num_labels)}
        else:
            cleaned = {}
            for i in range(len(self.id2label)):
                raw = self.id2label.get(i, f"LABEL_{i}")
                if str(raw).startswith("LABEL_") and i in LABEL_MAP:
                    cleaned[i] = LABEL_MAP[i]
                else:
                    cleaned[i] = str(raw)
            self.id2label = cleaned

        self.labels = [self.id2label[i] for i in sorted(self.id2label.keys())]

        print("✅ Model loaded successfully")

    def predict(self, text: str) -> dict:
        try:
            if not text or not text.strip():
                return {
                    "label": "Unknown",
                    "confidence": 0.0,
                    "top_predictions": [],
                    "probabilities": {}
                }

            # 🔥 LIMIT INPUT SIZE (CRITICAL)
            text = text[:1000]

            encoded = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=128   # 🔥 REDUCED
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

            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

            top_predictions = [
                {"label": label, "confidence": round(conf, 4)}
                for label, conf in sorted_probs[:3]
            ]

            return {
                "label": pred_label,
                "confidence": round(pred_conf, 4),
                "top_predictions": top_predictions,
                "probabilities": probabilities
            }

        except Exception as e:
            print("❌ Prediction error:", str(e))
            return {
                "label": "Error",
                "confidence": 0.0,
                "top_predictions": [],
                "probabilities": {},
                "error": str(e)
            }


# 🔥 GLOBAL SINGLE INSTANCE (VERY IMPORTANT)
_PREDICTOR = None

def get_predictor():
    global _PREDICTOR
    if _PREDICTOR is None:
        print("Initializing predictor...")
        _PREDICTOR = LegalDocumentPredictor()
    return _PREDICTOR


def predict(text: str):
    return get_predictor().predict(text)