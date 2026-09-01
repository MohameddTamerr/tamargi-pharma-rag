import re
from app.language.arabic import normalize_arabic

EGYPTIAN_TO_MEDICAL_MAP = {
    r"ايه موانع استخدام": "contraindications",
    r"إيه موانع استخدام": "contraindications",
    r"موانع استخدامه": "contraindications",
    r"موانع الاستخدام": "contraindications",
    r"بيتاخد امتى": "dosage administration frequency timing",
    r"امتى بيتاخد": "dosage administration frequency timing",
    r"طريقة الاستخدام": "dosage administration",
    r"جرعة": "dosage dose",
    r"جرعته": "dosage dose",
    r"بيتعارض مع ادوية ايه": "drug interactions contraindications",
    r"الآثار الجانبية": "adverse drug reactions side effects",
    r"الآثار الجانبيه": "adverse drug reactions side effects",
    r"اثاره الجانبية": "adverse drug reactions side effects",
    r"اعراضه الجانبية": "adverse drug reactions side effects",
    r"بيعمل ايه": "indications mechanism of action",
    r"دوا ده": "drug medication",
    r"الدوا ده": "drug medication",
    # Comparison patterns (Egyptian dialect)
    r"ايه الفرق بين": "comparison difference",
    r"إيه الفرق بين": "comparison difference",
    r"الفرق بين": "comparison difference",
    r"احسن من": "comparison better preferred",
    r"أحسن من": "comparison better preferred",
    r"افضل من": "comparison better preferred",
    # Symptom patterns (Egyptian colloquial)
    r"عندي برد": "symptoms common colds and flu fever Brufen Paracetamol Cetafen Panadol Stopadol OTC",
    r"عندي انفلونزا": "symptoms common colds and flu fever Paracetamol Ibuprofen Panadol Cold Flu OTC",
    r"عندي زكام": "symptoms common colds and flu congestion fever Panadol Sinus Relief Stopadol OTC",
    r"عندي رشح": "symptoms common colds and flu Panadol Cold Flu Stopadol OTC",
    r"عندي صداع": "symptomatic relief of headache including migraine headache mild to moderate pain Brufen Flamotal Spididol Panadol Stopadol Extra Ibuprofen Paracetamol OTC",
    r"عندي حموضة": "heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Healsec Controloc Pepzole Omez Gastrazole Protofix OTC",
    r"عندي حرقان": "heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Healsec Controloc Pepzole Omez OTC",
    r"عندي سخونية": "fever antipyretic mild to moderate pain Brufen Paracetamol Ibuprofen Arkadolow Cetafen OTC",
    r"عندي حرارة": "fever antipyretic mild to moderate pain Brufen Paracetamol Ibuprofen Arkadolow OTC",
    r"سخونية": "fever antipyretic mild to moderate pain Brufen Paracetamol Ibuprofen Arkadolow Cetafen OTC",
    r"اخد ايه": "approved indication dosage administration OTC",
    r"أخد إيه": "approved indication dosage administration OTC",
    r"اخد ايه للبرد": "symptoms common colds and flu fever Brufen Paracetamol Cetafen Panadol Stopadol OTC",
}

def normalize_egyptian_query(query: str) -> str:
    """
    Translates Egyptian colloquial medical patterns into search-optimized medical terms
    while extracting embedded English or generic drug names.
    Returns a retrieval-friendly query string.
    """
    if not query:
        return ""

    # Extract any English drug names embedded in query (e.g. "Anidulafungin")
    english_words = re.findall(r'[A-Za-z0-9\-]+', query)
    english_str = " ".join(english_words)

    normalized = normalize_arabic(query)
    expanded_terms = []
    seen_replacements = set()

    for pattern, replacement in EGYPTIAN_TO_MEDICAL_MAP.items():
        pattern_norm = normalize_arabic(pattern)
        if pattern_norm in normalized and replacement not in seen_replacements:
            expanded_terms.append(replacement)
            seen_replacements.add(replacement)

    # Reconstruct optimized medical search query
    parts = []
    if english_str:
        parts.append(english_str)
    
    parts.append(query) # Keep original query
    
    if expanded_terms:
        parts.extend(expanded_terms)

    return " ".join(parts).strip()
