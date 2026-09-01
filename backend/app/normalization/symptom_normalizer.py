from typing import Dict, List, Optional
from .text_normalizer import normalize_arabic_text

SYMPTOM_ALIASES: Dict[str, str] = {
    "صداع": "headache",
    "صداع نصفي": "migraine",
    "وجع راس": "headache",
    "الم راس": "headache",
    "وجع في الراس": "headache",
    "سخونية": "fever",
    "سخونة": "fever",
    "حرارة": "fever",
    "ارتفاع حرارة": "fever",
    "حمى": "fever",
    "كحة": "cough",
    "سعال": "cough",
    "كحة ناشفة": "dry_cough",
    "كحة ببلغم": "productive_cough",
    "مغص": "abdominal_cramps",
    "الم بطن": "abdominal_pain",
    "وجع بطن": "abdominal_pain",
    "تقلصات": "abdominal_cramps",
    "غثيان": "nausea",
    "ترجيع": "vomiting",
    "قيء": "vomiting",
    "دوخة": "dizziness",
    "دوار": "vertigo",
    "زغللة": "blurred_vision",
    "احتقان في الزور": "sore_throat",
    "احتقان في الحلق": "sore_throat",
    "احتقان زور": "sore_throat",
    "احتقان": "nasal_congestion",
    "الم حلق": "sore_throat",
    "وجع زور": "sore_throat",
    "التهاب حلق": "sore_throat",
    "رشح": "rhinorrhea",
    "زكام": "rhinorrhea",
    "الم في المفاصل": "arthralgia",
    "وجع في المفاصل": "arthralgia",
    "الم مفاصل": "arthralgia",
    "وجع مفاصل": "arthralgia",
    "الم عضلات": "myalgia",
    "الم في العضلات": "myalgia",
    "حرقان معدة": "heartburn",
    "حموضة": "heartburn",
    "ارتجاع": "reflux",
    "أرق": "insomnia",
    "ارق": "insomnia",
    "اسهال": "diarrhea",
    "امساك": "constipation"
}

def extract_symptoms(text: str) -> List[str]:
    """
    Extracts symptoms mentioned in user text.
    NOTE: Symptoms are returned strictly as symptoms and NEVER inferred as chronic diseases.
    """
    clean = normalize_arabic_text(text)
    extracted: List[str] = []

    sorted_symptoms = sorted(SYMPTOM_ALIASES.items(), key=lambda x: len(normalize_arabic_text(x[0])), reverse=True)
    for alias_k, canonical_v in sorted_symptoms:
        norm_alias = normalize_arabic_text(alias_k)
        if norm_alias in clean and canonical_v not in extracted:
            extracted.append(canonical_v)

    return extracted
