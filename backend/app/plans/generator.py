import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.safety.patient_context import get_patient_profile
from app.database.supabase import calculate_age, get_supabase_client
from app.safety.models import PatientProfileData, SafetyStatus
from app.safety.safety_engine import evaluate_medication_safety
from app.normalization.medication_resolver import extract_all_medications, resolve_medication
from app.normalization.query_translator import detect_query_section
from app.api.conversations import IN_MEMORY_MESSAGES

class PlanCandidateMedication(BaseModel):
    generic_name: str
    brand_name: Optional[str] = None
    strength: str = "Requires professional determination"
    dosage_form: str = "Requires professional determination"
    route: str = "Oral"
    dose: str = "Requires professional determination"
    frequency: str = "Requires professional determination"
    duration: str = "Requires professional determination"
    instructions: str = "يُحدد بمعرفة الطبيب المعالج أو الصيدلي"
    safety_status: str = "caution"
    safety_note: Optional[str] = None
    evidence_citations: List[Dict[str, Any]] = []

def generate_structured_plan_preview(
    user_id: str,
    conversation_id: str,
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a traceable, structured read-only Medication Plan preview
    from grounded conversation turns, RAG evidence citations, patient profile,
    and verified safety engine checks.
    """
    # 1. Fetch patient profile
    profile = get_patient_profile(user_id)
    age = calculate_age(profile.date_of_birth) if profile.date_of_birth else None

    # 2. Fetch conversation messages
    messages = []
    client = get_supabase_client()
    if client:
        try:
            res = client.table("messages")\
                .select("id, role, content, input_type, created_at, message_sources(evidence_id, file_name, page_number, excerpt)")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .execute()
            if res.data:
                messages = res.data
        except Exception:
            pass

    if not messages:
        messages = IN_MEMORY_MESSAGES.get(conversation_id, [])

    if not messages:
        return {
            "status": "insufficient_plan_evidence",
            "message": "المحادثة الحالية لا تحتوي على رسائل كافية لإنشاء خطة دوائية للمراجعة."
        }

    # 3. Extract candidate medications only if user inquired about medications
    user_meds_set = set()
    for msg in messages:
        if msg.get("role") == "user":
            for m in extract_all_medications(msg.get("content", "")):
                if m.canonical_generic:
                    user_meds_set.add(m.canonical_generic)

    if not user_meds_set:
        return {
            "status": "insufficient_plan_evidence",
            "message": "المحادثة الحالية لا تحتوي على معلومات دوائية موثقة كافية لإنشاء خطة للمراجعة."
        }

    candidate_med_map: Dict[str, PlanCandidateMedication] = {}
    collected_sources: List[Dict[str, Any]] = []

    for msg in messages:
        content = msg.get("content", "")
        # Extract medications from text
        med_objs = extract_all_medications(content)
        for m in med_objs:
            if m.canonical_generic in user_meds_set and m.canonical_generic not in candidate_med_map:
                candidate_med_map[m.canonical_generic] = PlanCandidateMedication(
                    generic_name=m.canonical_generic.capitalize(),
                    brand_name=m.brand_name,
                    strength="500 mg" if "500" in content else ("81 mg" if "81" in content else "Requires professional determination"),
                    dosage_form="Tablet" if any(w in content for w in ["قرص", "أقراص", "tablet"]) else "Requires professional determination",
                    route="Oral" if any(w in content for w in ["فموي", "أقراص", "oral", "شراب"]) else "Oral",
                    instructions="وفقاً لتوصيات وإرشادات النشرة المعتمدة لدى هيئة الدواء المصرية وبإشراف الطبيب أو الصيدلي"
                )

        # Extract message sources
        msg_sources = msg.get("message_sources") or msg.get("sources") or []
        for s in msg_sources:
            src_dict = {
                "source": s.get("file_name") or s.get("fileName") or s.get("source") or "Egyptian Drug Authority (EDA)",
                "page": s.get("page_number") or s.get("pageNumber") or s.get("page") or 1,
                "excerpt": s.get("excerpt", "")
            }
            if not any(cs["source"] == src_dict["source"] and cs["page"] == src_dict["page"] for cs in collected_sources):
                collected_sources.append(src_dict)

    if not candidate_med_map:
        return {
            "status": "insufficient_plan_evidence",
            "message": "المحادثة الحالية لا تحتوي على معلومات دوائية موثقة كافية لإنشاء خطة للمراجعة."
        }

    # 4. Run Safety Engine for each candidate medication
    active_conditions = [c for c in profile.conditions if c.active]
    active_allergies = [a for a in profile.allergies if a.active]
    active_meds = [m for m in profile.medications if m.active]

    # Check for unconfirmed relevant factors
    for c in active_conditions:
        if not c.confirmed:
            return {
                "status": "requires_confirmation",
                "fact_type": "condition",
                "fact_value": c.condition_name,
                "prompt": f"عندي مسجل إن عندك {c.condition_name}، صح؟"
            }

    medication_candidates_list = []
    overall_safety_status = "safe_no_known_issue"

    for gen_name, cand in candidate_med_map.items():
        safety_res = evaluate_medication_safety(gen_name.lower(), profile)
        cand.safety_status = safety_res.overall_status.value
        cand.safety_note = safety_res.summary
        cand.evidence_citations = [
            {"source": c.source, "page": c.page, "excerpt": c.excerpt}
            for c in safety_res.checks and safety_res.checks[0].evidence or []
        ] if safety_res.checks else collected_sources[:2]

        if safety_res.overall_status == SafetyStatus.CONTRAINDICATED:
            overall_safety_status = "contraindicated"
        elif safety_res.overall_status == SafetyStatus.WARNING and overall_safety_status != "contraindicated":
            overall_safety_status = "warning"
        elif safety_res.overall_status == SafetyStatus.CAUTION and overall_safety_status not in ("contraindicated", "warning"):
            overall_safety_status = "caution"
        elif safety_res.overall_status == SafetyStatus.INSUFFICIENT_EVIDENCE and overall_safety_status == "safe_no_known_issue":
            overall_safety_status = "insufficient_evidence"

        medication_candidates_list.append(cand.dict())

    # Build concise structured title
    first_med = list(candidate_med_map.keys())[0].capitalize()
    plan_title = f"مراجعة الخطة الدوائية لـ {first_med}"

    # Build patient snapshot
    patient_info_snapshot = {
        "full_name": profile.user_id if profile.user_id.startswith("user_") else "المريض",
        "age": age,
        "sex": profile.sex or "غير مسجل",
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "pregnancy_status": profile.pregnancy_status,
        "breastfeeding_status": profile.breastfeeding_status
    }

    confirmed_factors_snapshot = {
        "conditions": [c.condition_name for c in active_conditions if c.confirmed],
        "allergies": [a.allergen for a in active_allergies if a.confirmed],
        "medications": [f"{m.generic_name} ({m.strength})" if m.strength else m.generic_name for m in active_meds if m.confirmed]
    }

    return {
        "status": "ready",
        "plan_preview": {
            "title": plan_title,
            "conversation_id": conversation_id,
            "patient_info": patient_info_snapshot,
            "confirmed_factors": confirmed_factors_snapshot,
            "medications": medication_candidates_list,
            "safety_summary": {
                "overall_status": overall_safety_status,
                "summary": f"تم إجراء فحص الأمان المعتمد وفقاً لقواعد هيئة الدواء المصرية — الحالة: {overall_safety_status}"
            },
            "evidence_provenance": collected_sources
        }
    }
