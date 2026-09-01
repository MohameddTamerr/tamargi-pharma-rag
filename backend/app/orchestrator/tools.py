import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

from app.language.detector import detect_language
from app.language.egyptian import normalize_egyptian_query
from app.language.arabic import normalize_arabic
from app.language.query_expansion import expand_arabic_query
from app.rag.retrieval import retrieve
from app.rag.grounding import build_sources_list
from app.rag.generator import generate_grounded_answer
from app.rag.reranker import rerank_results
from app.safety.models import SafetyResult, SafetyStatus, PatientProfile, ConfirmationContext
from app.safety.patient_context import (
    get_patient_profile,
    resolve_pending_confirmation,
    extract_patient_facts_from_chat
)
from app.safety.safety_engine import evaluate_medication_safety
from app.safety.normalizer import normalize_medication_name
from app.video.video_matcher import get_verified_video
from app.api.plans import create_medication_plan, CreatePlanRequest, MedicationItem

def tool_medication_resolver(query_text: str, extracted_meds: List[str]) -> List[str]:
    """Resolves and normalizes candidate medication names."""
    return [normalize_medication_name(m)[0] for m in extracted_meds]

def tool_patient_profile(user_id: str) -> PatientProfile:
    """Retrieves authenticated patient profile with confirmed and pending factors."""
    return get_patient_profile(user_id)

def tool_safety_engine(
    medication: str,
    patient_profile: PatientProfile,
    query_text: str,
    conversation_id: str,
    retrieved_evidence: Optional[List[Dict[str, Any]]] = None
) -> SafetyResult:
    """Evaluates medication safety against verified rules and patient profile."""
    return evaluate_medication_safety(
        medication=medication,
        patient_profile=patient_profile,
        query_text=query_text,
        conversation_id=conversation_id,
        retrieved_evidence=retrieved_evidence
    )

from app.normalization.medication_resolver import extract_all_medications
from app.normalization.query_translator import build_canonical_retrieval_query

def tool_hybrid_rag(query_text: str, lang: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Any], str]:
    """
    Executes Hybrid RAG: language normalization -> expansion -> canonical English entity translation -> retrieval -> grounded answer.
    """
    if not lang:
        lang = detect_language(query_text)

    if lang == "egyptian":
        retrieval_query = normalize_egyptian_query(query_text)
    elif lang == "ar":
        retrieval_query = normalize_arabic(query_text)
    else:
        retrieval_query = query_text

    meds = extract_all_medications(query_text)
    med_names = [m.canonical_generic for m in meds if m.canonical_generic]

    if lang in ("ar", "egyptian"):
        retrieval_query = expand_arabic_query(retrieval_query)
        canonical_terms = build_canonical_retrieval_query(query_text, "general", meds)
        retrieval_query = f"{retrieval_query} {canonical_terms}".strip()

    results = retrieve(retrieval_query, target_medications=med_names)
    sources = build_sources_list(results)
    answer = generate_grounded_answer(query_text, results, user_language=lang)

    return results, sources, answer

def tool_drug_comparison_retrieval(
    med_a: str,
    med_b: str,
    query_text: str,
    lang: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Any], str]:
    """
    Executes separate dual retrieval for Drug A and Drug B, merges candidate pools,
    reranks the combined set, and generates a grounded comparative answer.
    """
    if not lang:
        lang = detect_language(query_text)

    # 1. Retrieve for Drug A
    results_a = retrieve(f"{med_a} indications dosage adverse reactions contraindications")
    # 2. Retrieve for Drug B
    results_b = retrieve(f"{med_b} indications dosage adverse reactions contraindications")

    # 3. Merge candidate chunks (deduplicating by chunk text/id)
    seen_keys = set()
    merged_candidates: List[Dict[str, Any]] = []
    for r in results_a + results_b:
        chunk_key = (r.get("file", ""), r.get("page", 0), r.get("chunk_id", 0))
        if chunk_key not in seen_keys:
            seen_keys.add(chunk_key)
            merged_candidates.append(r)

    # 4. Rerank combined pool against user comparison query
    reranked = rerank_results(query_text, merged_candidates, top_k=6)
    sources = build_sources_list(reranked)

    # 5. Generate comparative grounded answer
    answer = generate_grounded_answer(query_text, reranked, user_language=lang)

    return reranked, sources, answer

