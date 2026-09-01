import re

def normalize_arabic(text: str) -> str:
    """
    Standardizes Arabic text:
    - Removes diacritics / tashkeel
    - Normalizes Alefs (أ, إ, آ -> ا)
    - Normalizes Teh Marbuta (ة -> ه)
    - Normalizes Yeh (ى -> ي)
    """
    if not text:
        return ""

    # Remove tashkeel
    tashkeel = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel, '', text)

    # Normalize alef
    text = re.sub(r'[أإآ]', 'ا', text)

    # Normalize teh marbuta
    text = re.sub(r'ة', 'ه', text)

    # Normalize yeh
    text = re.sub(r'ى', 'ي', text)

    return text.strip()
