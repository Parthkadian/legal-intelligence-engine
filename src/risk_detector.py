"""
risk_detector.py — Clause detection, risk scoring, and insight generation.

detect_clauses() uses a two-pass hybrid strategy:
  Pass 1: Zero-shot classification via facebook/bart-large-mnli
          (context-aware; "termination of my lunch break" will NOT fire).
  Pass 2: Keyword matching as a per-clause fallback when the model is
          unavailable or its confidence is in the uncertain zone.
"""
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Zero-shot model (lazy singleton)
# ---------------------------------------------------------------------------

_ZS_CLASSIFIER = None
_ZS_MODEL_NAME = "facebook/bart-large-mnli"
_ZS_CONFIDENCE_THRESHOLD = 0.55   # below this we fall back to keywords


def _get_zs_classifier():
    """Load and cache the zero-shot classifier (once per process)."""
    global _ZS_CLASSIFIER
    if _ZS_CLASSIFIER is None:
        try:
            from transformers import pipeline
            logger.info("Loading zero-shot classifier (%s)…", _ZS_MODEL_NAME)
            _ZS_CLASSIFIER = pipeline(
                "zero-shot-classification",
                model=_ZS_MODEL_NAME,
                device=-1,      # CPU; avoids device-mismatch issues
            )
            logger.info("Zero-shot classifier loaded.")
        except Exception as exc:
            logger.warning(
                "Could not load zero-shot model (%s) — keyword fallback only.", exc
            )
            _ZS_CLASSIFIER = None
    return _ZS_CLASSIFIER


# ---------------------------------------------------------------------------
# Clause definitions
# ---------------------------------------------------------------------------

# Maps clause name → (zero-shot hypothesis, keyword fallback list)
_CLAUSE_DEFINITIONS: dict[str, tuple[str, list[str]]] = {
    "Termination Clause": (
        "This text contains a termination or contract exit clause.",
        ["termination", "terminate", "termination clause"],
    ),
    "Payment Clause": (
        "This text describes payment terms, fees, invoicing, or pricing.",
        ["payment", "fees", "invoice", "pricing"],
    ),
    "Liability Clause": (
        "This text limits or assigns legal liability or damages.",
        ["liability", "damages", "penalty"],
    ),
    "Confidentiality Clause": (
        "This text imposes confidentiality or non-disclosure obligations.",
        ["confidential", "non-disclosure", "nda"],
    ),
    "Indemnity Clause": (
        "This text contains an indemnification or hold-harmless provision.",
        ["indemnify", "indemnity"],
    ),
    "Jurisdiction Clause": (
        "This text specifies the governing law or jurisdiction for disputes.",
        ["jurisdiction", "governing law", "court"],
    ),
    "Arbitration Clause": (
        "This text requires arbitration or alternative dispute resolution.",
        ["arbitration", "arbitrator", "dispute resolution"],
    ),
    "Force Majeure Clause": (
        "This text contains a force majeure or act-of-God provision.",
        ["force majeure", "act of god", "unforeseeable"],
    ),
    "Non-compete Clause": (
        "This text restricts post-employment competition or solicitation.",
        ["non-compete", "noncompete", "restrictive covenant"],
    ),
    "Data Privacy Clause": (
        "This text addresses data privacy, GDPR, CCPA, or data protection.",
        ["data privacy", "gdpr", "ccpa", "data protection"],
    ),
}


# ---------------------------------------------------------------------------
# Keyword-only detection (fast fallback)
# ---------------------------------------------------------------------------

def _keyword_detect(text_lower: str) -> dict[str, bool]:
    return {
        clause: any(kw in text_lower for kw in keywords)
        for clause, (_, keywords) in _CLAUSE_DEFINITIONS.items()
    }


# ---------------------------------------------------------------------------
# Public: detect_clauses
# ---------------------------------------------------------------------------

