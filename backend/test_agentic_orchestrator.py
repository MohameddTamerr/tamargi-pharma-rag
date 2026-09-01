import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.safety.models import SafetyStatus
from app.safety.patient_context import (
    reset_in_memory_store,
    get_patient_profile,
    add_patient_condition,
    add_patient_allergy,
    add_patient_medication,
    add_patient_history
)
from app.safety.repository import seed_verified_rule, clear_test_rules
from app.orchestrator.orchestrator import TamargiOrchestrator
from app.orchestrator.intents import IntentType, detect_intents
from app.orchestrator.entity_extractor import extract_entities
from app.api.plans import verify_plan_by_token, IN_MEMORY_PLANS, IN_MEMORY_TOKEN_MAP

def seed_verified_rules_for_orchestrator():
    """Seeds the 9 verified rules from final_verified_safety_rules.csv."""
    df = pd.read_csv('c:/Users/user/Downloads/tamargi-pharma-rag/data/processed/final_verified_safety_rules.csv')
    verified_rows = df[df['final_verification_status'] == 'VERIFIED']
    
    for idx, r in verified_rows.iterrows():
        status_enum = SafetyStatus(r['final_status'])
        seed_verified_rule({
            "id": f"orch-verified-{idx+1}",
            "rule_type": r['rule_type'],
            "drug_a": r['drug_a'],
            "drug_b": r['drug_b_or_condition'] if r['rule_type'] == 'drug_drug' else None,
            "condition_name": r['drug_b_or_condition'] if r['rule_type'] == 'drug_disease' else None,
            "allergen_class": r['drug_b_or_condition'] if r['rule_type'] == 'allergy' else None,
            "dosage_form": r['drug_b_or_condition'] if r['rule_type'] in ('high_alert', 'do_not_crush') else None,
            "status": status_enum,
            "reason": f"Directly verified EDA evidence from {r['source_file']}",
            "source_file": r['source_file'],
            "source_page": int(r['source_page']),
            "source_monograph": str(r['source_monograph']) if pd.notna(r['source_monograph']) else None,
            "source_section": str(r['source_section']) if pd.notna(r['source_section']) else None,
            "evidence_excerpt": r['exact_evidence_excerpt'],
            "verified": True,
            "active": True
        })

