from enum import Enum
import re
from typing import List, Optional, Set
from pydantic import BaseModel

from app.safety.normalizer import normalize_text
from app.normalization.medication_resolver import extract_all_medications
from app.normalization.symptom_normalizer import extract_symptoms
from app.normalization.device_normalizer import resolve_device

class IntentType(str, Enum):
    GENERAL_MEDICATION_QUESTION = "general_medication_question"
    MEDICATION_SAFETY = "medication_safety"
    DRUG_COMPARISON = "drug_comparison"
    DRUG_INTERACTION = "drug_interaction"
    SYMPTOM_QUESTION = "symptom_question"
    DEVICE_USAGE = "device_usage"
    MEDICATION_PLAN_REQUEST = "medication_plan_request"
    PATIENT_PROFILE_UPDATE = "patient_profile_update"
    CONFIRMATION_RESPONSE = "confirmation_response"
    GENERAL_HEALTH_QUESTION = "general_health_question"

class IntentClassificationResult(BaseModel):
    primary_intent: IntentType
    secondary_intents: List[IntentType] = []
    confidence: float = 1.0

CONFIRMATION_PHRASES: Set[str] = {
    "ايوه", "ايوة", "نعم", "صح", "اه", "تمام", "مضبوط", "بالفعل", "صحيح", "yes", "yeah", "yep", "true",
    "لا", "مش عندي", "مش صحيح", "غلط", "خلاص خفيت", "معنديش", "لاء", "no", "nope", "false", "never"
}

def is_confirmation_reply(text: str) -> bool:
    clean = normalize_text(text)
    words = clean.split()
    if len(words) <= 5:
        for w in words:
            if w in CONFIRMATION_PHRASES:
                return True
        if clean in CONFIRMATION_PHRASES:
            return True
    return False