def tool_verified_video(query_text: str) -> Dict[str, Any]:
    """Retrieves verified Arabic instructional video for exact device."""
    return get_verified_video(query_text=query_text)

def tool_confirmation_handler(user_id: str, conversation_id: str, query_text: str):
    """Resolves pending medical confirmation from user response."""
    return resolve_pending_confirmation(user_id, conversation_id, query_text)

def tool_medication_plan_generator(
    user_id: str,
    medications: List[str],
    patient_profile: PatientProfile,
    safety_evaluations: List[SafetyResult],
    evidence_chunks: List[Dict[str, Any]],
    plan_title: str = "خطة دوائية للمراجعة الطبية"
) -> Dict[str, Any]:
    """
    Constructs and persists a Draft Medication Plan for professional review with secure QR token.
    Ensures missing doses are marked as 'Requires professional determination'.
    """
    # Check if any medication is contraindicated
    has_contraindication = any(
        s.overall_status == SafetyStatus.CONTRAINDICATED for s in safety_evaluations
    )

    rx_items: List[MedicationItem] = []
    for med in medications:
        # Find matching safety eval if available
        med_safety = next((s for s in safety_evaluations if getattr(s, 'medication', None) and s.medication.lower() == med.lower()), None)
        if not med_safety and safety_evaluations:
            med_safety = safety_evaluations[0]
        status_str = med_safety.overall_status.value if med_safety else "caution"
        note_str = med_safety.summary if med_safety else "تتطلب مراجعة وتحديد الجرعة من الصيدلي"

        rx_items.append(MedicationItem(
            generic_name=med,
            brand_name="حسب الوصفة",
            strength="Requires professional determination",
            dosage_form="Requires professional determination",
            route="Oral",
            dose="Requires professional determination",
            frequency="Requires professional determination",
            duration="Requires professional determination",
            instructions="يُحدد بمعرفة الطبيب المعالج أو الصيدلي",
            safety_status=status_str,
            safety_note=note_str
        ))

    confirmed_conds = [c.condition_name for c in patient_profile.conditions if c.confirmed]
    confirmed_allgs = [a.allergen for a in patient_profile.allergies if a.confirmed]
    confirmed_meds = [m.medication_name for m in patient_profile.medications if m.confirmed]

    evidence_prov = []
    for ch in evidence_chunks[:4]:
        evidence_prov.append({
            "source": ch.get("file", "egypt_formulary.pdf"),
            "page": ch.get("page", 1),
            "section": "Clinical Monograph",
            "excerpt": ch.get("text", "")[:200]
        })

    create_req = CreatePlanRequest(
        user_id=user_id,
        title=plan_title,
        patient_info={
            "full_name": "المريض",
            "sex": patient_profile.sex,
            "weight_kg": patient_profile.weight_kg,
            "height_cm": patient_profile.height_cm,
        },
        confirmed_factors={
            "conditions": confirmed_conds,
            "allergies": confirmed_allgs,
            "medications": confirmed_meds
        },
        medications=rx_items,
        safety_summary={
            "overall_status": "contraindicated" if has_contraindication else "caution",
            "summary_text": "خطة دوائية استرشادية تم إعدادها للمراجعة والتقييم الصيدلي.",
            "checks_count": len(safety_evaluations)
        },
        evidence_provenance=evidence_prov,
        notes="تم توليد هذه الخطة عبر Tamargi.ai لمراجعة الصيدلي."
    )

    plan_result = create_medication_plan(create_req)
    return plan_result
