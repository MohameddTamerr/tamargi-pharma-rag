import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.safety.models import SafetyStatus, ConfirmationStatus
from app.safety.patient_context import (
    reset_in_memory_store,
    get_patient_profile,
    add_patient_condition,
    add_patient_allergy,
    add_patient_medication,
    add_patient_history,
    resolve_pending_confirmation,
    extract_patient_facts_from_chat,
    IN_MEMORY_CONDITIONS
)
from app.safety.repository import (
    seed_verified_rule,
    clear_test_rules,
    get_verified_rules,
    is_valid_verified_rule
)
from app.safety.safety_engine import evaluate_medication_safety
from app.safety.high_alert_checker import check_high_alert
from app.safety.do_not_crush_checker import check_do_not_crush
from app.video.video_matcher import get_verified_video
from app.config import SAFETY_RULES_FILE, PROCESSED_DIR

def seed_verified_rules_from_final_audit():
    """Loads and seeds ONLY final_verification_status == 'VERIFIED' records from final_verified_safety_rules.csv."""
    rules_path = SAFETY_RULES_FILE if SAFETY_RULES_FILE.exists() else (PROCESSED_DIR / 'final_verified_safety_rules.csv')
    df = pd.read_csv(rules_path)
    verified_rows = df[df['final_verification_status'] == 'VERIFIED']
    
    count = 0
    for idx, r in verified_rows.iterrows():
        status_enum = SafetyStatus(r['final_status'])
        seed_verified_rule({
            "id": f"final-verified-{idx+1}",
            "rule_type": r['rule_type'],
            "drug_a": r['drug_a'],
            "drug_b": r['drug_b_or_condition'] if r['rule_type'] == 'drug_drug' else None,
            "condition_name": r['drug_b_or_condition'] if r['rule_type'] == 'drug_disease' else None,
            "allergen_class": r['drug_b_or_condition'] if r['rule_type'] == 'allergy' else None,
            "dosage_form": r['drug_b_or_condition'] if r['rule_type'] in ('high_alert', 'do_not_crush') else None,
            "status": status_enum,
            "reason": f"Directly verified EDA monograph evidence from {r['source_file']}",
            "source_file": r['source_file'],
            "source_page": int(r['source_page']),
            "source_monograph": str(r['source_monograph']) if pd.notna(r['source_monograph']) else None,
            "source_section": str(r['source_section']) if pd.notna(r['source_section']) else None,
            "evidence_excerpt": r['exact_evidence_excerpt'],
            "verified": True,
            "active": True
        })
        count += 1
    return count