def detect_intents(
    query_text: str,
    has_pending_confirmation: bool = False,
    candidate_medications: Optional[List[str]] = None,
    candidate_devices: Optional[List[str]] = None,
    candidate_symptoms: Optional[List[str]] = None
) -> IntentClassificationResult:
    q_clean = normalize_text(query_text)
    
    if candidate_medications is not None:
        meds = candidate_medications
    else:
        med_objs = extract_all_medications(query_text)
        meds = [m.canonical_generic for m in med_objs if m.canonical_generic]

    if candidate_devices is not None:
        devices = candidate_devices
    else:
        dev_res = resolve_device(query_text)
        devices = [dev_res[0]] if dev_res else []

    if candidate_symptoms is not None:
        symptoms = candidate_symptoms
    else:
        sym_objs = extract_symptoms(query_text)
        symptoms = [s for s in sym_objs if s]

    intents: List[IntentType] = []

    # 1. Pending Confirmation Response
    if has_pending_confirmation and is_confirmation_reply(q_clean):
        return IntentClassificationResult(
            primary_intent=IntentType.CONFIRMATION_RESPONSE,
            secondary_intents=[]
        )

    # 2. Patient Profile Update
    profile_update_keywords = [
        normalize_text(k) for k in [
            "ضيف للملف", "ضيفها للملف", "سجل في الملف", "سجلها في الملف", "سجل بملفي", "عدل ملفي",
            "update profile", "add to my profile", "save to my profile"
        ]
    ]
    if any(k in q_clean for k in profile_update_keywords):
        intents.append(IntentType.PATIENT_PROFILE_UPDATE)

    # 3. Medication Plan / Draft Prescription Request
    plan_keywords = [
        normalize_text(k) for k in [
            "روشتة", "روشته", "خطة دوائية", "خطة علاجية", "اكتبلي خطة", "اعمل لي خطة",
            "جهزلي الأدوية", "خطة الأدوية", "جدول وخطة", "جدول للادوية", "جدول للأدوية",
            "مراجعة دوائية", "medication plan", "prescription plan", "draft prescription"
        ]
    ]
    if any(k in q_clean for k in plan_keywords):
        intents.append(IntentType.MEDICATION_PLAN_REQUEST)

    # 4. Drug Comparison Intent (e.g. Paracetamol vs Ibuprofen)
    comparison_keywords = [
        normalize_text(k) for k in [
            "ما الفرق بين", "الفرق بين", "ايه الفرق بين", "مقارنة بين", "مقارنه بين",
            "أيهما أفضل", "ايهما افضل", "مين أحسن", "مين احسن", "difference between", "compare", "versus", " vs "
        ]
    ]
    if any(k in q_clean for k in comparison_keywords) or (len(meds) >= 2 and any(k in q_clean for k in [normalize_text(x) for x in ["الفرق", "مقارنة", "vs"]])):
        intents.append(IntentType.DRUG_COMPARISON)

    # 5. Drug-Drug Interaction Intent (Higher precedence than single-drug safety when 2+ drugs or explicit interaction keywords)
    ddi_keywords = [
        normalize_text(k) for k in [
            "يتعارض", "تعارض", "تداخل", "تفاعلات", "تفاعل", "interaction", "interact", "مع بعض", "سوياً", "سويا"
        ]
    ]
    has_taking_together = (" مع " in f" {q_clean} ") and any(k in q_clean for k in [normalize_text(x) for x in ["ينفع", "اخد", "آخد", "اخذ", "أخذ", "take", "taking"]])
    if has_taking_together:
        after_with = q_clean.split("مع", 1)[1].strip() if "مع" in q_clean else ""
        condition_cues = ["قرحة", "ضغط", "سكر", "كلى", "كبد", "حمل", "حامل", "ربو", "قلب", "kidney", "liver", "pregnancy", "asthma", "ulcer"]
        if any(c in after_with for c in condition_cues):
            has_taking_together = False

    is_ddi = any(k in q_clean for k in ddi_keywords) or len(meds) >= 2 or has_taking_together
    if is_ddi and not any(k in q_clean for k in comparison_keywords):
        intents.append(IntentType.DRUG_INTERACTION)

    # 6. Device Usage Intent
    device_keywords = [
        normalize_text(k) for k in [
            "ازاي استخدم", "ازاي أستخدم", "كيف استخدم", "كيف أستخدم", "طريقة استخدام",
            "طريقه استخدام", "طريقة استعمال", "كيفية استخدام", "how to use", "usage of", "جلسة", "جلسه"
        ]
    ]
    if any(k in q_clean for k in device_keywords) or len(devices) > 0 or ("بخاخ" in q_clean) or ("قلم انسولين" in q_clean) or ("قلم أنسولين" in q_clean):
        if any(k in q_clean for k in [normalize_text(x) for x in ["استخدام", "استعمال", "ازاي", "كيف", "طريقة", "كيفية", "how to", "use"]]):
            intents.append(IntentType.DEVICE_USAGE)

    # 7. Personalized Medication Safety (Can I take X / Contraindications / Warnings)
    safety_keywords = [
        normalize_text(k) for k in [
            "ينفع اخد", "ينفع آخد", "ينفع استخدم", "ينفع أستخدم", "هل يناسبني", "هل مناسب لحالتي",
            "موانع استخدام", "موانع استعمال", "أمان", "امان", "آمن", "امن", "أضرار", "اضرار",
            "خطورة", "خطوره", "آثار جانبية", "اثار جانبية", "contraindications", "warnings", "safe for me", "can i take", "pregnant", "حامل"
        ]
    ]
    if any(k in q_clean for k in safety_keywords) or (len(meds) == 1 and any(k in q_clean for k in [normalize_text(x) for x in ["ينفع", "آمن", "موانع", "أضرار", "حامل"]])):
        if IntentType.DRUG_INTERACTION not in intents:
            intents.append(IntentType.MEDICATION_SAFETY)

    # 8. Symptom Question (e.g., I have headache / fever / cough / abdominal cramps)
    symptom_keywords = [
        normalize_text(k) for k in [
            "عندي صداع", "عندي سخونية", "عندي مغص", "عندي كحة", "عندي حساسية", "عندي دوخة",
            "مغص", "تقلصات", "زغللة", "أشعر بألم", "اشعر بالم", "وجع", "ألم في", "الم في", "سخونة", "حمى", "حرارة", "احتقان", "symptom", "i have", "pain", "cough", "fever"
        ]
    ]
    if len(symptoms) > 0 or any(k in q_clean for k in symptom_keywords):
        if not any(k in q_clean for k in profile_update_keywords):
            intents.append(IntentType.SYMPTOM_QUESTION)

    # 9. General Medication Question (e.g., What is Metformin / How does X work?)
    general_med_keywords = [
        normalize_text(k) for k in [
            "ما هو", "ما هي", "ماهو", "ماهي", "دواعي استعمال", "دواعي استخدام", "فيما يستخدم",
            "ما فائدة", "فوائد", "جرعة", "جرعه", "what is", "used for", "mechanism", "indications"
        ]
    ]
    if (len(meds) >= 1 and not intents) or any(k in q_clean for k in general_med_keywords):
        if not intents:
            intents.append(IntentType.GENERAL_MEDICATION_QUESTION)

    # 10. General Health Question / Advice
    health_advice_keywords = [
        normalize_text(k) for k in [
            "نصائح", "نصائح عامة", "صحة القلب", "شرب المياه", "تناول المياه", "نظام غذائي", "health tips", "general advice"
        ]
    ]
    if any(k in q_clean for k in health_advice_keywords):
        intents.append(IntentType.GENERAL_HEALTH_QUESTION)

    # Fallback: General Health Question
    if not intents:
        intents.append(IntentType.GENERAL_HEALTH_QUESTION)

    return IntentClassificationResult(
        primary_intent=intents[0],
        secondary_intents=intents[1:]
    )
