import re

try:
    import spacy
except ImportError:
    spacy = None


_NLP = None


ALLOWED_ENTITY_LABELS = {
    "PERSON",
    "ORG",
    "DATE",
    "MONEY",
    "GPE",
    "LOC",
    "LAW",
    "NORP",
    "PRODUCT",
    "EVENT"
}


NOISY_ENTITY_TEXTS = {
    "one", "two", "three", "first", "second", "third",
    "hereby", "thereof", "whereas", "shall", "said",
    "agreement", "document", "contract", "party", "parties"
}


def get_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP

    if spacy is None:
        return None

    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None

    return _NLP


def _clean_entity_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[^\w₹$£]+|[^\w₹$£]+$", "", text)
    return text


def _is_valid_entity(text: str, label: str) -> bool:
    if not text:
        return False

    cleaned = _clean_entity_text(text)
    lowered = cleaned.lower()

    if not cleaned:
        return False

    if lowered in NOISY_ENTITY_TEXTS:
        return False

    if len(cleaned) < 3:
        return False

    if cleaned.isdigit():
        return False

    if label not in ALLOWED_ENTITY_LABELS:
        return False

    
    if " " not in cleaned and cleaned.islower() and label in {"PERSON", "ORG", "GPE", "LOC"}:
        return False

    
    if label == "PERSON":
        if len(cleaned.split()) == 1:
            if lowered in {
                "fire", "payment", "notice", "delivery", "services",
                "policy", "agreement", "termination", "liability"
            }:
                return False

   
    if label == "ORG":
        if lowered in {"company", "corporation", "bank", "university"}:
            return False

    return True


def _deduplicate_entities(entities: list) -> list:
    seen = set()
    unique = []

    for item in entities:
        text = _clean_entity_text(item.get("text", ""))
        label = item.get("label", "").strip()

        key = (text.lower(), label)
        if key not in seen:
            seen.add(key)
            unique.append({"text": text, "label": label})

    return unique


def regex_entities(text: str) -> list:
    entities = []

    patterns = [
        ("DATE", r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b"),
        ("MONEY", r"\b(?:USD|INR|GBP|EUR|\$|₹|£|€)\s?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[Mm]illion|[Bbp]illion|[Kk]|[Tt]housand)?\b"),
        ("LAW", r"\b(?:Indian Contract Act|Companies Act|Data Protection Act|GDPR|Information Technology Act)\b"),
        ("ORG", r"\b[A-Z][A-Za-z0-9&,\- ]+(?:Ltd|Limited|LLP|LLC|Corporation|Corp|Company|Bank|University|Technologies|Systems|Solutions|Private Limited|Pvt Ltd)\b"),
        ("PERSON", r"\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"),
        ("GPE", r"\b(?:India|Scotland|England|London|Edinburgh|Glasgow|Delhi|Mumbai|Bangalore|Faridabad)\b"),
    ]

    for label, pattern in patterns:
        for match in re.finditer(pattern, text):
            value = _clean_entity_text(match.group())
            if _is_valid_entity(value, label):
                entities.append({"text": value, "label": label})

    return _deduplicate_entities(entities)


def extract_entities(text: str) -> list:
    if not text or not text.strip():
        return []

    nlp = get_nlp()
    collected = []

    if nlp is not None:
        try:
            doc = nlp(text)

            for ent in doc.ents:
                cleaned_text = _clean_entity_text(ent.text)
                label = ent.label_.strip()

                if _is_valid_entity(cleaned_text, label):
                    collected.append({"text": cleaned_text, "label": label})
        except Exception:
            collected = []

    
    regex_found = regex_entities(text)
    collected.extend(regex_found)

    cleaned_entities = _deduplicate_entities(collected)

    
    cleaned_entities = sorted(
        cleaned_entities,
        key=lambda x: (x["label"], -len(x["text"]))
    )

    return cleaned_entities[:12]