"""
train.py — Fine-tuning BERT for legal document classification.

Label schema:
  0 = Contract
  1 = Court Ruling
  2 = Legal Notice
  3 = Agreement
  4 = Patent

Training data strategy (two-pass):
  1. CUAD (Contract Understanding Atticus Dataset) via HuggingFace `datasets`
     — real-world legal contracts, mapped to our 5-class schema.
  2. Curated seed samples (below) used as a supplement for underrepresented
     classes (Court Ruling, Legal Notice, Patent) not covered well by CUAD.

Training improvements over v1:
  - Linear LR warmup + cosine decay via get_linear_schedule_with_warmup.
  - Gradient clipping (max_norm=1.0) to prevent exploding gradients.
  - Per-epoch validation accuracy logged to training_log.jsonl.
  - Evaluation prints classification_report for per-class F1.
"""

import json
import time
import torch
from pathlib import Path
from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LABEL_NAMES = ["Contract", "Court Ruling", "Legal Notice", "Agreement", "Patent"]
NUM_LABELS = len(LABEL_NAMES)
MODEL_NAME = "bert-base-uncased"
SAVE_DIR = Path("models/bert_model")
LOG_FILE = Path("training_log.jsonl")
MAX_LEN = 256
BATCH_SIZE = 8
EPOCHS = 3
LR = 2e-5
WARMUP_RATIO = 0.1      # 10% of total steps used for warmup
GRAD_CLIP = 1.0


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class LegalDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[int], tokenizer):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
        }


# ---------------------------------------------------------------------------
# CUAD data loader
# ---------------------------------------------------------------------------

