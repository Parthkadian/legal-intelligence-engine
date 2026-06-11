<div align="center">

<!-- Banner -->
<img src="https://img.shields.io/badge/-%E2%9A%96%EF%B8%8F%20Legal%20Intelligence%20Engine-0a0f1e?style=for-the-badge&labelColor=0a0f1e" alt="Legal Intelligence Engine" width="100%"/>

<h1>⚖️ Legal Intelligence Engine</h1>
<h3><em>Enterprise-Grade AI for Legal Document Analysis & Risk Intelligence</em></h3>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3.1-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-pytest-6B7280?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)

<br/>

> **A production-ready, end-to-end AI platform** that classifies legal documents, extracts named entities, scores contractual risk, and delivers actionable clause-level intelligence — all powered by fine-tuned BERT, zero-shot NLI, and gradient-based explainability, served through a decoupled FastAPI microservice and an interactive Streamlit dashboard.

<br/>

[**🚀 Quick Start**](#-quickstart-docker) · [**📖 API Reference**](#-api-reference) · [**🏗️ Architecture**](#%EF%B8%8F-system-architecture) · [**🧠 ML Models**](#-ml-pipeline--models) · [**🧪 Testing**](#-testing) · [**🤝 Contributing**](#-contributing)

</div>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [System Architecture](#️-system-architecture)
- [ML Pipeline & Models](#-ml-pipeline--models)
- [Tech Stack](#-tech-stack)
- [Quickstart: Docker](#-quickstart-docker)
- [Local Development](#-local-development)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Configuration](#️-configuration)
- [Testing](#-testing)
- [Performance & Benchmarks](#-performance--benchmarks)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Project Overview

The **Legal Intelligence Engine** addresses a critical pain point in legal operations: the manual review of complex legal documents is time-consuming, error-prone, and expensive. This platform automates the entire analysis lifecycle using a multi-model AI pipeline:

1. **Classify** the document type with a fine-tuned BERT classifier
2. **Extract** named entities (persons, organisations, dates, monetary values, legislation)
3. **Explain** which tokens drove the classification decision (gradient saliency / SHAP)
4. **Detect** the presence or absence of 10 standard contractual clauses using a two-pass hybrid approach (zero-shot NLI + keyword fallback)
5. **Score** overall contract risk on a 0–100 scale and generate executive summaries, business impact notes, and actionable recommendations
6. **Answer** natural language questions about the document via an integrated DistilBERT QA engine
7. **Export** structured PDF reports and persist every analysis to a SQLite history store

This is not a demo — it is a production-architected system with lazy model loading, Docker-compose orchestration, a dedicated database layer, and a comprehensive pytest suite.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Deep Learning Classification** | Fine-tuned `bert-base-uncased` / hosted HuggingFace model classifies documents into Employment Contract, NDA, Service Agreement, Privacy Policy, and Vendor Agreement |
| 🔍 **Named Entity Recognition** | Two-pass NER: spaCy `en_core_web_sm` (context-aware) + regex fallback for dates, monetary values, legislation, orgs, and titled persons |
| 💡 **Gradient-based Explainability** | Token saliency via input-gradient norms with legal-term priority boosting; SHAP `PartitionExplainer` as a stable alternative |
| ⚠️ **Clause Detection & Risk Scoring** | Hybrid NLI + keyword engine detects 10 standard clauses; computes a weighted 0–100 risk score |
| 📊 **Executive Intelligence** | Auto-generated insights, business impact analysis, mitigation recommendations, and executive summaries |
| 💬 **Document QA Chat** | Natural language Q&A over any analysed document using `distilbert-base-cased-distilled-squad` |
| 📄 **PDF Report Export** | One-click structured PDF download of full analysis results from the Streamlit UI |
| 🗄️ **Persistent History** | All predictions stored in SQLite; live stats (total docs, high-risk flags) surfaced via `/stats` API |
| 🐳 **Docker Microservices** | Backend (FastAPI/Uvicorn) and Frontend (Streamlit) run in independent containers orchestrated by Docker Compose |
| 🔒 **Identity Document Guard** | Keyword shortcut prevents identity documents (Aadhaar, Passport, PAN, Driving License) from being processed as contracts |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                              │
│                    Streamlit UI  (:8501)                            │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│   │  Document    │  │  Risk &      │  │  Analysis History &      │ │
│   │  Upload /    │  │  Clause      │  │  Statistics Dashboard    │ │
│   │  Text Input  │  │  Dashboard   │  │  + PDF Export            │ │
│   └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘ │
└──────────┼─────────────────┼───────────────────────────────────────┘
           │   REST (JSON)   │
           ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  (:8000)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     /predict  (POST)                         │   │
│  │  ┌────────────┐  ┌─────────┐  ┌──────────┐  ┌───────────┐  │   │
│  │  │ BERT       │  │ spaCy   │  │ Gradient │  │ Zero-shot │  │   │
│  │  │ Classifier │→ │ + Regex │→ │ / SHAP   │→ │ NLI Risk  │  │   │
│  │  │ (predict)  │  │ NER     │  │ Explainer│  │ Detector  │  │   │
│  │  └────────────┘  └─────────┘  └──────────┘  └───────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────────────┐  │
│  │ /chat      │  │ /history      │  │ /stats                    │  │
│  │ DistilBERT │  │ SQLite GET    │  │ Aggregated counts         │  │
│  │ QA Engine  │  │               │  │                           │  │
│  └────────────┘  └───────────────┘  └───────────────────────────┘  │
│                                                                     │
│               ┌─────────────────────────────┐                      │
│               │   SQLite  (predictions.db)  │                      │
│               └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow for a Single Document Analysis

```
User Input → Identity Guard Check
           ↓ (if not identity doc)
      BERT Classification → {label, confidence, top_3_predictions}
           ↓
      spaCy NER + Regex Fallback → {entities}
           ↓
      Gradient Explainer (input × ∂loss/∂embed) → {token_saliency}
           ↓
      Zero-shot NLI (DistilBERT-MNLI) → Clause Detection
           ↓ (fallback if confidence < 0.55)
      Keyword Matching → Final Clause Map
           ↓
      Risk Scoring Engine → {score: 0-100, level, insights, impact, recs}
           ↓
      Executive Summary → Consolidated JSON Response
           ↓
      SQLite Persist → History & Stats
```

---

## 🧠 ML Pipeline & Models

### 1. Document Classification — Fine-tuned BERT

| Setting | Value |
|---|---|
| Base model | `bert-base-uncased` (via HuggingFace Hub) |
| Hosted model | `appster777/legal-doc-classifier` |
| Task | 5-class sequence classification |
| Labels | Employment Contract · NDA · Service Agreement · Privacy Policy · Vendor Agreement |
| Max token length | 128 tokens |
| Training data | CUAD dataset (real contracts, ≤2,000 balanced samples) + 80 curated seed samples |
| Optimiser | AdamW · lr=2e-5 · weight_decay=0.01 |
| Scheduler | Linear warmup (10%) + cosine decay |
| Gradient clipping | max_norm=1.0 |
| Epochs | 3 |

Training produces per-epoch validation accuracy logs (`training_log.jsonl`) and a final classification report with per-class F1 scores.

### 2. Clause Detection — Hybrid NLI + Keywords

Two-pass detection for **10 contractual clauses**:

| Clause | Risk Weight |
|---|---|
| Termination Clause | +25 pts |
| Liability Clause | +25 pts |
| Missing Payment Clause | +20 pts |
| Non-compete Clause | +15 pts |
| Data Privacy Clause | +15 pts |
| Confidentiality Clause | +10 pts |
| Indemnity Clause | +10 pts |
| Jurisdiction Clause | +10 pts |
| Missing Force Majeure | +10 pts |
| Arbitration Clause | +5 pts |

**Pass 1:** `typeform/distilbert-base-uncased-mnli` zero-shot classification — each clause hypothesis scored independently (`multi_label=True`). Clauses scoring ≥ 0.55 are marked present.

**Pass 2:** Per-clause keyword fallback for uncertain results (< 0.55 confidence) or if the NLI model is unavailable. Prevents false positives like *"termination of my lunch break"* that fool pure keyword matching.

### 3. Explainability — Gradient Saliency & SHAP

**Gradient method (default):**
- Computes `‖∂logit/∂embed‖₂` for each input token
- Boosts legal priority terms by 1.35×
- Filters stop words, punctuation, and BERT special tokens
- Returns top-8 attribution tokens

**SHAP alternative (`explain_with_shap`):**
- Uses `shap.Explainer` wrapping a HuggingFace text-classification pipeline
- Returns absolute SHAP values for the predicted class
- Gracefully falls back to gradient method if `shap` is not installed

### 4. Named Entity Recognition — spaCy + Regex

| Entity Type | Source |
|---|---|
| PERSON, ORG, DATE, MONEY, GPE, LOC | spaCy `en_core_web_sm` |
| DATE (structured), MONEY (multi-currency) | Regex fallback |
| LAW (GDPR, CCPA, Indian Contract Act…) | Regex |
| ORG (Ltd, LLC, LLP, Private Limited…) | Regex |
| PERSON (titled: Mr/Mrs/Ms/Dr) | Regex |

Both passes are merged, deduplicated, filtered for noise tokens, and capped at 12 entities.

### 5. Document Q&A — DistilBERT SQuAD

- Model: `distilbert-base-cased-distilled-squad`
- Interface: `/chat` endpoint accepts `{context, question}` and returns extracted answer spans
- Lazy-loaded on first chat request to minimise startup time

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **API Framework** | FastAPI + Uvicorn | 0.111.1 / 0.30.1 |
| **Data Validation** | Pydantic | 2.7.4 |
| **Deep Learning** | PyTorch | 2.3.1 |
| **Transformers** | HuggingFace Transformers | 4.41.2 |
| **Explainability** | SHAP | 0.45.1 |
| **NLP** | spaCy (`en_core_web_sm`) | 3.7.5 |
| **ML Utilities** | scikit-learn, NumPy, pandas | 1.5.0 / 1.26.4 / 2.2.2 |
| **PDF Generation** | fpdf2 | 2.7.9 |
| **Document Parsing** | PyMuPDF, pdfplumber, python-docx | 1.24.5 / 0.11.1 / 1.1.2 |
| **Frontend** | Streamlit | 1.35.0 |
| **Database** | SQLite3 (stdlib) | — |
| **Containerisation** | Docker + Docker Compose | — |
| **Testing** | pytest, pytest-mock, httpx | 8.2.2 / 3.14.0 / 0.27.0 |

---

## 🐳 Quickstart: Docker

The fastest way to run the full stack locally.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- ~3 GB free disk space (for model weights and Docker layers)

### Launch

```bash
# 1. Clone the repository
git clone https://github.com/Parthkadian/legal-intelligence-engine.git
cd legal-intelligence-engine

# 2. Build and start both services
docker-compose up --build
```

> **Note:** The first build downloads PyTorch, HuggingFace model weights (~2–3 GB), and spaCy models. Subsequent starts use the Docker layer cache and are significantly faster.

### Access the Services

| Service | URL | Description |
|---|---|---|
| **Streamlit UI** | http://localhost:8501 | Interactive analysis dashboard |
| **FastAPI (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **FastAPI (ReDoc)** | http://localhost:8000/redoc | Alternative API reference |
| **Health Check** | http://localhost:8000/health | Service liveness probe |

### Stop

```bash
docker-compose down
```

---

## 💻 Local Development

For active development without Docker:

### 1. Environment Setup

```bash
# Clone and enter the project
git clone https://github.com/Parthkadian/legal-intelligence-engine.git
cd legal-intelligence-engine

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 4. Start the Backend API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at `http://localhost:8000`. Models load lazily on the first request.

### 5. Start the Frontend UI

Open a second terminal (with the venv activated):

```bash
streamlit run ui/app.py
```

The dashboard will open at `http://localhost:8501`.

---

## 📡 API Reference

All endpoints return JSON. The `/predict` endpoint is the core of the system.

### `POST /predict`

Perform a full analysis on a legal document text.

**Request Body:**

```json
{
  "text": "This Employment Contract is entered into between Acme Corp Ltd and Dr. John Smith..."
}
```

**Response (200 OK):**

```json
{
  "label": "Employment Contract",
  "confidence": 0.9421,
  "probabilities": {
    "Employment Contract": 0.9421,
    "Non-Disclosure Agreement (NDA)": 0.0312,
    "Service Agreement": 0.0184,
    "Privacy Policy": 0.0053,
    "Vendor Agreement": 0.003
  },
  "top_predictions": [
    { "label": "Employment Contract", "confidence": 0.9421 },
    { "label": "Non-Disclosure Agreement (NDA)", "confidence": 0.0312 },
    { "label": "Service Agreement", "confidence": 0.0184 }
  ],
  "entities": [
    { "text": "Acme Corp Ltd", "label": "ORG" },
    { "text": "Dr. John Smith", "label": "PERSON" }
  ],
  "explanation": [
    { "word": "employment", "score": 4.8821 },
    { "word": "termination", "score": 3.7102 }
  ],
  "clauses": {
    "Termination Clause": true,
    "Payment Clause": true,
    "Liability Clause": false,
    "Confidentiality Clause": true,
    "Indemnity Clause": false,
    "Jurisdiction Clause": true,
    "Arbitration Clause": false,
    "Force Majeure Clause": false,
    "Non-compete Clause": true,
    "Data Privacy Clause": false
  },
  "risk_score": 65,
  "risk_level": "Medium",
  "insights": [
    "Termination clause detected → ensure exit conditions are clearly defined",
    "Non-compete clause restricts post-termination activities"
  ],
  "business_impact": [
    "Contract exit conditions present → requires careful validation",
    "Restrictive business operations post-termination"
  ],
  "recommendations": [
    "Review termination conditions to avoid unfair exit risks",
    "Consider adding Force Majeure to protect against extreme events"
  ],
  "executive_summary": {
    "document_type": "Employment Contract",
    "risk_score": 65,
    "risk_level": "Medium",
    "main_concern": "No major risks detected",
    "action": "Review recommended"
  },
  "processing_time_ms": 312.47
}
```

**Constraints:**
- Minimum text length: 20 characters
- Maximum text length: 3,000 characters (auto-truncated with log warning)

---

### `POST /chat`

Ask a natural language question about a document using extractive QA.

**Request Body:**

```json
{
  "context": "The employee shall not compete with the employer for a period of two years...",
  "question": "How long is the non-compete period?"
}
```

**Response (200 OK):**

```json
{
  "answer": "two years",
  "score": 0.85
}
```

---

### `GET /history`

Retrieve the 6 most recent prediction records.

**Response (200 OK):**

```json
{
  "history": [
    {
      "timestamp": "2026-06-03 13:24:01",
      "preview": "This Employment Contract is entered into between...",
      "label": "Employment Contract",
      "confidence": 0.9421,
      "risk_score": 65
    }
  ]
}
```

---

### `GET /stats`

Get aggregate analysis statistics.

**Response (200 OK):**

```json
{
  "docs_analyzed": 142,
  "high_risk_flags": 17
}
```

---

### `GET /health`

Service liveness and model load status.

**Response (200 OK):**

```json
{
  "status": "ok",
  "service": "alive",
  "predictor_loaded": true,
  "qa_model_loaded": false
}
```

---

## 📁 Project Structure

```
legal-intelligence-engine/
│
├── api/                          # FastAPI application layer
│   ├── main.py                   # All REST endpoints, lifespan, lazy model loading
│   └── database.py               # SQLite init, CRUD operations for predictions
│
├── src/                          # Core ML & NLP modules
│   ├── __init__.py
│   ├── predict.py                # LegalDocumentPredictor: BERT inference, label mapping
│   ├── explain.py                # LegalExplainer: gradient saliency + SHAP attribution
│   ├── ner.py                    # extract_entities: spaCy NER + regex fallback
│   ├── risk_detector.py          # detect_clauses, compute_risk_score, insight generation
│   ├── train.py                  # BERT fine-tuning script (CUAD + seed data)
│   └── data_preprocessing.py     # (utility) text preprocessing helpers
│
├── ui/
│   └── app.py                    # Streamlit frontend: upload, analysis, dashboard, PDF
│
├── tests/                        # pytest test suite
│   ├── __init__.py
│   ├── test_risk_detector.py     # Clause detection & scoring unit tests
│   ├── test_ner.py               # Entity extraction unit tests
│   └── test_explain.py           # Explainability unit tests
│
├── models/
│   └── bert_model/               # Fine-tuned BERT weights (after running train.py)
│
├── Dockerfile.backend            # Backend container definition
├── Dockerfile.frontend           # Frontend container definition
├── docker-compose.yml            # Multi-service orchestration
├── requirements.txt              # Pinned Python dependencies
├── pytest.ini                   # pytest configuration
├── predictions.db                # SQLite persistence store
└── training_log.jsonl            # Per-epoch training metrics (generated by train.py)
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HF_MODEL_NAME` | `appster777/legal-doc-classifier` | HuggingFace model ID or local path for the classifier |
| `API_URL` | `http://localhost:8000` | Backend URL consumed by the Streamlit frontend |

Set `HF_MODEL_NAME` to point to a locally fine-tuned model in `models/bert_model/` after running `train.py`:

```bash
# Windows (PowerShell)
$env:HF_MODEL_NAME = "models/bert_model"

# Linux / macOS
export HF_MODEL_NAME=models/bert_model
```

### Training Your Own Model

```bash
# Install the datasets library (required for CUAD download)
pip install datasets

# Run the fine-tuning script
python src/train.py
```

The script will:
1. Download and balance the CUAD dataset from HuggingFace Hub (up to 2,000 samples across 5 classes)
2. Merge with 80 curated seed samples covering all 5 label types
3. Train `bert-base-uncased` for 3 epochs with warmup + cosine decay
4. Log per-epoch validation accuracy to `training_log.jsonl`
5. Save the fine-tuned model to `models/bert_model/`
6. Print a final classification report with per-class F1 scores and confusion matrix

---

## 🧪 Testing

The project includes a comprehensive `pytest` suite covering all three core AI modules.

### Run All Tests

```bash
pytest tests/ -v
```

### Run Individual Test Files

```bash
# Risk detection & scoring
pytest tests/test_risk_detector.py -v

# Named entity recognition
pytest tests/test_ner.py -v

# Gradient explainability
pytest tests/test_explain.py -v
```

### Test Coverage Snapshot

| Module | Tests | Coverage Focus |
|---|---|---|
| `test_risk_detector.py` | Clause presence/absence, risk score bounds, insight generation, edge cases | `risk_detector.py` |
| `test_ner.py` | Entity type accuracy, noise filtering, deduplication, empty input | `ner.py` |
| `test_explain.py` | Token attribution shape, fallback keywords, SHAP integration | `explain.py` |

---

## 📈 Performance & Benchmarks

| Metric | Value |
|---|---|
| Average API response time (`/predict`) | ~300–500 ms (CPU, models warm) |
| First-request cold start (BERT load) | ~8–15 s (model download cached after first run) |
| BART NLI zero-shot cold start | ~20–30 s (first request only) |
| Max supported document length | 3,000 characters (auto-truncated) |
| NER entities returned | Up to 12 per document |
| Explanation tokens returned | Top 8 by attribution score |
| SQLite write throughput | > 1,000 records/s (local disk) |

> All benchmarks measured on a modern CPU. GPU acceleration (CUDA) is supported and will reduce inference times by 3–5×.

---

## 🗺️ Roadmap

- [ ] **Multi-language support** — Extend NER and classification to French, German, and Spanish legal documents
- [ ] **OCR integration** — Direct PDF/image ingestion via Tesseract or AWS Textract
- [ ] **Clause-level summarisation** — Abstractive summarisation of individual detected clauses using a T5/BART seq2seq model
- [ ] **Role-based authentication** — JWT-secured API endpoints with user-level history isolation
- [ ] **Async inference queue** — Celery + Redis task queue for handling concurrent long-running analysis jobs
- [ ] **Comparative analysis** — Side-by-side risk comparison of two uploaded documents
- [ ] **Custom clause library** — User-defined clause definitions added at runtime without redeployment
- [ ] **Webhook support** — Push analysis results to external systems (Slack, Jira, email) on completion
- [ ] **Fine-tuning UI** — In-app interface to submit document corrections and trigger model retraining

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/your-feature-name`
3. **Commit** your changes with conventional commit messages: `git commit -m "feat: add clause summarisation"`
4. **Push** to your fork: `git push origin feat/your-feature-name`
5. **Open** a Pull Request against the `main` branch

### Development Standards

- All new modules must include corresponding `tests/` coverage
- API endpoint changes must update the API Reference section of this README
- Follow PEP 8 style; use type hints on all public function signatures
- Maintain lazy model loading pattern — do **not** load heavy models at import time

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full text.

---

<div align="center">

**Built with ❤️ by [Parth Kadian](https://github.com/Parthkadian)**

*If this project helped you, please consider giving it a ⭐ on GitHub!*

[![GitHub Stars](https://img.shields.io/github/stars/Parthkadian/legal-intelligence-engine?style=social)](https://github.com/Parthkadian/legal-intelligence-engine)

</div>
