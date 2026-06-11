"""
Pre-download HuggingFace models into the Docker image at build time.
This avoids cold-start delays and OOM errors on Railway.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import AutoModelForQuestionAnswering

print("Downloading legal classifier model...")
AutoTokenizer.from_pretrained("briefme-io/legal_document_classifier")
AutoModelForSequenceClassification.from_pretrained("briefme-io/legal_document_classifier")
print("Legal classifier downloaded.")

print("Downloading QA model...")
AutoTokenizer.from_pretrained("distilbert-base-cased-distilled-squad")
AutoModelForQuestionAnswering.from_pretrained("distilbert-base-cased-distilled-squad")
print("QA model downloaded.")

print("All models ready.")
