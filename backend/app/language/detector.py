import re

def detect_language(text: str) -> str:
    """
    Detects language style:
    - 'egyptian' if Egyptian dialect markers/phrases are detected.
    - 'ar' if standard Arabic characters predominate.
    - 'en' otherwise.
    """
    if not text:
        return "en"

    # Check for Arabic script
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    arabic_chars = len(arabic_pattern.findall(text))
    total_chars = len(text.strip())

    if arabic_chars / max(total_chars, 1) < 0.2:
        return "en"

    # Egyptian dialect markers
    egyptian_keywords = [
        "ايه", "إيه", "ده", "دي", "دول", "علشان", "عشان", "امتى", "إمتى", 
        "ازاي", "إزاي", "بيتاخد", "بيتاخذ", "بيتعارض", "آثاره", "اثاره", 
        "ممكن اعرف", "انا باخد", "أنا باخد", "أنا باخذ", "هو بيعمل"
    ]

    text_lower = text.lower()
    for kw in egyptian_keywords:
        if kw in text_lower:
            return "egyptian"

    return "ar"
