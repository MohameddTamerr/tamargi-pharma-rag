from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import uuid
import re

from app.database.supabase import get_supabase_client
from .models import (
    PatientProfileData,
    PatientCondition,
    PatientAllergy,
    PatientMedication,
    PatientHistoryItem,
    PendingConfirmation,
    ConfirmationStatus
)
from .normalizer import (
    normalize_text,
    normalize_medication_name,
    normalize_condition_name,
    normalize_allergen_name
)

# In-memory store for offline/unit-testing environments
IN_MEMORY_PROFILES: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_CONDITIONS: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_ALLERGIES: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_MEDICATIONS: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_CONFIRMATIONS: Dict[str, List[Dict[str, Any]]] = {}

# Confirmation Phrasing Patterns
AFFIRMATIVE_PATTERNS = [
    r"^(?:ايوه|أيوة|ايوة|أيو|صح|اه|أه|تمام|مظبوط|مضبوط|لسه\s+عندي|ما\s+زال|نعم|بالتأكيد|صحيح)$",
    r"^(?:yes|yeah|yep|correct|true|still\s+have|i\s+do|right)$",
    r"(?:ايوه|صح|لسه\s+عندي|نعم|yes|correct)"
]

NEGATIVE_PATTERNS = [
    r"^(?:لا|لأ|مش\s+عندي|خفيت|راحت|غير\s+صحيح|ما\s+عنديش|معنديش|مش\s+باخده|وقفته)$",
    r"^(?:no|nope|not\s+anymore|don't\s+have|cured|stopped|false|incorrect)$",
    r"(?:لا|مش\s+عندي|معنديش|خفيت|no|stopped)"
]

def reset_in_memory_store():
    """Helper for testing: clears all mock profile data."""
    IN_MEMORY_PROFILES.clear()
    IN_MEMORY_CONDITIONS.clear()
    IN_MEMORY_ALLERGIES.clear()
    IN_MEMORY_MEDICATIONS.clear()
    IN_MEMORY_HISTORY.clear()
    IN_MEMORY_CONFIRMATIONS.clear()

def get_patient_profile(user_id: str) -> PatientProfileData:
    """
    Loads complete structured patient profile for a user.
    Enforces privacy by filtering strictly on user_id.
    """
    if not user_id:
        return PatientProfileData(user_id="anonymous")

    client = get_supabase_client()
    if client:
        try:
            p_res = client.table("patient_profiles").select("*").eq("user_id", user_id).execute()
            prof = p_res.data[0] if p_res.data else {}

            c_res = client.table("patient_conditions").select("*").eq("user_id", user_id).eq("active", True).execute()
            a_res = client.table("patient_allergies").select("*").eq("user_id", user_id).eq("active", True).execute()
            m_res = client.table("patient_medications").select("*").eq("user_id", user_id).eq("active", True).execute()
            h_res = client.table("patient_medical_history").select("*").eq("user_id", user_id).eq("active", True).execute()

            return PatientProfileData(
                user_id=user_id,
                date_of_birth=prof.get("date_of_birth"),
                sex=prof.get("sex"),
                pregnancy_status=prof.get("pregnancy_status", "none"),
                breastfeeding_status=prof.get("breastfeeding_status", "none"),
                weight_kg=prof.get("weight_kg"),
                height_cm=prof.get("height_cm"),
                conditions=[PatientCondition(**r) for r in c_res.data or []],
                allergies=[PatientAllergy(**r) for r in a_res.data or []],
                medications=[PatientMedication(**r) for r in m_res.data or []],
                medical_history=[PatientHistoryItem(**r) for r in h_res.data or []]
            )
        except Exception as e:
            print(f"[Supabase Profile Load Warning] {e}")

    # In-memory fallback
    prof = IN_MEMORY_PROFILES.get(user_id, {})
    conds = [PatientCondition(**c) for c in IN_MEMORY_CONDITIONS.get(user_id, []) if c.get("active", True)]
    allgs = [PatientAllergy(**a) for a in IN_MEMORY_ALLERGIES.get(user_id, []) if a.get("active", True)]
    meds = [PatientMedication(**m) for m in IN_MEMORY_MEDICATIONS.get(user_id, []) if m.get("active", True)]
    hist = [PatientHistoryItem(**h) for h in IN_MEMORY_HISTORY.get(user_id, []) if h.get("active", True)]

    return PatientProfileData(
        user_id=user_id,
        date_of_birth=prof.get("date_of_birth"),
        sex=prof.get("sex"),
        pregnancy_status=prof.get("pregnancy_status", "none"),
        breastfeeding_status=prof.get("breastfeeding_status", "none"),
        weight_kg=prof.get("weight_kg"),
        height_cm=prof.get("height_cm"),
        conditions=conds,
        allergies=allgs,
        medications=meds,
        medical_history=hist
    )

