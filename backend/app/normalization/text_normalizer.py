import re

def normalize_arabic_text(text: str) -> str:
    """
    Standardizes Arabic text:
    - Removes diacritics / tashkeel
    - Removes Tatweel / Kashida (ـ)
    - Normalizes Alef forms (أ, إ, آ -> ا)
    - Normalizes Teh Marbuta (ة -> ه)
    - Normalizes Yeh / Alef Maqsura (ى -> ي)
    - Normalizes multiple spaces and punctuation
    """
    if not text:
        return ""

    t = text.lower().strip()

    # 1. Remove Tashkeel / Diacritics
    tashkeel = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670]')
    t = re.sub(tashkeel, '', t)

    # 2. Remove Tatweel / Kashida (ـ)
    t = re.sub(r'[\u0640]', '', t)

    # 3. Normalize Alef forms
    t = re.sub(r'[أإآٱ]', 'ا', t)

    # 4. Normalize Teh Marbuta
    t = re.sub(r'ة', 'ه', t)

    # 5. Normalize Yeh / Alef Maqsura
    t = re.sub(r'[ىي]', 'ي', t)

    # 6. Normalize English characters to lowercase
    t = t.lower()

    # 7. Clean punctuation & excessive whitespace
    t = re.sub(r'[؟?!.,;:\"\'()\[\]{}_/\\-]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()

    return t

def normalize_medical_query(text: str) -> str:
    """Convenience wrapper for normalizing medical query strings."""
    return normalize_arabic_text(text)

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]