def load_cuad_data() -> tuple[list[str], list[int]]:
    """
    Load the CUAD dataset (HuggingFace hub) and map contract passages to our
    5-class label schema.

    CUAD is a QA-format dataset where each example has a contract context and
    a category question.  We use the context text and infer our label from the
    category name:

      CUAD category → our label
      ─────────────────────────
      Any "Agreement" / "Contract" type  → 0 (Contract)
      Any "Notice" type                  → 2 (Legal Notice)
      "Patent" or "IP"                   → 4 (Patent)
      Everything else                    → 0 (Contract, default)

    Court Ruling (1) and Agreement (3) are not well represented in CUAD, so
    we rely on the seed samples for those classes.

    Returns (texts, labels) — may be empty if `datasets` is not installed or
    the download fails, in which case training falls back to seed data only.
    """
    try:
        from datasets import load_dataset  # pip install datasets
    except ImportError:
        print("[CUAD] `datasets` package not installed — skipping CUAD.")
        print("       Run: pip install datasets")
        return [], []

    print("[CUAD] Downloading CUAD dataset from HuggingFace Hub…")
    try:
        ds = load_dataset("theatticusproject/cuad", split="train", trust_remote_code=True)
    except Exception as exc:
        print(f"[CUAD] Download failed ({exc}) — falling back to seed data only.")
        return [], []

    texts, labels = [], []
    for example in ds:
        context: str = example.get("context", "") or ""
        context = context.strip()
        if not context or len(context) < 50:
            continue

        # Truncate to first 400 chars for speed; BERT sees 256 tokens anyway
        excerpt = context[:400]

        # Map to our label based on the category field
        category: str = (example.get("title") or example.get("category") or "").lower()

        if "patent" in category or "intellectual property" in category:
            label = 4
        elif "notice" in category:
            label = 2
        elif "agreement" in category and "non" not in category:
            label = 3
        else:
            label = 0  # Contract (most CUAD entries are contracts)

        texts.append(excerpt)
        labels.append(label)

    # Cap at 2000 CUAD samples (balanced down-sampling per class)
    from collections import defaultdict
    per_class: dict[int, list[str]] = defaultdict(list)
    for t, l in zip(texts, labels):
        per_class[l].append(t)

    cap_per_class = 400
    balanced_texts, balanced_labels = [], []
    for lbl, txts in per_class.items():
        sample = txts[:cap_per_class]
        balanced_texts.extend(sample)
        balanced_labels.extend([lbl] * len(sample))

    print(f"[CUAD] Loaded {len(balanced_texts)} samples across {len(per_class)} classes.")
    return balanced_texts, balanced_labels


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(model, loader, device) -> tuple[list, list]:
    """Run inference and return (true_labels, pred_labels)."""
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(batch["label"].numpy())
    return all_labels, all_preds


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(
    train_texts: list[str],
    train_labels: list[int],
    test_texts: list[str],
    test_labels: list[int],
) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)

    train_dataset = LegalDataset(train_texts, train_labels, tokenizer)
    test_dataset = LegalDataset(test_texts, test_labels, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=NUM_LABELS)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)

    total_steps = len(train_loader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    print(f"Training on {len(train_texts)} samples | Validation on {len(test_texts)} samples")
    print(f"Device: {device} | Epochs: {EPOCHS} | LR: {LR} | Warmup steps: {warmup_steps}\n")

    training_log = []

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        epoch_start = time.time()

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels_batch = batch["label"].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels_batch,
            )
            loss = outputs.loss
            loss.backward()

            # Gradient clipping — prevents exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)

            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        # ── Per-epoch validation ───────────────────────────────────────────
        true_labels, pred_labels = evaluate_model(model, test_loader, device)
        val_acc = accuracy_score(true_labels, pred_labels)
        avg_loss = total_loss / len(train_loader)
        elapsed = time.time() - epoch_start

        print(
            f"Epoch {epoch + 1}/{EPOCHS} | "
            f"loss: {avg_loss:.4f} | "
            f"val_acc: {val_acc:.4f} | "
            f"time: {elapsed:.1f}s"
        )

        log_entry = {
            "epoch": epoch + 1,
            "avg_train_loss": round(avg_loss, 6),
            "val_accuracy": round(val_acc, 6),
            "elapsed_seconds": round(elapsed, 1),
        }
        training_log.append(log_entry)
        LOG_FILE.write_text(
            "\n".join(json.dumps(entry) for entry in training_log) + "\n"
        )

    # ── Save model ─────────────────────────────────────────────────────────
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(SAVE_DIR))
    tokenizer.save_pretrained(str(SAVE_DIR))
    print(f"\nModel saved to {SAVE_DIR}")
    print(f"Training log saved to {LOG_FILE}")

    # ── Final evaluation ───────────────────────────────────────────────────
    true_labels, pred_labels = evaluate_model(model, test_loader, device)
    acc = accuracy_score(true_labels, pred_labels)
    cm = confusion_matrix(true_labels, pred_labels, labels=list(range(NUM_LABELS)))

    print(f"\nFinal Test Accuracy: {acc * 100:.2f}%\n")

    print("Classification Report:")
    print(classification_report(true_labels, pred_labels, target_names=LABEL_NAMES))

    print("Confusion Matrix (rows = true, cols = predicted):")
    header = f"{'':15s}" + "".join(f"{name:>14s}" for name in LABEL_NAMES)
    print(header)
    for i, row in enumerate(cm):
        row_str = f"{LABEL_NAMES[i]:15s}" + "".join(f"{val:>14d}" for val in row)
        print(row_str)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # ── Seed samples (always included) ────────────────────────────────────
    # Label 0 = Contract
    contract_texts = [
        "This contract is legally binding and governs the sale of goods between the parties.",
        "The parties agree to the terms and conditions set forth in this service agreement.",
        "This purchase agreement is entered into as of the date signed by both parties.",
        "Failure to perform under this contract shall result in liquidated damages.",
        "The contractor shall complete the work within the timeline specified herein.",
        "This employment contract outlines the obligations and compensation of the employee.",
        "All intellectual property created under this contract belongs to the employer.",
        "Either party may terminate this contract with 30 days written notice.",
        "The vendor warrants that all goods delivered are free from material defects.",
        "This software license agreement grants a non-exclusive right to use the product.",
        "Confidentiality obligations under this contract survive termination for five years.",
        "The parties agree that disputes shall be resolved via binding arbitration.",
        "This construction contract requires compliance with all local building codes.",
        "Payment is due within 30 days of invoice receipt under this supply agreement.",
        "This non-disclosure agreement prohibits sharing proprietary information with third parties.",
        "The contractor must maintain adequate insurance coverage throughout the contract term.",
    ]

    # Label 1 = Court Ruling
    court_ruling_texts = [
        "The court finds the defendant guilty of breach of contract and awards damages.",
        "The appellate court reversed the lower court's decision on procedural grounds.",
        "The Supreme Court held that the statute was unconstitutional as applied.",
        "The court dismissed the plaintiff's complaint for lack of standing.",
        "The judge granted summary judgment in favor of the defendant.",
        "The jury returned a verdict of not guilty on all counts.",
        "The court ordered the defendant to pay compensatory and punitive damages.",
        "The tribunal upheld the administrative agency's decision regarding the permit.",
        "The court granted a preliminary injunction preventing the defendant from operating.",
        "The court ruled that the evidence was inadmissible under the exclusionary rule.",
        "The bench found the witness testimony credible and accepted it into the record.",
        "The court issued a writ of mandamus compelling the official to act.",
        "The appellate panel affirmed the lower court's ruling on all issues.",
        "The judge sentenced the defendant to three years of probation and community service.",
        "The court found in favor of the plaintiff and awarded attorney's fees.",
        "The order of the court directed both parties to attend mediation.",
    ]

    # Label 2 = Legal Notice
    legal_notice_texts = [
        "This is a legal notice informing you of your obligation to vacate the premises.",
        "You are hereby notified that legal action will be taken if payment is not received.",
        "Notice is given that the annual general meeting will be held on the stated date.",
        "This cease-and-desist notice demands that you immediately stop infringing our trademark.",
        "Legal notice is hereby served regarding unpaid dues on the above-referenced property.",
        "You are notified of your right to dispute this debt within 30 days of receipt.",
        "This notice informs tenants of upcoming inspection of the rental property.",
        "Notice of default is hereby issued for failure to make mortgage payments.",
        "This legal notice concerns the termination of your utility service for non-payment.",
        "Public notice is given that the zoning ordinance will be amended at next month's meeting.",
        "You are hereby put on notice that any trespass will be prosecuted to the full extent.",
        "This notice serves to inform you that your lease will not be renewed.",
        "Legal notice is given that the estate of the deceased is being administered.",
        "Notice of lien is filed against the property described herein for unpaid taxes.",
        "You are notified that your vehicle has been impounded and must be claimed within 10 days.",
        "This statutory notice is issued pursuant to Section 13 of the relevant act.",
    ]

    # Label 3 = Agreement
    agreement_texts = [
        "This agreement is made between two parties to govern their business relationship.",
        "The parties have reached a mutual agreement on the terms of the joint venture.",
        "This settlement agreement resolves all outstanding claims between the parties.",
        "The memorandum of understanding sets forth the preliminary terms of cooperation.",
        "Both parties agree to share revenues equally under the terms of this partnership.",
        "This licensing agreement permits the licensee to use the patent for a fixed term.",
        "The parties entered into a non-compete agreement effective upon termination.",
        "This shareholders' agreement governs the rights and obligations of all equity holders.",
        "The collaboration agreement defines the scope of work for the joint research project.",
        "This escrow agreement designates a neutral third party to hold funds in trust.",
        "The distribution agreement grants exclusive rights to sell products in the territory.",
        "Both parties acknowledge the terms of this mediation agreement as binding.",
        "The franchise agreement establishes the rights of the franchisee to operate the brand.",
        "This operating agreement governs the internal affairs of the limited liability company.",
        "The parties have executed this forbearance agreement to delay enforcement of the loan.",
        "This co-authorship agreement specifies each party's contribution and royalty share.",
    ]

    # Label 4 = Patent
    patent_texts = [
        "Patent application for a novel method of synthesizing pharmaceutical compounds.",
        "This invention relates to an improved design for a rechargeable lithium-ion battery.",
        "The patent claims priority from the provisional application filed in the prior year.",
        "A patent is sought for a machine learning algorithm that classifies legal documents.",
        "This utility patent covers a new and useful process for water purification.",
        "The invention discloses a semiconductor device with improved thermal conductivity.",
        "The patent application includes claims directed to a novel polymer composition.",
        "A design patent is requested for the ornamental appearance of the mobile device.",
        "The prior art search revealed no existing patents on the described mechanism.",
        "This patent covers a software system for real-time fraud detection in banking.",
        "The claims of this patent are directed to a method of compressing video data.",
        "An international patent application was filed under the PCT for global protection.",
        "The specification describes preferred embodiments of the claimed invention in detail.",
        "The patent discloses a biodegradable material suitable for food packaging applications.",
        "This continuation patent application adds new claims to the parent patent.",
        "The invention relates to a wearable biosensor that monitors glucose levels continuously.",
    ]

    seed_texts = (
        contract_texts + court_ruling_texts + legal_notice_texts +
        agreement_texts + patent_texts
    )
    seed_labels = (
        [0] * len(contract_texts) +
        [1] * len(court_ruling_texts) +
        [2] * len(legal_notice_texts) +
        [3] * len(agreement_texts) +
        [4] * len(patent_texts)
    )

    # ── CUAD data (real-world contracts) ───────────────────────────────────
    cuad_texts, cuad_labels = load_cuad_data()

    # ── Merge seed + CUAD ──────────────────────────────────────────────────
    all_texts = seed_texts + cuad_texts
    all_labels = seed_labels + cuad_labels

    print(f"Total dataset size: {len(all_texts)} samples")

    # ── Train / test split (stratified) ───────────────────────────────────
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        all_texts,
        all_labels,
        test_size=0.20,
        random_state=42,
        stratify=all_labels,
    )

    train_model(train_texts, train_labels, test_texts, test_labels)