def run_all_tests():
    print("=" * 95)
    print("TAMARGI.AI — FINAL EVIDENCE INTEGRITY & SAFETY ENGINE COMPREHENSIVE TEST SUITE")
    print("=" * 95)

    test_results = []
    reset_in_memory_store()
    clear_test_rules()

    # Load and audit final_verified_safety_rules.csv
    rules_path = SAFETY_RULES_FILE if SAFETY_RULES_FILE.exists() else (PROCESSED_DIR / 'final_verified_safety_rules.csv')
    df_audit = pd.read_csv(rules_path)
    
    # -------------------------------------------------------------
    # TEST 1: Evidence Integrity Audit Integrity (All 5 direct_* checks must be True for VERIFIED)
    # -------------------------------------------------------------
    verified_rows = df_audit[df_audit['final_verification_status'] == 'VERIFIED']
    all_5_direct_pass = True
    for _, r in verified_rows.iterrows():
        if not (r['direct_drug_a_support'] and r['direct_factor_support'] and 
                r['direct_relationship_support'] and r['direct_status_support'] and 
                r['direct_scope_support']):
            all_5_direct_pass = False
            break
    
    pass1 = (len(verified_rows) == 9 and all_5_direct_pass is True)
    test_results.append(("1. Evidence Integrity Audit (All 5 direct_* checks True for 9 VERIFIED rules)", pass1, len(verified_rows)))
    print(f"Test 1: Final Audit -> Surviving VERIFIED: {len(verified_rows)} | 5-Direct Checks: {all_5_direct_pass} [{'PASS' if pass1 else 'FAIL'}]")

    # Seed verified rules (9 rules)
    seeded_count = seed_verified_rules_from_final_audit()
    print(f"Seeded {seeded_count} VERIFIED rules with source_monograph into repository.\n")

    # -------------------------------------------------------------
    # TEST 2: Monograph Provenance Check (Monograph field populated for drug-specific rules)
    # -------------------------------------------------------------
    active_rules = get_verified_rules()
    monograph_checked = all(
        r.source_monograph is not None and len(r.source_monograph.strip()) > 0
        for r in active_rules if r.rule_type in ('drug_disease', 'drug_drug', 'allergy')
    )
    pass2 = (len(active_rules) == 9 and monograph_checked is True)
    test_results.append(("2. Source Monograph Provenance (source_monograph non-empty)", pass2, active_rules))
    print(f"Test 2: Monograph Provenance -> Active Count: {len(active_rules)} | Monograph Provenance Valid: {monograph_checked} [{'PASS' if pass2 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 3: VERIFIED Allergy Rule (Amoxicillin + Penicillins P.371)
    # -------------------------------------------------------------
    u3 = "user_3"
    add_patient_allergy(u3, "Penicillin", confirmed=True)
    p3 = get_patient_profile(u3)
    res3 = evaluate_medication_safety(medication="amoxicillin", patient_profile=p3, query_text="Can I take amoxicillin?")
    
    pass3 = (
        res3.overall_status == SafetyStatus.CONTRAINDICATED and
        any(c.type == "allergy" for c in res3.checks) and
        res3.checks[0].evidence[0].source == "egypt_antimicrobial_formulary_2023.pdf" and
        res3.checks[0].evidence[0].page == 371
    )
    test_results.append(("3. VERIFIED Allergy Rule Triggered (Amoxicillin P.371)", pass3, res3))
    print(f"Test 3: VERIFIED Allergy Rule -> Status: {res3.overall_status.value} | Page: {res3.checks[0].evidence[0].page if res3.checks else None} [{'PASS' if pass3 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 4: VERIFIED Drug-Disease Rule (Dexamethasone + Diabetes Mellitus P.153)
    # -------------------------------------------------------------
    u4 = "user_4"
    add_patient_condition(u4, "Diabetes Mellitus", confirmed=True)
    p4 = get_patient_profile(u4)
    res4 = evaluate_medication_safety(medication="dexamethasone", patient_profile=p4, query_text="ينفع آخد ديكساميثازون؟")
    
    pass4 = (
        res4.overall_status == SafetyStatus.CAUTION and
        any(c.type == "drug_disease" for c in res4.checks) and
        res4.checks[0].evidence[0].page == 153
    )
    test_results.append(("4. VERIFIED Drug-Disease Rule (Dexamethasone P.153)", pass4, res4))
    print(f"Test 4: VERIFIED Drug-Disease Rule -> Status: {res4.overall_status.value} | Page: {res4.checks[0].evidence[0].page if res4.checks else None} [{'PASS' if pass4 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 5: VERIFIED Drug-Drug Interaction (Sildenafil + Isosorbide Dinitrate P.69)
    # -------------------------------------------------------------
    u5 = "user_5"
    add_patient_medication(u5, "nitroglycerin", confirmed=True)
    p5 = get_patient_profile(u5)
    res5 = evaluate_medication_safety(medication="sildenafil", patient_profile=p5, query_text="Can I take sildenafil?")
    
    pass5 = (
        res5.overall_status == SafetyStatus.CONTRAINDICATED and
        any(c.type == "drug_drug" for c in res5.checks) and
        res5.checks[0].evidence[0].page == 69
    )
    test_results.append(("5. VERIFIED DDI Rule (Sildenafil + Nitrates P.69)", pass5, res5))
    print(f"Test 5: VERIFIED DDI Rule -> Status: {res5.overall_status.value} | Page: {res5.checks[0].evidence[0].page if res5.checks else None} [{'PASS' if pass5 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 6: VERIFIED Drug-Drug Interaction (Clarithromycin + Simvastatin P.185)
    # -------------------------------------------------------------
    u6 = "user_6"
    add_patient_medication(u6, "simvastatin", confirmed=True)
    p6 = get_patient_profile(u6)
    res6 = evaluate_medication_safety(medication="clarithromycin", patient_profile=p6, query_text="Can I take clarithromycin?")
    
    pass6 = (
        res6.overall_status == SafetyStatus.CONTRAINDICATED and
        any(c.type == "drug_drug" for c in res6.checks) and
        res6.checks[0].evidence[0].page == 185
    )
    test_results.append(("6. VERIFIED DDI Rule (Clarithromycin + Simvastatin P.185)", pass6, res6))
    print(f"Test 6: VERIFIED DDI Rule -> Status: {res6.overall_status.value} | Page: {res6.checks[0].evidence[0].page if res6.checks else None} [{'PASS' if pass6 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 7: Downgraded Suspect Rule #1 (Spironolactone + Captopril) -> NOT in Active Seed
    # -------------------------------------------------------------
    u7 = "user_7"
    add_patient_medication(u7, "captopril", confirmed=True)
    p7 = get_patient_profile(u7)
    res7 = evaluate_medication_safety(medication="spironolactone", patient_profile=p7, query_text="Can I take spironolactone?")
    
    pass7 = (
        res7.overall_status == SafetyStatus.INSUFFICIENT_EVIDENCE and
        len(res7.checks) == 0
    )
    test_results.append(("7. Downgraded Suspect Rule #1 (Spironolactone + Captopril) Excluded", pass7, res7))
    print(f"Test 7: Downgraded Spironolactone+Captopril -> Checks: {len(res7.checks)} | Status: {res7.overall_status.value} [{'PASS' if pass7 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 8: Downgraded Suspect Rule #2 (Clopidogrel + Omeprazole) -> NOT in Active Seed
    # -------------------------------------------------------------
    u8 = "user_8"
    add_patient_medication(u8, "omeprazole", confirmed=True)
    p8 = get_patient_profile(u8)
    res8 = evaluate_medication_safety(medication="clopidogrel", patient_profile=p8, query_text="Can I take clopidogrel?")
    
    pass8 = (
        res8.overall_status == SafetyStatus.INSUFFICIENT_EVIDENCE and
        len(res8.checks) == 0
    )
    test_results.append(("8. Downgraded Rule (Clopidogrel + Omeprazole) Excluded", pass8, res8))
    print(f"Test 8: Downgraded Clopidogrel+Omeprazole -> Checks: {len(res8.checks)} | Status: {res8.overall_status.value} [{'PASS' if pass8 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 9: Downgraded Do-Not-Crush Rule (Aspocid 81) -> Excluded from Seed
    # -------------------------------------------------------------
    dnc_res9 = check_do_not_crush("ينفع اطحن قرص aspocid 81؟", "aspocid 81")
    pass9 = dnc_res9 is None # Product-specific rule downgraded
    test_results.append(("9. Downgraded Aspocid 81 Do-Not-Crush Rule Excluded", pass9, dnc_res9))
    print(f"Test 9: Downgraded Aspocid 81 -> Triggered: {dnc_res9 is not None} [{'PASS' if pass9 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 10: VERIFIED High-Alert Rule (Insulin P.10)
    # -------------------------------------------------------------
    ha_res10 = check_high_alert("insulin")
    pass10 = (
        ha_res10 is not None and
        ha_res10.type == "high_alert" and
        ha_res10.evidence[0].source == "egypt_high_alert_medications_2025.pdf" and
        ha_res10.evidence[0].page == 10
    )
    test_results.append(("10. VERIFIED High-Alert Rule (Insulin P.10)", pass10, ha_res10))
    print(f"Test 10: VERIFIED High-Alert Insulin -> Page: {ha_res10.evidence[0].page if ha_res10 else None} [{'PASS' if pass10 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 11: VERIFIED High-Alert Rule (Enoxaparin P.6)
    # -------------------------------------------------------------
    ha_res11 = check_high_alert("enoxaparin")
    pass11 = (
        ha_res11 is not None and
        ha_res11.type == "high_alert" and
        ha_res11.evidence[0].page == 6
    )
    test_results.append(("11. VERIFIED High-Alert Rule (Enoxaparin P.6)", pass11, ha_res11))
    print(f"Test 11: VERIFIED High-Alert Enoxaparin -> Page: {ha_res11.evidence[0].page if ha_res11 else None} [{'PASS' if pass11 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 12: Unconfirmed Condition Confirmation Flow
    # -------------------------------------------------------------
    u12 = "user_12"
    add_patient_condition(u12, "Asthma", confirmed=False)
    p12 = get_patient_profile(u12)
    res12 = evaluate_medication_safety(medication="propranolol", patient_profile=p12, query_text="ينفع أستخدم بروبرانولول؟", conversation_id="conv_12")
    
    pass12 = (
        res12.requires_confirmation is True and
        res12.overall_status == SafetyStatus.REQUIRES_CONFIRMATION
    )
    test_results.append(("12. Unconfirmed Stored Condition Requires Confirmation", pass12, res12))
    print(f"Test 12: Unconfirmed Condition -> Requires Confirmation: {res12.requires_confirmation} [{'PASS' if pass12 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 13: Confirmation Resolution ('ايوه' -> Confirmed -> Contraindicated)
    # -------------------------------------------------------------
    resolve_pending_confirmation(u12, "conv_12", "ايوه عندي حساسية صدر")
    p12_updated = get_patient_profile(u12)
    res12_post = evaluate_medication_safety(medication="propranolol", patient_profile=p12_updated, query_text="ينفع أستخدم بروبرانولول؟")
    
    pass13 = (
        p12_updated.conditions[0].confirmed is True and
        res12_post.overall_status == SafetyStatus.CONTRAINDICATED
    )
    test_results.append(("13. Confirmation Resolution ('ايوه' -> Confirmed -> Contraindicated)", pass13, res12_post))
    print(f"Test 13: Confirmation Resolution -> Post-Status: {res12_post.overall_status.value} [{'PASS' if pass13 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 14: Verified Turbohaler Video Still Operational
    # -------------------------------------------------------------
    v14 = get_verified_video(query_text="ازاي استخدم التربوهيلر؟")
    pass14 = v14.get("found") is True and v14.get("usage_topic") == "turbohaler_usage"
    test_results.append(("14. Verified Turbohaler Video Intact", pass14, v14))
    print(f"Test 14: Turbohaler Video -> Found: {v14.get('found')} | Topic: {v14.get('usage_topic')} [{'PASS' if pass14 else 'FAIL'}]")

    # -------------------------------------------------------------
    # TEST 15: Cross-User Privacy Partitioning
    # -------------------------------------------------------------
    u15_a = "user_15_alice"
    u15_b = "user_15_bob"
    add_patient_condition(u15_a, "Hypertension", confirmed=True)
    add_patient_allergy(u15_b, "Sulfa", confirmed=True)
    
    p15_a = get_patient_profile(u15_a)
    p15_b = get_patient_profile(u15_b)
    
    pass15 = (
        len(p15_a.conditions) == 1 and len(p15_a.allergies) == 0 and
        len(p15_b.allergies) == 1 and len(p15_b.conditions) == 0
    )
    test_results.append(("15. Cross-User Privacy Partitioning", pass15, None))
    print(f"Test 15: Cross-User Privacy -> Alice Conds: {len(p15_a.conditions)}, Bob Allgs: {len(p15_b.allergies)} [{'PASS' if pass15 else 'FAIL'}]")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    all_passed = all(r[1] for r in test_results)
    print("=" * 95)
    print(f"FINAL RESULT: {'ALL 15 FINAL INTEGRITY TESTS PASSED (100%)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 95)

    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
