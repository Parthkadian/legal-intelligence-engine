def detect_clauses(text: str) -> dict:
    text = text.lower()

    return {
        "Termination Clause": any(k in text for k in ["termination", "terminate", "termination clause"]),
        "Payment Clause": any(k in text for k in ["payment", "fees", "invoice", "pricing"]),
        "Liability Clause": any(k in text for k in ["liability", "damages", "penalty"]),
        "Confidentiality Clause": any(k in text for k in ["confidential", "non-disclosure", "nda"]),
        "Indemnity Clause": any(k in text for k in ["indemnify", "indemnity"]),
        "Jurisdiction Clause": any(k in text for k in ["jurisdiction", "governing law", "court"]),
        "Arbitration Clause": any(k in text for k in ["arbitration", "arbitrator", "dispute resolution"]),
        "Force Majeure Clause": any(k in text for k in ["force majeure", "act of god", "unforeseeable"]),
        "Non-compete Clause": any(k in text for k in ["non-compete", "noncompete", "restrictive covenant"]),
        "Data Privacy Clause": any(k in text for k in ["data privacy", "gdpr", "ccpa", "data protection"])
    }

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



def generate_insights(text: str, clauses: dict) -> list:
    text = text.lower()
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
        insights.append("Non-compete clause restrict post-termination activities")
        
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
        "action": "Review recommended" if score >= 40 else "Safe to proceed with minor review"
    }