def get_active_pending_confirmation(user_id: str, conversation_id: str) -> Optional[PendingConfirmation]:
    """Finds any pending confirmation prompt awaiting user response."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("pending_medical_confirmations")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("conversation_id", conversation_id)\
                .eq("status", "pending")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if res.data:
                return PendingConfirmation(**res.data[0])
        except Exception:
            pass

    for item in reversed(IN_MEMORY_CONFIRMATIONS.get(user_id, [])):
        if item.get("conversation_id") == conversation_id and item.get("status") == "pending":
            return PendingConfirmation(**item)
    return None

def create_pending_confirmation(
    user_id: str,
    conversation_id: str,
    fact_type: str,
    fact_id: Optional[str],
    normalized_value: str,
    original_question: str,
    medication_context: Optional[str] = None
) -> PendingConfirmation:
    """Stores a pending confirmation in the database."""
    conf = PendingConfirmation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        conversation_id=conversation_id,
        fact_type=fact_type,
        fact_id=fact_id,
        normalized_value=normalized_value,
        original_question=original_question,
        medication_context=medication_context,
        status="pending",
        created_at=datetime.now()
    )

    client = get_supabase_client()
    if client:
        try:
            client.table("pending_medical_confirmations").insert(conf.model_dump(mode="json")).execute()
        except Exception:
            pass

    if user_id not in IN_MEMORY_CONFIRMATIONS:
        IN_MEMORY_CONFIRMATIONS[user_id] = []
    IN_MEMORY_CONFIRMATIONS[user_id].append(conf.model_dump(mode="json"))
    return conf

def resolve_pending_confirmation(
    user_id: str,
    conversation_id: str,
    user_message: str
) -> Tuple[bool, Optional[str], Optional[PendingConfirmation]]:
    """
    Checks if user response resolves a pending confirmation.
    
    Returns:
        (is_resolved: bool, decision: 'confirmed' | 'denied' | None, confirmation: Optional[PendingConfirmation])
    """
    pending = get_active_pending_confirmation(user_id, conversation_id)
    if not pending:
        return (False, None, None)

    msg_clean = normalize_text(user_message)
    is_affirmative = any(re.search(pat, msg_clean, re.IGNORECASE) for pat in AFFIRMATIVE_PATTERNS)
    is_negative = any(re.search(pat, msg_clean, re.IGNORECASE) for pat in NEGATIVE_PATTERNS)

    if not is_affirmative and not is_negative:
        return (False, None, pending)

    resolution = "confirmed" if is_affirmative else "denied"
    now_time = datetime.now()

    # 1. Update pending confirmation record
    client = get_supabase_client()
    if client:
        try:
            client.table("pending_medical_confirmations")\
                .update({"status": resolution, "resolved_at": now_time.isoformat()})\
                .eq("id", pending.id)\
                .execute()
        except Exception:
            pass

    for item in IN_MEMORY_CONFIRMATIONS.get(user_id, []):
        if item.get("id") == pending.id:
            item["status"] = resolution
            item["resolved_at"] = now_time

    # 2. Update underlying medical fact table
    fact_table_map = {
        "condition": "patient_conditions",
        "allergy": "patient_allergies",
        "medication": "patient_medications",
        "history": "patient_medical_history"
    }

    table_name = fact_table_map.get(pending.fact_type)
    if table_name and pending.fact_id:
        update_data = {
            "last_confirmed_at": now_time.isoformat()
        }
        if resolution == "confirmed":
            update_data["confirmed"] = True
            update_data["active"] = True
        else: # Denied -> Soft delete (active = false for auditability)
            update_data["active"] = False

        if client:
            try:
                client.table(table_name).update(update_data).eq("id", pending.fact_id).execute()
            except Exception:
                pass

        # Update in-memory
        mem_dict = {
            "condition": IN_MEMORY_CONDITIONS,
            "allergy": IN_MEMORY_ALLERGIES,
            "medication": IN_MEMORY_MEDICATIONS,
            "history": IN_MEMORY_HISTORY
        }.get(pending.fact_type, {})

        for fact in mem_dict.get(user_id, []):
            if fact.get("id") == pending.fact_id:
                if resolution == "confirmed":
                    fact["confirmed"] = True
                    fact["active"] = True
                else:
                    fact["active"] = False
                fact["last_confirmed_at"] = now_time

    return (True, resolution, pending)

def add_patient_condition(user_id: str, condition_name: str, confirmed: bool = True) -> PatientCondition:
    """Inserts a structured patient condition."""
    norm = normalize_condition_name(condition_name)
    c_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "condition_name": condition_name,
        "normalized_condition": norm,
        "status": "active",
        "confirmed": confirmed,
        "last_confirmed_at": datetime.now() if confirmed else None,
        "source": "chat",
        "active": True,
        "created_at": datetime.now()
    }
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_conditions").insert(c_data).execute()
        except Exception:
            pass
    if user_id not in IN_MEMORY_CONDITIONS:
        IN_MEMORY_CONDITIONS[user_id] = []
    IN_MEMORY_CONDITIONS[user_id].append(c_data)
    return PatientCondition(**c_data)

def add_patient_allergy(user_id: str, allergen: str, confirmed: bool = True, severity: str = "moderate") -> PatientAllergy:
    """Inserts a structured patient allergy."""
    can_allergen, a_class = normalize_allergen_name(allergen)
    a_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "allergen": allergen,
        "normalized_allergen": can_allergen,
        "reaction": None,
        "severity": severity,
        "confirmed": confirmed,
        "last_confirmed_at": datetime.now() if confirmed else None,
        "active": True,
        "created_at": datetime.now()
    }
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_allergies").insert(a_data).execute()
        except Exception:
            pass
    if user_id not in IN_MEMORY_ALLERGIES:
        IN_MEMORY_ALLERGIES[user_id] = []
    IN_MEMORY_ALLERGIES[user_id].append(a_data)
    return PatientAllergy(**a_data)

def add_patient_medication(
    user_id: str,
    generic_name: str,
    brand_name: Optional[str] = None,
    strength: Optional[str] = None,
    dose: Optional[str] = None,
    confirmed: bool = True
) -> PatientMedication:
    """Inserts a structured patient medication."""
    gen_norm, detected_brand = normalize_medication_name(generic_name)
    m_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "generic_name": gen_norm,
        "brand_name": brand_name or detected_brand,
        "strength": strength,
        "dosage_form": None,
        "dose": dose,
        "frequency": None,
        "indication": None,
        "confirmed": confirmed,
        "last_confirmed_at": datetime.now() if confirmed else None,
        "active": True,
        "created_at": datetime.now()
    }
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_medications").insert(m_data).execute()
        except Exception:
            pass
    if user_id not in IN_MEMORY_MEDICATIONS:
        IN_MEMORY_MEDICATIONS[user_id] = []
    IN_MEMORY_MEDICATIONS[user_id].append(m_data)
    return PatientMedication(**m_data)

def add_patient_history(
    user_id: str,
    history_type: str,
    value: str,
    confirmed: bool = True
) -> PatientHistoryItem:
    """Inserts a structured patient history item."""
    h_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "history_type": history_type,
        "value": value,
        "normalized_value": normalize_text(value),
        "confirmed": confirmed,
        "last_confirmed_at": datetime.now() if confirmed else None,
        "active": True,
        "created_at": datetime.now()
    }
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_medical_history").insert(h_data).execute()
        except Exception:
            pass
    if user_id not in IN_MEMORY_HISTORY:
        IN_MEMORY_HISTORY[user_id] = []
    IN_MEMORY_HISTORY[user_id].append(h_data)
    return PatientHistoryItem(**h_data)

def extract_patient_facts_from_chat(user_id: str, text: str) -> List[Dict[str, Any]]:
    """
    Carefully extracts explicit user-asserted profile facts from chat.
    
    Rules:
    - Explicit diagnosis statements ("أنا عندي سكر", "عندي حساسية من البنسلين") -> stored.
    - Explicit medication statements ("باخد Metformin 500 mg") -> stored as medication, NOT diagnosis.
    - Uncertain statements ("أعتقد", "ممكن يكون عندي حساسية") -> stored with confirmed=False.
    - Symptom statements ("عندي كحة وسخونية") -> NEVER hallucinated into a stored chronic disease.
    """
    if not text or not user_id or user_id == "anonymous":
        return []

    extracted = []
    text_norm = normalize_text(text)

    # 1. Condition Extraction
    if re.search(r"(?:انا|أنا|عندي|تم تشخيصي ب)\s+(?:مرض\s+)?(?:السكر|سكر|السكري)", text_norm):
        cond = add_patient_condition(user_id, "Diabetes Mellitus", confirmed=True)
        extracted.append({"type": "condition", "item": cond})

    elif re.search(r"(?:انا|أنا|عندي)\s+(?:مرض\s+)?(?:الضغط|ضغط\s+عالي|ارتفاع\s+ضغط\s+الدم)", text_norm):
        cond = add_patient_condition(user_id, "Hypertension", confirmed=True)
        extracted.append({"type": "condition", "item": cond})

    # 2. Allergy Extraction
    allergy_match = re.search(r"(?:عندي|اعاني من)\s+حساسي[ةه]\s+(?:من|ضد)?\s+([a-zA-Z\u0600-\u06FF\s]+)", text, re.IGNORECASE)
    if allergy_match:
        cand_allergen = allergy_match.group(1).strip()
        is_uncertain = any(w in text_norm for w in ["اعتقد", "أعتقد", "ممكن", "شاكك", "مش متأكد", "maybe", "suspect"])
        if "بنسلين" in cand_allergen or "penicillin" in cand_allergen.lower():
            allergy = add_patient_allergy(user_id, "Penicillin", confirmed=(not is_uncertain))
            extracted.append({"type": "allergy", "item": allergy})

    # 3. Medication Extraction (e.g. "باخد Metformin 500 mg", "باخذ دواء كونكور 5")
    med_match = re.search(r"(?:باخد|باخذ|اتناول|أتناول|مستمر على)\s+(?:دواء|علاج)?\s*([a-zA-Z\u0600-\u06FF0-9\s.]+)", text, re.IGNORECASE)
    if med_match:
        cand_med = med_match.group(1).strip()
        # Parse strength if present
        strength_match = re.search(r"(\d+(?:\.\d+)?\s*(?:mg|gm|mcg|ملجم|جم|مجم))", cand_med, re.IGNORECASE)
        strength = strength_match.group(1) if strength_match else None
        
        # Clean candidate
        cand_clean = re.sub(r"(\d+(?:\.\d+)?\s*(?:mg|gm|mcg|ملجم|جم|مجم))", "", cand_med).strip()
        gen_name, brand_name = normalize_medication_name(cand_clean)
        
        if gen_name and len(gen_name) > 2:
            med = add_patient_medication(user_id, gen_name, brand_name=brand_name, strength=strength, confirmed=True)
            extracted.append({"type": "medication", "item": med})

    return extracted
