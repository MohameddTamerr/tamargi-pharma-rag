from typing import List, Optional, Dict, Any
from .models import (
    SafetyStatus,
    SafetyCheckItem,
    EvidenceCitation,
    XAIExplanation,
    SafetyResult,
    ConfirmationContext,
    PatientProfileData,
    PatientCondition,
    PatientAllergy,
    PatientMedication
)
from .normalizer import (
    normalize_medication_name,
    normalize_condition_name,
    normalize_allergen_name,
    normalize_text
)
from .patient_context import create_pending_confirmation
from .allergy_checker import check_allergy
from .drug_disease_checker import check_drug_disease, get_relevant_conditions_for_medication
from .drug_drug_checker import check_drug_drug, get_relevant_medications_for_interaction
from .high_alert_checker import check_high_alert
from .do_not_crush_checker import check_do_not_crush
from .repository import get_verified_rules

AR_CONDITION_NAMES = {
    "diabetes_mellitus": "مرض السكر",
    "hypertension": "ارتفاع ضغط الدم",
    "chronic_kidney_disease": "مشاكل أو قصور في الكلى",
    "asthma": "حساسية الصدر / الربو",
    "peptic_ulcer_disease": "قرحة في المعدة",
    "hepatic_impairment": "مشاكل في الكبد",
    "heart_failure": "ضعف عضلة القلب"
}