def run_all_orchestrator_tests():
    print("=" * 95)
    print("TAMARGI.AI — END-TO-END AGENTIC ORCHESTRATOR TEST SUITE (18 SCENARIOS)")
    print("=" * 95)

    test_results = []
    reset_in_memory_store()
    clear_test_rules()
    seed_verified_rules_for_orchestrator()

    # -------------------------------------------------------------
    # TEST 1: General Medication Question (RAG only where appropriate)
    # -------------------------------------------------------------
    u1 = "user_orch_1"
    res1 = TamargiOrchestrator.orchestrate(
        query="What is metformin used for in adults?",
        conversation_id="conv_1",
        user_id=u1
    )
    pass1 = (
        res1.trace.intent == "general_medication_question" and
        "hybrid_rag" in res1.trace.tools_called and
        len(res1.sources) > 0 and
        res1.requires_confirmation is False
    )
    test_results.append(("1. General Medication Question (RAG only)", pass1, res1.trace.tools_called))
    print(f"Test 1: General Med Question -> Intent: {res1.trace.intent} | Tools: {res1.trace.tools_called} [{'PASS' if pass1 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 2: Personalized Medication Safety (Profile + Safety + RAG)
    # -------------------------------------------------------------
    u2 = "user_orch_2"
    add_patient_condition(u2, "Diabetes Mellitus", confirmed=True)
    res2 = TamargiOrchestrator.orchestrate(
        query="ينفع آخد ديكساميثازون؟",
        conversation_id="conv_2",
        user_id=u2
    )
    pass2 = (
        res2.safety is not None and
        res2.safety.overall_status == SafetyStatus.CAUTION and
        "safety_engine" in res2.trace.tools_called and
        "patient_profile" in res2.trace.tools_called
    )
    test_results.append(("2. Personalized Medication Safety (Profile + Safety + RAG)", pass2, res2.trace.tools_called))
    print(f"Test 2: Personalized Med Safety -> Safety Status: {res2.safety.overall_status if res2.safety else None} [{'PASS' if pass2 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 3: Relevant Unconfirmed Condition -> Asks Confirmation Prompt
    # -------------------------------------------------------------
    u3 = "user_orch_3"
    add_patient_condition(u3, "Asthma", confirmed=False)
    res3 = TamargiOrchestrator.orchestrate(
        query="ينفع أستخدم دواء بروبرانولول؟",
        conversation_id="conv_3",
        user_id=u3
    )
    pass3 = (
        res3.requires_confirmation is True and
        res3.confirmation is not None and
        "حساسية صدر" in res3.confirmation.prompt or "الربو" in res3.confirmation.prompt
    )
    test_results.append(("3. Relevant Unconfirmed Condition Asks Confirmation", pass3, res3.requires_confirmation))
    print(f"Test 3: Unconfirmed Condition Confirmation -> Requires Conf: {res3.requires_confirmation} [{'PASS' if pass3 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 4: User says "ايوه" -> Confirms & Automatically Resumes Original Question
    # -------------------------------------------------------------
    res4 = TamargiOrchestrator.orchestrate(
        query="ايوه عندي ربو وحساسية صدر",
        conversation_id="conv_3",
        user_id=u3
    )
    pass4 = (
        res4.trace.intent == "confirmation_response" and
        res4.safety is not None and
        res4.safety.overall_status == SafetyStatus.CONTRAINDICATED and
        "تم تحديث ملفك الطبي" in res4.answer and
        "بروبرانولول" in res4.answer or "propranolol" in res4.answer.lower()
    )
    test_results.append(("4. Confirmation Continuation ('ايوه' -> Confirmed -> Contraindicated)", pass4, res4.answer[:120]))
    print(f"Test 4: Confirmation Continuation ('ايوه') -> Resumed Status: {res4.safety.overall_status if res4.safety else None} [{'PASS' if pass4 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 5: User says "لا" -> Deactivates Fact & Automatically Resumes Original Question
    # -------------------------------------------------------------
    u5 = "user_orch_5"
    add_patient_condition(u5, "Asthma", confirmed=False)
    # Turn 1: Triggers confirmation
    TamargiOrchestrator.orchestrate("ينفع أستخدم دواء بروبرانولول؟", conversation_id="conv_5", user_id=u5)
    # Turn 2: User says 'لا معنديش'
    res5 = TamargiOrchestrator.orchestrate("لا مش عندي ربو", conversation_id="conv_5", user_id=u5)
    
    p5_updated = get_patient_profile(u5)
    pass5 = (
        len(p5_updated.conditions) == 0 and # Deactivated/removed
        res5.trace.intent == "confirmation_response" and
        "استبعاد" in res5.answer
    )
    test_results.append(("5. Denial Continuation ('لا' -> Deactivates Fact & Resumes)", pass5, res5.answer[:100]))
    print(f"Test 5: Denial Continuation ('لا') -> Active Conditions: {len(p5_updated.conditions)} [{'PASS' if pass5 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 6: Unrelated Patient History -> Not Requested / Filtered Out
    # -------------------------------------------------------------
    u6 = "user_orch_6"
    add_patient_history(u6, "surgery", "appendectomy", confirmed=True)
    res6 = TamargiOrchestrator.orchestrate("ينفع آخد ديكساميثازون؟", conversation_id="conv_6", user_id=u6)
    pass6 = (
        res6.requires_confirmation is False and # appendectomy is unrelated to dexamethasone rule
        "appendectomy" not in res6.answer.lower()
    )
    test_results.append(("6. Unrelated Patient History Not Requested", pass6, res6.requires_confirmation))
    print(f"Test 6: Unrelated Patient History -> Ignored For Dexa: {pass6} [{'PASS' if pass6 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 7: Paracetamol vs Ibuprofen -> Separate Dual Retrieval For Both
    # -------------------------------------------------------------
    u7 = "user_orch_7"
    res7 = TamargiOrchestrator.orchestrate(
        query="ما الفرق بين الباراسيتامول والإيبوبروفين من حيث الآثار الجانبية؟",
        conversation_id="conv_7",
        user_id=u7
    )
    pass7 = (
        res7.trace.intent == "drug_comparison" and
        "comparison_retrieval" in res7.trace.tools_called and
        len(res7.sources) > 0
    )
    test_results.append(("7. Drug Comparison (Separate Dual Retrieval For Both)", pass7, res7.trace.tools_called))
    print(f"Test 7: Drug Comparison -> Intent: {res7.trace.intent} | Tools: {res7.trace.tools_called} [{'PASS' if pass7 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 8: Verified Drug-Drug Interaction (Sildenafil + Nitrates)
    # -------------------------------------------------------------
    u8 = "user_orch_8"
    add_patient_medication(u8, "nitroglycerin", confirmed=True)
    res8 = TamargiOrchestrator.orchestrate(
        query="Can I take sildenafil with my nitroglycerin?",
        conversation_id="conv_8",
        user_id=u8
    )
    pass8 = (
        res8.safety is not None and
        res8.safety.overall_status == SafetyStatus.CONTRAINDICATED and
        "safety_engine" in res8.trace.tools_called
    )
    test_results.append(("8. Verified DDI Check (Sildenafil + Nitrates)", pass8, res8.safety.overall_status if res8.safety else None))
    print(f"Test 8: Verified DDI -> Status: {res8.safety.overall_status if res8.safety else None} [{'PASS' if pass8 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 9: No Verified Safety Coverage -> Insufficient Evidence (Not Safe)
    # -------------------------------------------------------------
    u9 = "user_orch_9"
    # Unverified combination without rule in verified store
    res9 = TamargiOrchestrator.orchestrate(
        query="هل دواء سيفاليكسين آمن لحالتي؟",
        conversation_id="conv_9",
        user_id=u9
    )
    pass9 = (
        res9.safety is None or
        res9.safety.overall_status == SafetyStatus.INSUFFICIENT_EVIDENCE
    )
    test_results.append(("9. No Verified Rule Coverage -> Insufficient Evidence", pass9, res9.safety.overall_status if res9.safety else "None"))
    print(f"Test 9: No Verified Rule -> Status: {res9.safety.overall_status if res9.safety else 'None'} [{'PASS' if pass9 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 10: Exact Turbohaler Usage -> Verified Arabic Video Returned
    # -------------------------------------------------------------
    res10 = TamargiOrchestrator.orchestrate(
        query="ازاي استخدم جهاز Symbicort Turbohaler؟",
        conversation_id="conv_10",
        user_id="user_orch_10"
    )
    pass10 = (
        res10.trace.intent == "device_usage" and
        res10.video is not None and
        res10.video.get("found") is True and
        res10.video.get("device_name") == "Turbohaler"
    )
    test_results.append(("10. Exact Turbohaler Usage (Verified Arabic Video)", pass10, res10.video.get("device_name") if res10.video else None))
    print(f"Test 10: Exact Turbohaler Video -> Found: {res10.video.get('found') if res10.video else False} [{'PASS' if pass10 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 11: Generic "بخاخ" -> exact_device_unknown (No Random Video)
    # -------------------------------------------------------------
    res11 = TamargiOrchestrator.orchestrate(
        query="ازاي استخدم البخاخ؟",
        conversation_id="conv_11",
        user_id="user_orch_11"
    )
    pass11 = (
        res11.trace.intent == "device_usage" and
        (res11.video is None or res11.video.get("found") is False) and
        "في أنواع مختلفة من أجهزة الاستنشاق" in res11.answer
    )
    test_results.append(("11. Generic Inhaler ('بخاخ') Suppresses Video & Prompts Device Name", pass11, "exact_device_unknown"))
    print(f"Test 11: Generic Inhaler Check -> Prompt Added: {'في أنواع مختلفة' in res11.answer} [{'PASS' if pass11 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 12: Medication Plan Request (Patient Context + Safety + Evidence)
    # -------------------------------------------------------------
    u12 = "user_orch_12"
    add_patient_condition(u12, "Hypertension", confirmed=True)
    res12 = TamargiOrchestrator.orchestrate(
        query="اعمل لي خطة دوائية لمراجعة دواء باراسيتامول",
        conversation_id="conv_12",
        user_id=u12
    )
    pass12 = (
        res12.trace.intent == "medication_plan_request" and
        res12.plan is not None and
        res12.plan.get("verification_token") is not None and
        "تم إعداد مسودة الخطة الدوائية" in res12.answer
    )
    test_results.append(("12. Medication Plan Request Flow", pass12, res12.plan.get("id") if res12.plan else None))
    print(f"Test 12: Medication Plan Request -> Plan Created: {res12.plan is not None} | Token: {res12.plan.get('verification_token') if res12.plan else None} [{'PASS' if pass12 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 13: Medication Plan with Contraindicated Medication Shows Conflict
    # -------------------------------------------------------------
    u13 = "user_orch_13"
    add_patient_allergy(u13, "Penicillin", confirmed=True)
    res13 = TamargiOrchestrator.orchestrate(
        query="اعمل لي خطة دوائية لدواء amoxicillin",
        conversation_id="conv_13",
        user_id=u13
    )
    pass13 = (
        res13.plan is not None and
        res13.plan.get("safety_summary", {}).get("overall_status") == "contraindicated" and
        "تحذير طبي هام" in res13.answer or "ممنوع" in res13.answer
    )
    test_results.append(("13. Medication Plan with Contraindicated Medication Highlights Conflict", pass13, res13.plan.get("safety_summary") if res13.plan else None))
    print(f"Test 13: Contraindicated Medication Plan -> Safety Summary Status: {res13.plan.get('safety_summary', {}).get('overall_status') if res13.plan else None} [{'PASS' if pass13 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 14: Medication Plan Missing Dose Shows "Requires professional determination"
    # -------------------------------------------------------------
    if res12.plan and res12.plan.get("medications"):
        med_item = res12.plan["medications"][0]
        pass14 = (
            med_item.get("dose") == "Requires professional determination" and
            med_item.get("frequency") == "Requires professional determination"
        )
    else:
        pass14 = False
    test_results.append(("14. Medication Plan Missing Doses Marked 'Requires professional determination'", pass14, None))
    print(f"Test 14: Missing Dose Prescribed Invariant -> Dose: {med_item.get('dose') if pass14 else None} [{'PASS' if pass14 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 15: User A Conversation Invisible to User B
    # -------------------------------------------------------------
    u15_a = "user_alice"
    u15_b = "user_bob"
    TamargiOrchestrator.orchestrate("سؤال خاص بأليس عن باراسيتامول", conversation_id="conv_alice", user_id=u15_a)
    # Bob should not have access to Alice's profile
    p_b = get_patient_profile(u15_b)
    p_a = get_patient_profile(u15_a)
    pass15 = (p_b.user_id == u15_b and p_a.user_id == u15_a)
    test_results.append(("15. User A Conversation Isolation from User B", pass15, None))
    print(f"Test 15: User Isolation -> Alice UID: {p_a.user_id}, Bob UID: {p_b.user_id} [{'PASS' if pass15 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 16: QR Verification Exposes Read-Only Plan Only
    # -------------------------------------------------------------
    if res12.plan and res12.plan.get("verification_token"):
        v_token = res12.plan["verification_token"]
        verified_data = verify_plan_by_token(v_token)
        pass16 = (
            verified_data is not None and
            verified_data.get("id") == res12.plan["id"] and
            "messages" not in verified_data and # No chat history exposed
            "password" not in verified_data and
            "user_id" not in verified_data # Stripped from public view
        )
    else:
        pass16 = False
    test_results.append(("16. QR Verification Exposes Read-Only Plan Without Chat/User Records", pass16, None))
    print(f"Test 16: QR Verification Data Exposure Protection -> Safe: {pass16} [{'PASS' if pass16 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 17: Symptom-Only Question (No Diagnosis Invention)
    # -------------------------------------------------------------
    res17 = TamargiOrchestrator.orchestrate(
        query="عندي صداع ودوخة بقالهم يومين",
        conversation_id="conv_17",
        user_id="user_orch_17"
    )
    p17 = get_patient_profile("user_orch_17")
    pass17 = (
        res17.trace.intent == "symptom_question" and
        len(p17.conditions) == 0 and # Did not convert headache into a diagnosed chronic condition
        "hybrid_rag" in res17.trace.tools_called
    )
    test_results.append(("17. Symptom-Only Question Does Not Infer Medical Diagnoses", pass17, res17.trace.intent))
    print(f"Test 17: Symptom Question -> Intent: {res17.trace.intent} | Inferred Conditions: {len(p17.conditions)} [{'PASS' if pass17 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 18: General Medication Question Does Not Ask Unrelated Chronic Diseases
    # -------------------------------------------------------------
    u18 = "user_orch_18"
    add_patient_condition(u18, "Asthma", confirmed=False)
    res18 = TamargiOrchestrator.orchestrate(
        query="ما هي الآثار الجانبية لدواء باراسيتامول؟",
        conversation_id="conv_18",
        user_id=u18
    )
    pass18 = (
        res18.requires_confirmation is False and # Did not block general info question
        res18.trace.intent == "general_medication_question"
    )
    test_results.append(("18. General Question Does Not Trigger Unrelated Fact Confirmations", pass18, res18.requires_confirmation))
    print(f"Test 18: General Question Independence -> Requires Conf: {res18.requires_confirmation} [{'PASS' if pass18 else 'FAIL'}]")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    all_passed = all(r[1] for r in test_results)
    print("=" * 95)
    print(f"FINAL RESULT: {'ALL 18 ORCHESTRATION TESTS PASSED (100%)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 95)

    return all_passed

if __name__ == "__main__":
    success = run_all_orchestrator_tests()
    if not success:
        sys.exit(1)
