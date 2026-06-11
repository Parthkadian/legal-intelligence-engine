"""
Unit tests for src/explain.py

Tests ONLY the pure-Python helpers that require no model weights:
  - LegalExplainer._clean_token
  - LegalExplainer._is_valid_token
  - LegalExplainer._boost_score
  - LegalExplainer._fallback_keywords
  - LegalExplainer._postprocess_ranked_words

The gradient-based explain() and explain_with_shap() methods require loaded
model weights and are covered by integration tests (test_api.py).

Run with: pytest tests/test_explain.py -v -m unit
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.explain import LEGAL_PRIORITY_TERMS


# ---------------------------------------------------------------------------
# Helper: instantiate LegalExplainer without loading model weights
# ---------------------------------------------------------------------------

def make_explainer():
    """Return a LegalExplainer whose __init__ is bypassed (no disk I/O)."""
    with patch("src.explain.AutoTokenizer.from_pretrained"), \
         patch("src.explain.AutoModelForSequenceClassification.from_pretrained"), \
         patch("torch.device", return_value="cpu"):
        from src.explain import LegalExplainer
        obj = LegalExplainer.__new__(LegalExplainer)
        obj.device = "cpu"
        obj.tokenizer = MagicMock()
        obj.model = MagicMock()
    return obj


@pytest.fixture
def explainer():
    return make_explainer()


# ---------------------------------------------------------------------------
# _clean_token
# ---------------------------------------------------------------------------

class TestCleanToken:
    @pytest.mark.unit
    def test_removes_bert_continuation_prefix(self, explainer):
        assert explainer._clean_token("##ing") == "ing"

    @pytest.mark.unit
    def test_strips_surrounding_whitespace(self, explainer):
        assert explainer._clean_token("  hello  ") == "hello"

    @pytest.mark.unit
    def test_strips_leading_punctuation(self, explainer):
        assert explainer._clean_token("...contract") == "contract"

    @pytest.mark.unit
    def test_strips_trailing_punctuation(self, explainer):
        assert explainer._clean_token("contract.") == "contract"

    @pytest.mark.unit
    def test_empty_string_stays_empty(self, explainer):
        assert explainer._clean_token("") == ""

    @pytest.mark.unit
    def test_pure_word_unchanged(self, explainer):
        assert explainer._clean_token("termination") == "termination"


# ---------------------------------------------------------------------------
# _is_valid_token
# ---------------------------------------------------------------------------

class TestIsValidToken:
    @pytest.mark.unit
    def test_rejects_empty_string(self, explainer):
        assert explainer._is_valid_token("") is False

    @pytest.mark.unit
    def test_rejects_cls_sep_pad_tokens(self, explainer):
        for tok in ["[CLS]", "[SEP]", "[PAD]", "cls", "sep", "pad"]:
            assert explainer._is_valid_token(tok) is False, f"'{tok}' should be invalid"

    @pytest.mark.unit
    def test_rejects_common_stopwords(self, explainer):
        for word in ["the", "and", "for", "this", "that", "with"]:
            assert explainer._is_valid_token(word) is False

    @pytest.mark.unit
    def test_rejects_tokens_shorter_than_4_chars(self, explainer):
        assert explainer._is_valid_token("law") is False
        assert explainer._is_valid_token("act") is False

    @pytest.mark.unit
    def test_rejects_pure_digits(self, explainer):
        assert explainer._is_valid_token("1234") is False

    @pytest.mark.unit
    def test_rejects_pure_punctuation(self, explainer):
        assert explainer._is_valid_token("----") is False

    @pytest.mark.unit
    def test_accepts_legal_term(self, explainer):
        assert explainer._is_valid_token("termination") is True

    @pytest.mark.unit
    def test_accepts_long_word(self, explainer):
        assert explainer._is_valid_token("confidentiality") is True

    @pytest.mark.unit
    def test_accepts_valid_mixed_word(self, explainer):
        assert explainer._is_valid_token("payment") is True


# ---------------------------------------------------------------------------
# _boost_score
# ---------------------------------------------------------------------------

class TestBoostScore:
    @pytest.mark.unit
    def test_legal_priority_term_gets_boosted(self, explainer):
        base = 1.0
        boosted = explainer._boost_score("termination", base, "termination clause")
        assert boosted > base

    @pytest.mark.unit
    def test_non_priority_term_not_boosted_as_much(self, explainer):
        base = 1.0
        legal_boosted = explainer._boost_score("termination", base, "termination")
        plain_boosted = explainer._boost_score("xylophone", base, "xylophone")
        assert legal_boosted > plain_boosted

    @pytest.mark.unit
    def test_long_word_gets_minor_boost(self, explainer):
        base = 1.0
        short_boosted = explainer._boost_score("deed", base, "deed")
        long_boosted = explainer._boost_score("confidentiality", base, "confidentiality")
        assert long_boosted > short_boosted

    @pytest.mark.unit
    def test_zero_score_stays_zero(self, explainer):
        result = explainer._boost_score("termination", 0.0, "termination")
        assert result == 0.0


# ---------------------------------------------------------------------------
# _fallback_keywords
# ---------------------------------------------------------------------------

class TestFallbackKeywords:
    @pytest.mark.unit
    def test_returns_list(self, explainer):
        result = explainer._fallback_keywords("This agreement covers payment terms.")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_each_item_has_word_and_score(self, explainer):
        result = explainer._fallback_keywords("payment liability indemnity")
        for item in result:
            assert "word" in item
            assert "score" in item

    @pytest.mark.unit
    def test_respects_top_k(self, explainer):
        long_text = " ".join(["payment", "liability", "indemnity", "jurisdiction",
                               "termination", "confidential", "arbitration", "warranty",
                               "damages", "penalty", "disclosure", "obligations"])
        result = explainer._fallback_keywords(long_text, top_k=3)
        assert len(result) <= 3

    @pytest.mark.unit
    def test_legal_terms_prioritised(self, explainer):
        # Mix legal and non-legal words with similar frequency
        text = "payment payment payment xylophone xylophone xylophone"
        result = explainer._fallback_keywords(text, top_k=5)
        words = [item["word"] for item in result]
        # "payment" is in LEGAL_PRIORITY_TERMS so should score higher
        assert "payment" in words

    @pytest.mark.unit
    def test_stopwords_excluded(self, explainer):
        text = "this agreement between parties shall have such terms"
        result = explainer._fallback_keywords(text, top_k=8)
        words = [item["word"] for item in result]
        stopwords = {"this", "shall", "have", "such", "between"}
        assert not any(w in stopwords for w in words)

    @pytest.mark.unit
    def test_empty_text_returns_fallback(self, explainer):
        result = explainer._fallback_keywords("")
        # Should return something even for empty input
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_words_shorter_than_4_excluded(self, explainer):
        text = "pay fee law act done"
        result = explainer._fallback_keywords(text, top_k=8)
        words = [item["word"] for item in result]
        assert not any(len(w) < 4 for w in words)


# ---------------------------------------------------------------------------
# LEGAL_PRIORITY_TERMS constant sanity checks
# ---------------------------------------------------------------------------

class TestLegalPriorityTerms:
    @pytest.mark.unit
    def test_is_a_set(self):
        assert isinstance(LEGAL_PRIORITY_TERMS, set)

    @pytest.mark.unit
    def test_contains_core_legal_terms(self):
        expected = {"termination", "liability", "payment", "confidential",
                    "indemnity", "arbitration", "jurisdiction", "breach"}
        assert expected.issubset(LEGAL_PRIORITY_TERMS)

    @pytest.mark.unit
    def test_all_lowercase(self):
        assert all(term == term.lower() for term in LEGAL_PRIORITY_TERMS)
