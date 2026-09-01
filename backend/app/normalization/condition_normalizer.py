from typing import Dict, Optional, List
from .text_normalizer import normalize_arabic_text

CONDITION_ALIASES: Dict[str, str] = {
    # Diabetes
    "مرض السكر": "diabetes_mellitus",
    "السكر": "diabetes_mellitus",
    "سكر": "diabetes_mellitus",
    "السكري": "diabetes_mellitus",
    "مرض السكري": "diabetes_mellitus",
    "ارتفاع السكر": "diabetes_mellitus",
    "diabetes": "diabetes_mellitus",
    "diabetes mellitus": "diabetes_mellitus",
    "dm": "diabetes_mellitus",
    "type 2 diabetes": "diabetes_mellitus",
    "type 1 diabetes": "diabetes_mellitus",

    # Hypertension
    "الضغط": "hypertension",
    "ضغط": "hypertension",
    "ضغط عالي": "hypertension",
    "ضغط الدم": "hypertension",
    "مرض الضغط": "hypertension",
    "ارتفاع ضغط الدم": "hypertension",
    "hypertension": "hypertension",
    "htn": "hypertension",
    "high blood pressure": "hypertension",

    # Asthma & Pulmonary
    "الربو": "asthma",
    "ربو": "asthma",
    "حساسية صدر": "asthma",
    "حساسية الصدر": "asthma",
    "ازمة ربو": "asthma",
    "ضيق تنفس": "asthma",
    "asthma": "asthma",
    "bronchial asthma": "asthma",
    "copd": "copd",
    "سدة رئوية": "copd",

    # Chronic Kidney Disease
    "الكلى": "chronic_kidney_disease",
    "كلى": "chronic_kidney_disease",
    "قصور كلوي": "chronic_kidney_disease",
    "قصور في الكلى": "chronic_kidney_disease",
    "فشل كلوي": "chronic_kidney_disease",
    "اعتلال كلوي": "chronic_kidney_disease",
    "chronic kidney disease": "chronic_kidney_disease",
    "ckd": "chronic_kidney_disease",
    "renal impairment": "chronic_kidney_disease",
    "renal failure": "chronic_kidney_disease",

    # Peptic Ulcer Disease
    "قرحة معدة": "peptic_ulcer_disease",
    "قرحة في المعدة": "peptic_ulcer_disease",
    "قرحة": "peptic_ulcer_disease",
    "قرحة هضمية": "peptic_ulcer_disease",
    "peptic ulcer": "peptic_ulcer_disease",
    "peptic ulcer disease": "peptic_ulcer_disease",
    "gastric ulcer": "peptic_ulcer_disease",
    "stomach ulcer": "peptic_ulcer_disease",

    # Hepatic Impairment
    "كبد": "hepatic_impairment",
    "قصور كبدي": "hepatic_impairment",
    "تليف كبد": "hepatic_impairment",
    "تليف الكبد": "hepatic_impairment",
    "فشل كبدي": "hepatic_impairment",
    "hepatic impairment": "hepatic_impairment",
    "liver cirrhosis": "hepatic_impairment",
    "liver failure": "hepatic_impairment",

    # Explicit Heart Failure Only
    "فشل عضلة القلب": "heart_failure",
    "ضعف عضلة القلب": "heart_failure",
    "هبوط القلب": "heart_failure",
    "قصور القلب": "heart_failure",
    "heart failure": "heart_failure",
    "chf": "heart_failure",

    # Bleeding Disorders
    "سيولة": "bleeding_disorder",
    "سيولة في الدم": "bleeding_disorder",
    "نزيف": "bleeding_disorder",
    "هيموفيليا": "bleeding_disorder",
    "bleeding disorder": "bleeding_disorder",
    "hemophilia": "bleeding_disorder"
}

def normalize_condition_name(condition_text: str) -> str:
    """Normalizes Arabic/English condition terms to standard clinical keys."""
    if not condition_text:
        return ""
    
    clean = normalize_arabic_text(condition_text)
    
    for alias_k, canonical_v in CONDITION_ALIASES.items():
        norm_alias = normalize_arabic_text(alias_k)
        if norm_alias == clean or norm_alias in clean or clean in norm_alias:
            return canonical_v
            
    return clean.replace(" ", "_")

def extract_conditions(text: str) -> List[str]:
    """Extracts confirmed condition entities from text."""
    clean = normalize_arabic_text(text)
    extracted: List[str] = []
    
    for alias_k, canonical_v in CONDITION_ALIASES.items():
        norm_alias = normalize_arabic_text(alias_k)
        if norm_alias in clean and canonical_v not in extracted:
            extracted.append(canonical_v)
            
    return extracted
