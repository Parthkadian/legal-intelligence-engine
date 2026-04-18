# ⚖️ Legal Intelligence Workspace

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10](https://img.shields.io/badge/Python-3.10-success)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Microservices-2496ED?logo=docker&logoColor=white)

An enterprise-grade Legal NLP microservice architecture designed to automate the classification, risk assessment, and metadata extraction of raw legal documents. 

Built for high-performance and decoupled execution, this ecosystem leverages deep learning models (BERT-based architectures) and heuristic NLP pipelines to transform unstructured legal contracts into actionable, JSON-structured insights.

---

## 🚀 Key Features

*   **Deep Learning Classification:** Utilizes HuggingFace `transformers` to classify documents into standard legal paradigms (NDAs, Employment Contracts, Vendor Agreements, etc.).
*   **Named Entity Recognition (NER):** Custom SpaCy pipelines scrub and identify PII, organizations, and monetary values.
*   **Automated Risk Scoring:** Rule-based heuristic engine detects precarious clauses (e.g., severe indemnification, unregulated jurisdiction) and computes real-time risk matrices.
*   **Interactive UI Command Center:** A highly responsive Streamlit frontend featuring session history mapping, dynamic SQL tracking, and direct PDF/CSV/DOCX export capabilities.
*   **Decoupled Microservice Architecture:** Segregated backend (FastAPI) and frontend (Streamlit) communicating over isolated Docker container networks.

---

## 🛠️ Core Technology Stack

| Component | Framework / Library |
| :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Python 3.10 |
| **Machine Learning** | PyTorch, HuggingFace Transformers, SpaCy |
| **Frontend UI** | Streamlit, Native HTML/CSS Injection |
| **Database persistence** | SQLite3 (Local Session Tracking) |
| **Infrastructure** | Docker, Docker Compose |

---

## 🐋 Quickstart: Docker Deployment

The entire architecture is strictly containerized. To spin up the complete ecosystem locally, ensure you have Docker Desktop installed on your host machine.

```bash
# 1. Clone the repository
git clone https://github.com/Parthkadian/legal-intelligence-engine.git
cd legal-intelligence-engine

# 2. Build and launch the decoupled microservices
docker-compose up --build
```
> **Performance Note**: The initial build takes approximately 5-10 minutes as the Docker daemon downloads heavy deep learning model weights (PyTorch, Transformers). All subsequent startups take `< 3 seconds` due to Docker caching.

**Access the Services:**
*   **Frontend UI Command Center:** `http://localhost:8501`
*   **Backend API Documentation (Swagger UI):** `http://localhost:8000/docs`

---

## 📁 System Architecture Roadmap

```text
legal-intelligence-engine/
│
├── api/                     # Backend Microservice
│   ├── main.py              # FastAPI endpoints (/predict, /history, /chat)
│   └── database.py          # SQLite connection and session persistence
│
├── src/                     # Core Machine Learning Logic
│   ├── __init__.py          # Module initialization
│   ├── data_preprocessing.py# NLP cleaning and truncation pipelines
│   ├── explain.py           # Legal Token isolation and algorithm explanations
│   ├── ner.py               # SpaCy Entity Extraction routines
│   ├── predict.py           # BERT model inference and pipeline setup
│   ├── risk_detector.py     # Clause detection and Risk Scoring matrix
│   └── train.py             # Model fine-tuning routines
│
├── ui/                      # Frontend Microservice
│   └── app.py               # Streamlit application (View Layer)
│
├── test_api.py              # External API Integration testing tests
├── test_fastapi.py          # PyTest suite for FastAPI endpoints
├── test_qa.py               # HuggingFace QA evaluation scripts
│
├── Dockerfile.backend       # Environment Blueprint for ML Inference & API
├── Dockerfile.frontend      # Environment Blueprint for Streamlit UI
└── docker-compose.yml       # Orchestration and Port bridging map
```

---

## 📈 Executive Summary

This tool minimizes legal overhead by providing instantaneous risk analysis before a document ever hits a human lawyer's desk. The API-first design ensures it can be integrated directly into larger corporate document pipelines (e.g., Salesforce, SharePoint) via RESTful requests, while the Streamlit UI provides a no-code visual interface for standalone auditors.

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
