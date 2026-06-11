"""
Unit tests for src/risk_detector.py

All tests are pure-Python (no model weights, no network).
Run with: pytest tests/test_risk_detector.py -v -m unit
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.risk_detector import (
    detect_clauses,
    compute_risk_score,
    get_risk_level,
    generate_insights,
    generate_business_impact,
    generate_recommendations,
    generate_executive_summary,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_clauses_present():
    return {
        "Termination Clause": True,
        "Payment Clause": True,
        "Liability Clause": True,
        "Confidentiality Clause": True,
        "Indemnity Clause": True,
        "Jurisdiction Clause": True,
        "Arbitration Clause": True,
        "Force Majeure Clause": True,
        "Non-compete Clause": True,
        "Data Privacy Clause": True,
    }


@pytest.fixture
def no_clauses():
    return {k: False for k in [
        "Termination Clause", "Payment Clause", "Liability Clause",
        "Confidentiality Clause", "Indemnity Clause", "Jurisdiction Clause",
        "Arbitration Clause", "Force Majeure Clause", "Non-compete Clause",
        "Data Privacy Clause",
    ]}


# ---------------------------------------------------------------------------
# detect_clauses
# ---------------------------------------------------------------------------

class TestDetectClauses:
    @pytest.mark.unit
    def test_detects_termination(self):
        result = detect_clauses("This agreement may be terminated by either party.")
        assert result["Termination Clause"] is True

    @pytest.mark.unit
    def test_detects_payment(self):
        result = detect_clauses("Invoice must be paid within 30 days.")
        assert result["Payment Clause"] is True

    @pytest.mark.unit
    def test_detects_liability(self):
        result = detect_clauses("The party shall not be liable for indirect damages.")
        assert result["Liability Clause"] is True

    @pytest.mark.unit
    def test_detects_confidentiality(self):
        result = detect_clauses("This NDA prohibits disclosure of proprietary information.")
        assert result["Confidentiality Clause"] is True

    @pytest.mark.unit
    def test_detects_indemnity(self):
        result = detect_clauses("The vendor shall indemnify the client against all losses.")
        assert result["Indemnity Clause"] is True

    @pytest.mark.unit
    def test_detects_jurisdiction(self):
        result = detect_clauses("Governing law shall be the laws of England and Wales.")
        assert result["Jurisdiction Clause"] is True

    @pytest.mark.unit
    def test_detects_arbitration(self):
        result = detect_clauses("All disputes shall be resolved by arbitration.")
        assert result["Arbitration Clause"] is True

    @pytest.mark.unit
    def test_detects_force_majeure(self):
        result = detect_clauses(
            "This agreement includes a force majeure clause covering earthquakes, "
            "floods, and other acts of God beyond the parties' control."
        )
        assert result["Force Majeure Clause"] is True

    @pytest.mark.unit
    def test_detects_non_compete(self):
        result = detect_clauses("Employee agrees to a non-compete for 12 months post-termination.")
        assert result["Non-compete Clause"] is True

    @pytest.mark.unit
    def test_detects_data_privacy(self):
        result = detect_clauses("Processing is subject to GDPR data protection requirements.")
        assert result["Data Privacy Clause"] is True

    @pytest.mark.unit
    def test_empty_text_returns_all_false(self):
        result = detect_clauses("")
        assert all(v is False for v in result.values())

    @pytest.mark.unit
    def test_returns_dict_with_all_ten_keys(self):
        result = detect_clauses("some legal text")
        assert len(result) == 10
        assert all(isinstance(v, bool) for v in result.values())

    @pytest.mark.unit
    def test_case_insensitive(self):
        result = detect_clauses("TERMINATION CLAUSE IS PRESENT IN THIS DOCUMENT.")
        assert result["Termination Clause"] is True


# ---------------------------------------------------------------------------
# compute_risk_score
# ---------------------------------------------------------------------------

class TestComputeRiskScore:
    @pytest.mark.unit
    def test_score_capped_at_100(self, all_clauses_present):
        score = compute_risk_score(all_clauses_present)
        assert score <= 100

    @pytest.mark.unit
    def test_missing_payment_clause_adds_score(self, no_clauses):
        score_without_payment = compute_risk_score(no_clauses)
        clauses_with_payment = {**no_clauses, "Payment Clause": True}
        score_with_payment = compute_risk_score(clauses_with_payment)
        assert score_without_payment > score_with_payment

    @pytest.mark.unit
    def test_missing_force_majeure_adds_score(self, no_clauses):
        score_without = compute_risk_score(no_clauses)
        clauses_with = {**no_clauses, "Force Majeure Clause": True}
        score_with = compute_risk_score(clauses_with)
        assert score_without > score_with

    @pytest.mark.unit
    def test_all_clauses_present_returns_high_score(self, all_clauses_present):
        # All risky clauses present and payment present — should still be high
        score = compute_risk_score(all_clauses_present)
        assert score >= 70

    @pytest.mark.unit
    def test_no_clauses_returns_nonzero(self, no_clauses):
        # Missing payment + missing force majeure both add points
        score = compute_risk_score(no_clauses)
        assert score > 0

    @pytest.mark.unit
    def test_score_is_integer(self, all_clauses_present):
        score = compute_risk_score(all_clauses_present)
        assert isinstance(score, int)


# ---------------------------------------------------------------------------
# get_risk_level
# ---------------------------------------------------------------------------

class TestGetRiskLevel:
    @pytest.mark.unit
    def test_high_at_70(self):
        assert get_risk_level(70) == "High"

    @pytest.mark.unit
    def test_high_at_100(self):
        assert get_risk_level(100) == "High"

    @pytest.mark.unit
    def test_medium_at_40(self):
        assert get_risk_level(40) == "Medium"

    @pytest.mark.unit
    def test_medium_at_69(self):
        assert get_risk_level(69) == "Medium"

    @pytest.mark.unit
    def test_low_at_0(self):
        assert get_risk_level(0) == "Low"

    @pytest.mark.unit
    def test_low_at_39(self):
        assert get_risk_level(39) == "Low"

    @pytest.mark.unit
    def test_boundary_between_medium_and_high(self):
        assert get_risk_level(69) == "Medium"
        assert get_risk_level(70) == "High"


# ---------------------------------------------------------------------------
# generate_insights
# ---------------------------------------------------------------------------

class TestGenerateInsights:
    @pytest.mark.unit
    def test_returns_list(self, no_clauses):
        result = generate_insights(no_clauses)
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_termination_clause_yields_insight(self):
        clauses = {"Termination Clause": True, "Payment Clause": True,
                   "Liability Clause": False, "Confidentiality Clause": False,
                   "Indemnity Clause": False, "Jurisdiction Clause": False,
                   "Arbitration Clause": False, "Force Majeure Clause": False,
                   "Non-compete Clause": False, "Data Privacy Clause": False}
        insights = generate_insights(clauses)
        assert any("termination" in i.lower() for i in insights)

    @pytest.mark.unit
    def test_missing_payment_yields_insight(self, no_clauses):
        insights = generate_insights(no_clauses)
        assert any("payment" in i.lower() for i in insights)

    @pytest.mark.unit
    def test_no_clauses_still_returns_list(self, no_clauses):
        insights = generate_insights(no_clauses)
        assert isinstance(insights, list)


# ---------------------------------------------------------------------------
# generate_recommendations
# ---------------------------------------------------------------------------

class TestGenerateRecommendations:
    @pytest.mark.unit
    def test_returns_default_when_no_issues(self, all_clauses_present):
        # all_clauses_present has payment=True, force_majeure=True, score would be high
        # but test with a minimal low-risk set
        safe_clauses = {k: False for k in all_clauses_present}
        safe_clauses["Payment Clause"] = True
        safe_clauses["Force Majeure Clause"] = True
        recs = generate_recommendations(0, safe_clauses)
        assert len(recs) >= 1

    @pytest.mark.unit
    def test_high_score_triggers_escalation_rec(self, all_clauses_present):
        recs = generate_recommendations(75, all_clauses_present)
        assert any("legal team" in r.lower() or "escalate" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# generate_executive_summary
# ---------------------------------------------------------------------------

class TestGenerateExecutiveSummary:
    @pytest.mark.unit
    def test_returns_dict_with_expected_keys(self, no_clauses):
        summary = generate_executive_summary("Contract", 50, no_clauses)
        assert "document_type" in summary
        assert "risk_score" in summary
        assert "risk_level" in summary
        assert "main_concern" in summary
        assert "action" in summary

    @pytest.mark.unit
    def test_document_type_preserved(self, no_clauses):
        summary = generate_executive_summary("Patent", 10, no_clauses)
        assert summary["document_type"] == "Patent"

    @pytest.mark.unit
    def test_high_score_triggers_high_risk_concern(self, no_clauses):
        summary = generate_executive_summary("Contract", 75, no_clauses)
        assert "risk" in summary["main_concern"].lower()
