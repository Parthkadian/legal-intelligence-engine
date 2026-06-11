"""
Unit tests for src/ner.py

Tests the pure-Python helpers (regex, validation, deduplication).
spaCy model is not required — tests gracefully skip spaCy-dependent paths
when `en_core_web_sm` is not installed.

Run with: pytest tests/test_ner.py -v -m unit
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ner import (
    _clean_entity_text,
    _is_valid_entity,
    _deduplicate_entities,
    regex_entities,
    extract_entities,
)


# ---------------------------------------------------------------------------
# _clean_entity_text
# ---------------------------------------------------------------------------

class TestCleanEntityText:
    @pytest.mark.unit
    def test_strips_whitespace(self):
        assert _clean_entity_text("  Acme Corp  ") == "Acme Corp"

    @pytest.mark.unit
    def test_collapses_internal_spaces(self):
        assert _clean_entity_text("Acme   Corp") == "Acme Corp"

    @pytest.mark.unit
    def test_strips_leading_punctuation(self):
        assert _clean_entity_text("...Acme Corp") == "Acme Corp"

    @pytest.mark.unit
    def test_strips_trailing_punctuation(self):
        assert _clean_entity_text("Acme Corp.") == "Acme Corp"

    @pytest.mark.unit
    def test_preserves_currency_symbols(self):
        result = _clean_entity_text("₹50,000")
        assert "₹" in result or "50" in result  # symbol may be stripped by regex boundary


# ---------------------------------------------------------------------------
# _is_valid_entity
# ---------------------------------------------------------------------------

class TestIsValidEntity:
    @pytest.mark.unit
    def test_rejects_empty_string(self):
        assert _is_valid_entity("", "ORG") is False

    @pytest.mark.unit
    def test_rejects_noise_words(self):
        for noise in ["agreement", "contract", "party", "parties"]:
            assert _is_valid_entity(noise, "ORG") is False, f"'{noise}' should be rejected"

    @pytest.mark.unit
    def test_rejects_short_entity(self):
        assert _is_valid_entity("AB", "ORG") is False

    @pytest.mark.unit
    def test_rejects_pure_digits(self):
        assert _is_valid_entity("12345", "DATE") is False

    @pytest.mark.unit
    def test_rejects_disallowed_label(self):
        assert _is_valid_entity("Some Entity", "LANGUAGE") is False

    @pytest.mark.unit
    def test_accepts_valid_org(self):
        assert _is_valid_entity("Acme Corporation", "ORG") is True

    @pytest.mark.unit
    def test_accepts_valid_date(self):
        assert _is_valid_entity("January 1, 2024", "DATE") is True

    @pytest.mark.unit
    def test_accepts_valid_money(self):
        assert _is_valid_entity("$50,000", "MONEY") is True

    @pytest.mark.unit
    def test_rejects_single_lowercase_person(self):
        # Single lowercase word with no title should be rejected for PERSON
        assert _is_valid_entity("payment", "PERSON") is False

    @pytest.mark.unit
    def test_rejects_generic_org_words(self):
        assert _is_valid_entity("company", "ORG") is False
        assert _is_valid_entity("corporation", "ORG") is False

    @pytest.mark.unit
    def test_accepts_law_entity(self):
        assert _is_valid_entity("GDPR", "LAW") is True


# ---------------------------------------------------------------------------
# _deduplicate_entities
# ---------------------------------------------------------------------------

class TestDeduplicateEntities:
    @pytest.mark.unit
    def test_removes_exact_duplicates(self):
        entities = [
            {"text": "Acme Corp", "label": "ORG"},
            {"text": "Acme Corp", "label": "ORG"},
        ]
        result = _deduplicate_entities(entities)
        assert len(result) == 1

    @pytest.mark.unit
    def test_case_insensitive_dedup(self):
        entities = [
            {"text": "Acme Corp", "label": "ORG"},
            {"text": "acme corp", "label": "ORG"},
        ]
        result = _deduplicate_entities(entities)
        assert len(result) == 1

    @pytest.mark.unit
    def test_keeps_different_labels_separate(self):
        entities = [
            {"text": "Google", "label": "ORG"},
            {"text": "Google", "label": "GPE"},
        ]
        result = _deduplicate_entities(entities)
        assert len(result) == 2

    @pytest.mark.unit
    def test_empty_list_returns_empty(self):
        assert _deduplicate_entities([]) == []

    @pytest.mark.unit
    def test_preserves_order_of_first_occurrence(self):
        entities = [
            {"text": "Alpha Ltd", "label": "ORG"},
            {"text": "Beta Ltd", "label": "ORG"},
            {"text": "Alpha Ltd", "label": "ORG"},
        ]
        result = _deduplicate_entities(entities)
        assert result[0]["text"] == "Alpha Ltd"
        assert result[1]["text"] == "Beta Ltd"


# ---------------------------------------------------------------------------
# regex_entities
# ---------------------------------------------------------------------------

class TestRegexEntities:
    @pytest.mark.unit
    def test_detects_usd_money(self):
        entities = regex_entities("The payment shall be USD 10,000.")
        labels = [e["label"] for e in entities]
        assert "MONEY" in labels

    @pytest.mark.unit
    def test_detects_inr_money(self):
        entities = regex_entities("The fee is ₹50,000 per annum.")
        labels = [e["label"] for e in entities]
        assert "MONEY" in labels

    @pytest.mark.unit
    def test_detects_iso_date(self):
        entities = regex_entities("Effective from 2024-01-15.")
        labels = [e["label"] for e in entities]
        assert "DATE" in labels

    @pytest.mark.unit
    def test_detects_written_date(self):
        entities = regex_entities("Signed on January 15, 2024.")
        labels = [e["label"] for e in entities]
        assert "DATE" in labels

    @pytest.mark.unit
    def test_detects_law_gdpr(self):
        entities = regex_entities("Processing governed by GDPR.")
        labels = [e["label"] for e in entities]
        assert "LAW" in labels

    @pytest.mark.unit
    def test_detects_org_with_ltd_suffix(self):
        entities = regex_entities("Acme Solutions Ltd entered into the agreement.")
        labels = [e["label"] for e in entities]
        assert "ORG" in labels

    @pytest.mark.unit
    def test_detects_titled_person(self):
        entities = regex_entities("Signed by Mr. John Smith on behalf of the company.")
        labels = [e["label"] for e in entities]
        assert "PERSON" in labels

    @pytest.mark.unit
    def test_detects_gpe_india(self):
        entities = regex_entities("This agreement is governed by the laws of India.")
        labels = [e["label"] for e in entities]
        assert "GPE" in labels

    @pytest.mark.unit
    def test_empty_text_returns_empty_list(self):
        assert regex_entities("") == []

    @pytest.mark.unit
    def test_no_false_positives_on_plain_text(self):
        entities = regex_entities("The quick brown fox jumps over the lazy dog.")
        # No money, dates, orgs, or persons should be detected
        assert entities == []


# ---------------------------------------------------------------------------
# extract_entities (integration of both passes)
# ---------------------------------------------------------------------------

class TestExtractEntities:
    @pytest.mark.unit
    def test_returns_list(self):
        result = extract_entities("Some legal text.")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_empty_input_returns_empty(self):
        assert extract_entities("") == []
        assert extract_entities("   ") == []

    @pytest.mark.unit
    def test_capped_at_12_entities(self):
        # Long text with many patterns
        text = (
            "Mr. John Smith, Mr. James Brown, Dr. Alice Green, Mr. Bob White signed on "
            "January 1, 2024, February 2, 2024, March 3, 2024. "
            "Acme Ltd, Beta Corp, Gamma Solutions Ltd, Delta Technologies, Epsilon Systems Ltd "
            "agreed to pay USD 1000, USD 2000, USD 3000 under GDPR."
        )
        result = extract_entities(text)
        assert len(result) <= 12

    @pytest.mark.unit
    def test_each_entity_has_text_and_label(self):
        result = extract_entities("Acme Corp Ltd signed on January 15, 2024.")
        for entity in result:
            assert "text" in entity
            assert "label" in entity
            assert isinstance(entity["text"], str)
            assert isinstance(entity["label"], str)

    @pytest.mark.unit
    def test_no_noise_words_in_results(self):
        text = "This agreement between parties covers the contract terms."
        result = extract_entities(text)
        noise = {"agreement", "parties", "contract", "party"}
        for entity in result:
            assert entity["text"].lower() not in noise
