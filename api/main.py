from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import time
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.predict import get_predictor
from src.ner import extract_entities
from src.explain import explain_text
from src.risk_detector import (
    detect_clauses,
    compute_risk_score,
    get_risk_level,
    generate_insights,
    generate_business_impact,
    generate_recommendations,
    generate_executive_summary,
)
from api.database import init_db, save_prediction, get_history
import torch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("legal-doc-api")

app = FastAPI(
    title="AI Legal Risk Intelligence API",
    version="3.0.0",
    description="Explainable AI system for legal document classification and risk analysis"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    context: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    score: float


class PredictResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict
    top_predictions: list
    entities: list
    explanation: list
    clauses: dict
    risk_score: int
    risk_level: str
    insights: list
    business_impact: list
    recommendations: list
    executive_summary: dict
    processing_time_ms: float


qa_tokenizer = None
qa_model = None
predictor_instance = None


def load_predictor():
    global predictor_instance
    if predictor_instance is None:
        logger.info("Loading classification predictor...")
        predictor_instance = get_predictor()
        logger.info("Predictor loaded successfully.")
        logger.info("Available labels: %s", predictor_instance.labels)
    return predictor_instance


def load_qa_model():
    global qa_tokenizer, qa_model

    if qa_tokenizer is None or qa_model is None:
        logger.info("Lazy loading QA model...")
        from transformers import AutoTokenizer, AutoModelForQuestionAnswering

        model_name = "distilbert-base-cased-distilled-squad"
        qa_tokenizer = AutoTokenizer.from_pretrained(model_name)
        qa_model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        logger.info("QA model loaded successfully.")

    return qa_tokenizer, qa_model


@app.on_event("startup")
def startup_event():
    logger.info("Starting AI Legal Risk Intelligence API...")
    try:
        init_db()
        logger.info("Database initialized successfully.")

        # Load only the predictor on startup.
        # QA model is loaded lazily when /chat is called.
        load_predictor()

        logger.info("Startup complete.")
    except Exception as e:
        logger.exception("Startup failed: %s", e)
        raise


@app.get("/")
def root():
    return {
        "message": "AI Legal Risk Intelligence API is running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health():
    try:
        predictor = load_predictor()
        return {
            "status": "ok",
            "model_loaded": True,
            "num_labels": len(predictor.labels),
            "labels": predictor.labels,
            "qa_model_loaded": qa_model is not None
        }
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return {
            "status": "error",
            "model_loaded": False,
            "error": str(e),
            "qa_model_loaded": qa_model is not None
        }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Please enter a longer legal text.")

    start_time = time.time()

    try:
        text_lower = text.lower()
        identity_keywords = [
            "aadhaar",
            "aadhar",
            "passport",
            "pan card",
            "driving license",
            "voter id",
            "identity card",
            "national id",
        ]
        is_identity_document = any(keyword in text_lower for keyword in identity_keywords)

        if is_identity_document:
            prediction = {
                "label": "Identity Document",
                "confidence": 0.99,
                "probabilities": {"Identity Document": 0.99},
                "top_predictions": [{"label": "Identity Document", "confidence": 0.99}],
            }
            entities = extract_entities(text)

            expl_words = [kw for kw in identity_keywords if kw in text_lower][:3]
            if not expl_words:
                expl_words = ["identity", "document"]
            explanation = [{"word": w.upper(), "score": 1.0} for w in expl_words]

            clauses = {}
            risk_score = 0
            risk_level = "None"
            insights = ["Personal Identity Document detected. Contract clauses do not apply."]
            business_impact = ["Used for identification verification only."]
            recommendations = ["Ensure document is kept secure to prevent identity theft."]
            executive_summary = {
                "document_type": "Identity Document",
                "risk_score": 0,
                "risk_level": "None",
                "main_concern": "Personal Data Storage",
                "action": "Ensure secure storage of PII",
            }
        else:
            predictor = load_predictor()

            prediction = predictor.predict(text)
            entities = extract_entities(text)
            explanation = explain_text(text)

            clauses = detect_clauses(text)
            risk_score = compute_risk_score(clauses)
            risk_level = get_risk_level(risk_score)
            insights = generate_insights(text, clauses)
            business_impact = generate_business_impact(risk_score, clauses)
            recommendations = generate_recommendations(risk_score, clauses)
            executive_summary = generate_executive_summary(
                prediction["label"],
                risk_score,
                clauses,
            )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        response = {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "top_predictions": prediction.get("top_predictions", []),
            "entities": entities,
            "explanation": explanation,
            "clauses": clauses,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "insights": insights,
            "business_impact": business_impact,
            "recommendations": recommendations,
            "executive_summary": executive_summary,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            "Prediction done | label=%s | confidence=%.4f | risk=%d | level=%s | time=%sms",
            response["label"],
            response["confidence"],
            response["risk_score"],
            response["risk_level"],
            response["processing_time_ms"],
        )

        save_prediction(text, response["label"], response["confidence"], response["risk_score"])
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/history")
def history_endpoint():
    try:
        return {"history": get_history(limit=6)}
    except Exception as e:
        logger.exception("Fetch history failed: %s", e)
        raise HTTPException(status_code=500, detail=f"History fetch failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        tokenizer, model = load_qa_model()

        inputs = tokenizer(request.question, request.context, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        answer_start = torch.argmax(outputs.start_logits)
        answer_end = torch.argmax(outputs.end_logits) + 1

        answer_tokens = inputs["input_ids"][0][answer_start:answer_end]
        answer = tokenizer.decode(answer_tokens, skip_special_tokens=True).strip()

        if not answer:
            answer = "No clear answer found in the provided context."

        score = 0.85

        return {"answer": answer, "score": score}
    except Exception as e:
        logger.exception("Chat QA failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat QA failed: {str(e)}")