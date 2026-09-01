import re
from typing import List, Optional, Tuple
from .text_normalizer import normalize_arabic_text
from .medication_resolver import MedicationResolutionResult

INTENT_KEYWORD_MAP = {
    "contraindications": [
        "موانع", "ممنوع", "contraindication", "contraindications", "hypersensitivity", "allergy", "حساسية", "penicillin"
    ],
    "dosage_adjustment": [
        "renal adjustment", "kidney adjustment", "hepatic adjustment", "altered kidney function",
        "تعديل الجرعة", "مرضى الكلى", "مرضى الكبد", "قصور كلوي"
    ],
    "administration": [
        "administered", "administer", "administration", "how to take", "take with food", "empty stomach",
        "طريقة", "كيفية", "ازاي", "طريقة استعمال", "طريقة استخدام", "طريقة اخذ", "طريقة أخذ", "طريقة إعطاء"
    ],
    "high_alert": [
        "high alert", "high-alert", "narrow therapeutic", "عالي الخطورة", "عالية الخطورة", "خطورة", "عقار عالي الخطورة"
    ],
    "do_not_crush": [
        "do not crush", "crush", "chew", "extended release", "sustained release", "enteric coated",
        "كسر", "طحن", "ممتدة المفعول", "ممتد المفعول", "مغلفة معويا", "مغلفة"
    ],
    "drug_interactions": [
        "interaction", "interactions", "interact", "cyp3a4", "bleeding", "ace inhibitors",
        "تعارض", "تفاعل", "تداخل", "تداخلات", "مع بعض", "تفاعلات"
    ],
    "adverse_reactions": [
        "side effects", "adverse reactions", "adverse effects", "tendon rupture", "tendinitis",
        "اثار جانبية", "آثار جانبية", "اعراض جانبية", "أعراض جانبية", "أوتار", "اوتار", "تمزق"
    ],
    "pregnancy_lactation": [
        "pregnancy", "lactation", "breastfeeding", "pregnant", "teratogenic",
        "حمل", "حامل", "رضاعة", "مرضع", "جنين"
    ],
    "dosage": [
        "dose", "dosage", "how much", "maximum dose", "maximum daily dose", "dosage forms", "strengths", "available forms",
        "جرعة", "جرعه", "كمية", "الجرعة القصوى", "أشكال دوائية", "اشكال دوائية", "تركيزات"
    ],
    "warnings_precautions": [
        "warning", "warnings", "precaution", "precautions", "monitoring", "diabetic", "diabetes",
        "تحذير", "تحذيرات", "احتياط", "احتياطات", "سكر", "مرضى السكر"
    ],
    "indications": [
        "indication", "indications", "therapeutic uses", "what is it used for", "approved uses", "ulcer",
        "دواعي", "استعمال", "استخدام", "فائدة", "علاج", "قرحة"
    ]
}

def detect_query_section(query_text: str) -> str:
    """Detects the primary canonical section intent from user query."""
    clean_q = normalize_arabic_text(query_text).lower()
    for section, keywords in INTENT_KEYWORD_MAP.items():
        for k in keywords:
            k_clean = normalize_arabic_text(k).lower()
            if k_clean in clean_q:
                return section
    return "indications"

def build_canonical_retrieval_query(
    query_text: str,
    intent: str,
    resolved_medications: List[MedicationResolutionResult]
) -> str:
    """
    Constructs a concise, targeted English retrieval query for the English EDA PDF corpus
    from Arabic or English user queries using canonical drug entities, focused section concepts,
    and specific clinical modifiers.
    """
    clean_q = normalize_arabic_text(query_text).lower()
    
    # 1. Collect canonical generic names
    med_names = [m.canonical_generic for m in resolved_medications if m.canonical_generic]
    
    # 2. Detect primary section concept
    detected_sec = detect_query_section(query_text)
    section_term = detected_sec.replace("_", " ")

    # 3. Detect specific clinical modifiers
    modifiers = []
    if "oral" in clean_q or "فموي" in clean_q or "أقراص" in clean_q or "اقراص" in clean_q:
        modifiers.append("oral")
    if "sublingual" in clean_q or "تحت اللسان" in clean_q:
        modifiers.append("sublingual")
    if "rheumat" in clean_q or "روماتيزم" in clean_q or "مفاصل" in clean_q:
        modifiers.append("rheumatoid arthritis")
    if "angina" in clean_q or "ذبحة" in clean_q:
        modifiers.append("angina")
    if "cyp3a4" in clean_q:
        modifiers.append("cyp3a4")
    if "ace inhibitor" in clean_q:
        modifiers.append("ace inhibitors")
    if "81 mg" in clean_q or "81" in clean_q:
        modifiers.append("81 mg")
    if any(normalize_arabic_text(k).lower() in clean_q for k in ["extended release", "ممتدة المفعول", "ممتد المفعول"]):
        modifiers.append("extended release dose dumping")
    elif any(normalize_arabic_text(k).lower() in clean_q for k in ["enteric coated", "مغلفة معويا", "مغلفة", "مغلفه"]):
        modifiers.append("enteric coated gastric acid")
    elif any(normalize_arabic_text(k).lower() in clean_q for k in ["do not crush", "طحن", "كسر"]):
        modifiers.append("do not crush")

    if any(normalize_arabic_text(k).lower() in clean_q for k in ["high alert", "عالي الخطورة", "عالية الخطورة", "خطورة"]):
        modifiers.append("high alert")

    if any(normalize_arabic_text(k).lower() in clean_q for k in ["otc", "over the counter", "الجرعة القصوى", "بدون وصفة"]):
        modifiers.append("otc")

    mod_str = f" {' '.join(modifiers)}" if modifiers else ""

    # 4. Assemble concise query
    if med_names:
        med_str = " ".join(med_names)
        return f"{med_str} {section_term}{mod_str}".strip()

    return f"{clean_q} {section_term}{mod_str}".strip()
