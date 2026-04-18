import re


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,;:()%/$£₹-]", " ", text)
    return text.strip()