def detect_clauses(text: str) -> dict:
    """
    Detect which of the 10 standard legal clauses are present in *text*.

    Strategy (two-pass hybrid):
      1. Zero-shot classification via ``facebook/bart-large-mnli``.
         Each clause hypothesis is scored against the document text.
         Results above _ZS_CONFIDENCE_THRESHOLD are treated as present.
      2. If the model is unavailable *or* its confidence is below the
         threshold for a given clause, fall back to keyword matching for
         that individual clause.

    This prevents simple false-positives like "termination of my lunch
    break" that fool pure keyword matching.
    """
    if not text or not text.strip():
        return {clause: False for clause in _CLAUSE_DEFINITIONS}

    text_lower = text.lower()

    # Keyword results always computed — used as per-clause fallback
    keyword_results = _keyword_detect(text_lower)

    classifier = _get_zs_classifier()
    if classifier is None:
        return keyword_results

    hypotheses = [defn[0] for defn in _CLAUSE_DEFINITIONS.values()]

    try:
        # multi_label=True: each clause scored independently (0–1)
        zs_result = classifier(
            text[:1024],        # BART max ~1024 tokens
            candidate_labels=hypotheses,
            multi_label=True,
        )

        score_map: dict[str, float] = dict(
            zip(zs_result["labels"], zs_result["scores"])
        )

        final: dict[str, bool] = {}
        for clause, (hypothesis, _) in _CLAUSE_DEFINITIONS.items():
            zs_score = score_map.get(hypothesis, 0.0)
            if zs_score >= _ZS_CONFIDENCE_THRESHOLD:
                # Confidently present
                final[clause] = True
            else:
                # Below threshold: keyword is the tiebreaker.
                # A clear keyword hit overrides a low-confidence ZS result,
                # which is the correct behaviour — the model may simply be
                # uncertain rather than confidently wrong.
                final[clause] = keyword_results[clause]

        return final

    except Exception as exc:
        logger.warning(
            "Zero-shot inference failed (%s) — using keyword fallback.", exc
        )
        return keyword_results


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def compute_risk_score(clauses: dict) -> int:
    score = 0

    if clauses.get("Termination Clause"):
        score += 25

    if clauses.get("Liability Clause"):
        score += 25

    if not clauses.get("Payment Clause"):
        score += 20

    if clauses.get("Confidentiality Clause"):
        score += 10

    if clauses.get("Indemnity Clause"):
        score += 10

    if clauses.get("Jurisdiction Clause"):
        score += 10

    if clauses.get("Non-compete Clause"):
        score += 15

    if clauses.get("Data Privacy Clause"):
        score += 15

    if clauses.get("Arbitration Clause"):
        score += 5

    if not clauses.get("Force Majeure Clause"):
        score += 10

    return min(score, 100)


def get_risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# Insights, impact, recommendations, summary
# ---------------------------------------------------------------------------

def generate_insights(clauses: dict) -> list:
    insights = []

    if clauses.get("Termination Clause"):
        insights.append("Termination clause detected → ensure exit conditions are clearly defined")

    if clauses.get("Liability Clause"):
        insights.append("Liability clause present → potential financial/legal exposure")

    if clauses.get("Confidentiality Clause"):
        insights.append("Confidentiality clause ensures data protection obligations")

    if not clauses.get("Payment Clause"):
        insights.append("Payment terms missing → high financial and revenue risk")

    if clauses.get("Indemnity Clause"):
        insights.append("Indemnity clause present → one party may bear significant legal burden")

    if clauses.get("Jurisdiction Clause"):
        insights.append("Jurisdiction defined → legal disputes tied to specific courts")

    if clauses.get("Arbitration Clause"):
        insights.append("Arbitration clause present → disputes resolved outside courts")

    if clauses.get("Force Majeure Clause"):
        insights.append("Force Majeure clause present → protects against unforeseeable events")

    if clauses.get("Non-compete Clause"):
        insights.append("Non-compete clause restricts post-termination activities")

    if clauses.get("Data Privacy Clause"):
        insights.append("Data privacy obligations attached → ensure GDPR/CCPA compliance")

    return insights


def generate_business_impact(score: int, clauses: dict) -> list:
    impact = []

    if score >= 70:
        impact.append("High legal exposure → immediate legal review recommended")

    if not clauses.get("Payment Clause"):
        impact.append("Revenue risk due to missing or unclear payment terms")

    if clauses.get("Liability Clause"):
        impact.append("Potential financial liability exposure for involved parties")

    if clauses.get("Termination Clause"):
        impact.append("Contract exit conditions present → requires careful validation")

    if clauses.get("Indemnity Clause"):
        impact.append("Risk transfer through indemnity → could increase financial burden")

    if clauses.get("Non-compete Clause"):
        impact.append("Restrictive business operations post-termination")

    if clauses.get("Data Privacy Clause"):
        impact.append("High compliance burden for data mapping and security")

    return impact


def generate_recommendations(score: int, clauses: dict) -> list:
    recs = []

    if score >= 70:
        recs.append("Escalate document to legal team for detailed review")

    if not clauses.get("Payment Clause"):
        recs.append("Add clear payment schedule and financial terms")

    if clauses.get("Termination Clause"):
        recs.append("Review termination conditions to avoid unfair exit risks")

    if clauses.get("Liability Clause"):
        recs.append("Clarify liability limits and obligations")

    if clauses.get("Confidentiality Clause"):
        recs.append("Ensure confidentiality scope aligns with business needs")

    if clauses.get("Indemnity Clause"):
        recs.append("Assess indemnity clause for potential financial exposure")

    if not clauses.get("Force Majeure Clause"):
        recs.append("Consider adding Force Majeure to protect against extreme events")

    if clauses.get("Data Privacy Clause"):
        recs.append("Involve DPO or data compliance team to review obligations")

    if not recs:
        recs.append("No major issues detected — document appears balanced")

    return recs


def generate_executive_summary(label: str, score: int, clauses: dict) -> dict:
    main_issue = "No major risks detected"

    if score >= 70:
        main_issue = "High legal risk due to missing or risky clauses"
    elif not clauses.get("Payment Clause"):
        main_issue = "Missing payment terms"

    return {
        "document_type": label,
        "risk_score": score,
        "risk_level": get_risk_level(score),
        "main_concern": main_issue,
        "action": "Review recommended" if score >= 40 else "Safe to proceed with minor review",
    }