def evaluate_medication_safety(
    medication: str,
    patient_profile: PatientProfileData,
    query_text: str = "",
    conversation_id: str = "default_conv",
    retrieved_evidence: Optional[List[Dict[str, Any]]] = None
) -> SafetyResult:
    """
    Two-Stage Deterministic Safety Engine:
    - Stage A: Fast deterministic matching against verified_safety_rules.
    - Stage B: RAG retrieved evidence context (informational only; never automatically manufactures contraindications).
    
    Absence of a rule defaults to `insufficient_evidence`, NOT `safe_no_known_issue`.
    """
    if not medication:
        return SafetyResult(
            overall_status=SafetyStatus.INSUFFICIENT_EVIDENCE,
            summary="لم يتم تحديد اسم دواء للتحقق من أمانه الطبي."
        )

    req_gen, brand_name = normalize_medication_name(medication)

    # -------------------------------------------------------------
    # Step 1: Identify Relevant Stored Patient Facts from Verified Rules
    # -------------------------------------------------------------
    rel_conditions = get_relevant_conditions_for_medication(req_gen)
    rel_meds = get_relevant_medications_for_interaction(req_gen)

    # Check for relevant unconfirmed conditions
    for cond in patient_profile.conditions:
        if not cond.active:
            continue
        norm_c = cond.normalized_condition or normalize_condition_name(cond.condition_name)
        if norm_c in rel_conditions:
            if not cond.confirmed:
                ar_label = AR_CONDITION_NAMES.get(norm_c, cond.condition_name)
                prompt = f"عندي مسجل إن عندك {ar_label}، هل ده لسه صحيح؟"
                pending = create_pending_confirmation(
                    user_id=patient_profile.user_id,
                    conversation_id=conversation_id,
                    fact_type="condition",
                    fact_id=cond.id,
                    normalized_value=norm_c,
                    original_question=query_text,
                    medication_context=medication
                )
                return SafetyResult(
                    overall_status=SafetyStatus.REQUIRES_CONFIRMATION,
                    summary="يوجد ظرف صحي مسجل بملفك الطبي يرتبط بأمان هذا الدواء ويتطلب تأكيدك أولاً.",
                    requires_confirmation=True,
                    confirmation=ConfirmationContext(
                        fact_type="condition",
                        fact_id=cond.id,
                        value=cond.condition_name,
                        normalized_value=norm_c,
                        prompt=prompt
                    )
                )

    # Check for relevant unconfirmed allergies
    for allergy in patient_profile.allergies:
        if not allergy.active:
            continue
        can_a, a_class = normalize_allergen_name(allergy.allergen)
        allergy_rules = get_verified_rules(rule_type="allergy", drug_a=req_gen)
        is_rel = (can_a == req_gen) or any(can_a in (r.allergen_class or "").lower() for r in allergy_rules)
        if is_rel and not allergy.confirmed:
            prompt = f"عندي مسجل إن عندك حساسية من {allergy.allergen}، هل ده لسه صحيح؟"
            pending = create_pending_confirmation(
                user_id=patient_profile.user_id,
                conversation_id=conversation_id,
                fact_type="allergy",
                fact_id=allergy.id,
                normalized_value=can_a,
                original_question=query_text,
                medication_context=medication
            )
            return SafetyResult(
                overall_status=SafetyStatus.REQUIRES_CONFIRMATION,
                summary="توجد حساسية دوائية مسجلة بملفك ترتبط بهذا الدواء وتتطلب تأكيدك أولاً.",
                requires_confirmation=True,
                confirmation=ConfirmationContext(
                    fact_type="allergy",
                    fact_id=allergy.id,
                    value=allergy.allergen,
                    normalized_value=can_a,
                    prompt=prompt
                )
            )

    # -------------------------------------------------------------
    # Stage A: Run Deterministic Safety Checkers on Verified Knowledge Store
    # -------------------------------------------------------------
    all_checks: List[SafetyCheckItem] = []

    # 1. Allergy check (Only active & confirmed)
    confirmed_allergies = [a for a in patient_profile.allergies if a.active and a.confirmed]
    all_checks.extend(check_allergy(medication, confirmed_allergies))

    # 2. Drug-Disease check (Only active & confirmed)
    confirmed_conditions = [c for c in patient_profile.conditions if c.active and c.confirmed]
    all_checks.extend(check_drug_disease(medication, confirmed_conditions))

    # 3. Drug-Drug check (Only active & confirmed)
    confirmed_meds = [m for m in patient_profile.medications if m.active and m.confirmed]
    all_checks.extend(check_drug_drug(medication, confirmed_meds))

    # 4. High-Alert check
    high_alert_res = check_high_alert(medication)
    if high_alert_res:
        all_checks.append(high_alert_res)

    # 5. Do-Not-Crush check
    dnc_res = check_do_not_crush(query_text, medication)
    if dnc_res:
        all_checks.append(dnc_res)

    # -------------------------------------------------------------
    # Stage B: Evidence Assessment & Overall Status Computation
    # -------------------------------------------------------------
    # Absence of rule != Safe. If no clinical finding triggered, check if verified safe rule exists
    overall_status = SafetyStatus.INSUFFICIENT_EVIDENCE
    summary_text = "لم تتوفر أدلة كافية في المصادر المعتمدة لإصدار حكم أمان شخصي."

    if all_checks:
        has_contraindicated = any(c.status == SafetyStatus.CONTRAINDICATED for c in all_checks)
        has_warning = any(c.status == SafetyStatus.WARNING for c in all_checks)
        has_caution = any(c.status == SafetyStatus.CAUTION for c in all_checks)

        if has_contraindicated:
            overall_status = SafetyStatus.CONTRAINDICATED
            summary_text = "تحذير أمان عالي: هذا الدواء موصوف بعدم الاستخدام (ممنوع) بناءً على الأدلة الموثقة في هيئة الدواء المصرية."
        elif has_warning:
            overall_status = SafetyStatus.WARNING
            summary_text = "تنبيه أمان: يوجد تحذير طبي موثق بخصوص استخدام هذا الدواء مع حالتك الصحية أو أدويتك الحالية."
        elif has_caution:
            overall_status = SafetyStatus.CAUTION
            summary_text = "ملاحظة أمان: يتطلب هذا الدواء حذراً ومتابعة خاصة وفقاً للأدلة المعتمدة."
    else:
        # Check if an explicit verified rule declares this medication safe for the patient factors
        safe_rules = get_verified_rules(drug_a=req_gen)
        if any(r.status == SafetyStatus.SAFE_NO_KNOWN_ISSUE for r in safe_rules):
            overall_status = SafetyStatus.SAFE_NO_KNOWN_ISSUE
            summary_text = "بناءً على الأدلة المعتمدة، لم يتم رصد أي موانع استخدام أو تداخلات دوائية مع بياناتك المسجلة."

    # -------------------------------------------------------------
    # Build Structured Explainable AI (XAI) Object
    # -------------------------------------------------------------
    because_reasons: List[str] = []
    patient_factors_used: List[str] = []
    evidence_used: List[EvidenceCitation] = []

    for chk in all_checks:
        because_reasons.append(f"{chk.patient_factor}: {chk.reason}")
        if chk.patient_factor and chk.patient_factor not in patient_factors_used:
            patient_factors_used.append(chk.patient_factor)
        for ev in chk.evidence:
            if not any(e.rule_id == ev.rule_id and e.source == ev.source and e.page == ev.page for e in evidence_used):
                evidence_used.append(ev)

    if not because_reasons:
        if overall_status == SafetyStatus.SAFE_NO_KNOWN_ISSUE:
            because_reasons = ["تم فحص الأدلة المعتمدة والتأكد من خلو الدواء من الموانع المسجلة مع حالتك."]
        else:
            because_reasons = ["لم تتوفر قاعدة أمان دوائية موثقة في الدليل الطبي للبت في هذا الاستفسار بشكل قاطع."]

    xai_obj = XAIExplanation(
        decision=overall_status,
        summary=summary_text,
        because=because_reasons,
        patient_factors_used=patient_factors_used,
        evidence_used=evidence_used
    )

    return SafetyResult(
        medication=medication,
        overall_status=overall_status,
        summary=summary_text,
        checks=all_checks,
        requires_confirmation=False,
        confirmation=None,
        xai=xai_obj
    )
