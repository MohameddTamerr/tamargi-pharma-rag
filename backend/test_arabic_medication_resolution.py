import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.normalization.text_normalizer import normalize_arabic_text, levenshtein_distance
from app.normalization.medication_resolver import (
    resolve_medication,
    extract_all_medications,
    extract_strength,
    extract_dosage_form
)
from app.normalization.condition_normalizer import normalize_condition_name, extract_conditions
from app.normalization.symptom_normalizer import extract_symptoms
from app.normalization.device_normalizer import resolve_device, is_ambiguous_device
from app.normalization.query_translator import build_canonical_retrieval_query
from app.orchestrator.orchestrator import TamargiOrchestrator
from app.safety.models import SafetyStatus
from app.safety.patient_context import (
    reset_in_memory_store,
    add_patient_condition,
    add_patient_medication,
    get_patient_profile
)
from app.safety.repository import seed_verified_rule, clear_test_rules

def seed_verified_rules():
    """Seeds the 9 verified rules from final_verified_safety_rules.csv."""
    df = pd.read_csv('c:/Users/user/Downloads/tamargi-pharma-rag/data/processed/final_verified_safety_rules.csv')
    verified_rows = df[df['final_verification_status'] == 'VERIFIED']
    
    for idx, r in verified_rows.iterrows():
        status_enum = SafetyStatus(r['final_status'])
        seed_verified_rule({
            "id": f"norm-verified-{idx+1}",
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

def run_all_resolution_tests():
    print("=" * 95)
    print("TAMARGI.AI — ARABIC & EGYPTIAN MEDICATION RESOLUTION TEST SUITE")
    print("=" * 95)

    reset_in_memory_store()
    clear_test_rules()
    seed_verified_rules()

    results = []

    # 1. بروفين -> ibuprofen
    res1 = resolve_medication("بروفين")
    p1 = res1 is not None and res1.canonical_generic == "ibuprofen"
    results.append(("1. بروفين -> ibuprofen", p1, res1.canonical_generic if res1 else None))
    print(f"Check 1: بروفين -> {res1.canonical_generic if res1 else None} [{'PASS' if p1 else 'FAIL'}]")

    # 2. Brufen -> ibuprofen
    res2 = resolve_medication("Brufen")
    p2 = res2 is not None and res2.canonical_generic == "ibuprofen"
    results.append(("2. Brufen -> ibuprofen", p2, res2.canonical_generic if res2 else None))
    print(f"Check 2: Brufen -> {res2.canonical_generic if res2 else None} [{'PASS' if p2 else 'FAIL'}]")

    # 3. بنادول -> paracetamol
    res3 = resolve_medication("بنادول")
    p3 = res3 is not None and res3.canonical_generic == "paracetamol"
    results.append(("3. بنادول -> paracetamol", p3, res3.canonical_generic if res3 else None))
    print(f"Check 3: بنادول -> {res3.canonical_generic if res3 else None} [{'PASS' if p3 else 'FAIL'}]")

    # 4. Panadol -> paracetamol
    res4 = resolve_medication("Panadol")
    p4 = res4 is not None and res4.canonical_generic == "paracetamol"
    results.append(("4. Panadol -> paracetamol", p4, res4.canonical_generic if res4 else None))
    print(f"Check 4: Panadol -> {res4.canonical_generic if res4 else None} [{'PASS' if p4 else 'FAIL'}]")

    # 5. جلوكوفاج -> metformin
    res5 = resolve_medication("جلوكوفاج")
    p5 = res5 is not None and res5.canonical_generic == "metformin"
    results.append(("5. جلوكوفاج -> metformin", p5, res5.canonical_generic if res5 else None))
    print(f"Check 5: جلوكوفاج -> {res5.canonical_generic if res5 else None} [{'PASS' if p5 else 'FAIL'}]")

    # 6. Ventolin -> salbutamol
    res6 = resolve_medication("Ventolin")
    p6 = res6 is not None and res6.canonical_generic == "salbutamol"
    results.append(("6. Ventolin -> salbutamol", p6, res6.canonical_generic if res6 else None))
    print(f"Check 6: Ventolin -> {res6.canonical_generic if res6 else None} [{'PASS' if p6 else 'FAIL'}]")

    # 7. Arabic + English mixed interaction question
    # "ينفع اخد Brufen وانا باخد warfarin؟"
    meds7 = extract_all_medications("ينفع اخد Brufen وانا باخد warfarin؟")
    gens7 = [m.canonical_generic for m in meds7]
    p7 = "ibuprofen" in gens7 and "warfarin" in gens7
    results.append(("7. Arabic + English mixed interaction extraction", p7, gens7))
    print(f"Check 7: Mixed interaction extraction -> {gens7} [{'PASS' if p7 else 'FAIL'}]")

    # 8. Arabic drug comparison
    # "ايه الفرق بين Panadol و Brufen؟"
    meds8 = extract_all_medications("ايه الفرق بين Panadol و Brufen؟")
    gens8 = [m.canonical_generic for m in meds8]
    p8 = "paracetamol" in gens8 and "ibuprofen" in gens8
    results.append(("8. Arabic drug comparison extraction", p8, gens8))
    print(f"Check 8: Arabic comparison extraction -> {gens8} [{'PASS' if p8 else 'FAIL'}]")

    # 9. Strength extraction
    # "Brufen 400 tablet" -> 400
    str9 = extract_strength("Brufen 400 tablet")
    p9 = str9 is not None and "400" in str9
    results.append(("9. Strength extraction (400)", p9, str9))
    print(f"Check 9: Strength extraction -> {str9} [{'PASS' if p9 else 'FAIL'}]")

    # 10. Dosage-form extraction
    # "فنتولين شراب" -> syrup
    form10 = extract_dosage_form("فنتولين شراب للاطفال")
    p10 = form10 == "syrup"
    results.append(("10. Dosage-form extraction (syrup)", p10, form10))
    print(f"Check 10: Dosage-form extraction -> {form10} [{'PASS' if p10 else 'FAIL'}]")

    # 11. ربو -> asthma
    cond11 = normalize_condition_name("عندي ربو")
    p11 = cond11 == "asthma"
    results.append(("11. ربو -> asthma", p11, cond11))
    print(f"Check 11: ربو -> {cond11} [{'PASS' if p11 else 'FAIL'}]")

    # 12. سكر -> diabetes_mellitus
    cond12 = normalize_condition_name("مرض السكر")
    p12 = cond12 == "diabetes_mellitus"
    results.append(("12. سكر -> diabetes_mellitus", p12, cond12))
    print(f"Check 12: سكر -> {cond12} [{'PASS' if p12 else 'FAIL'}]")

    # 13. صداع remains symptom (never inferred as disease)
    sym13 = extract_symptoms("عندي صداع شديد")
    conds13 = extract_conditions("عندي صداع شديد")
    p13 = "headache" in sym13 and len(conds13) == 0
    results.append(("13. صداع remains symptom (no disease)", p13, sym13))
    print(f"Check 13: صداع -> Symptom: {sym13} | Conditions: {conds13} [{'PASS' if p13 else 'FAIL'}]")

    # 14. Generic بخاخ remains ambiguous
    dev14 = resolve_device("ازاي استخدم البخاخ؟")
    p14 = dev14 is not None and dev14[1] is True # is_ambiguous = True
    results.append(("14. Generic 'بخاخ' is ambiguous", p14, dev14))
    print(f"Check 14: Generic بخاخ -> Ambiguous: {dev14[1] if dev14 else False} [{'PASS' if p14 else 'FAIL'}]")

    # 15. Turbohaler resolves exact device
    dev15 = resolve_device("طريقة استخدام جهاز Turbohaler")
    p15 = dev15 is not None and dev15[0] == "Turbohaler" and dev15[1] is False
    results.append(("15. Turbohaler resolves exact device", p15, dev15))
    print(f"Check 15: Turbohaler -> Device: {dev15[0] if dev15 else None} | Ambiguous: {dev15[1] if dev15 else True} [{'PASS' if p15 else 'FAIL'}]")

    # 16. Low-confidence / Unrecognized medication handling
    res16 = resolve_medication("دواء_غير_معروف_xyz123")
    p16 = res16 is None
    results.append(("16. Unrecognized medication -> None (no guess)", p16, res16))
    print(f"Check 16: Unrecognized Med -> {res16} [{'PASS' if p16 else 'FAIL'}]")

    # 17. Arabic personalized safety reaches existing Safety Engine
    u17 = "user_norm_17"
    add_patient_condition(u17, "Diabetes Mellitus", confirmed=True)
    res17 = TamargiOrchestrator.orchestrate("ينفع آخد ديكساميثازون؟", conversation_id="conv_norm_17", user_id=u17)
    p17 = res17.safety is not None and res17.safety.overall_status == SafetyStatus.CAUTION
    results.append(("17. Arabic personalized safety reaches Safety Engine", p17, res17.safety.overall_status if res17.safety else None))
    print(f"Check 17: Arabic Safety Check -> Status: {res17.safety.overall_status if res17.safety else None} [{'PASS' if p17 else 'FAIL'}]")

    # 18. Arabic comparison performs separate retrieval
    res18 = TamargiOrchestrator.orchestrate("ما الفرق بين الباراسيتامول والإيبوبروفين؟", conversation_id="conv_norm_18", user_id="user_norm_18")
    p18 = res18.trace.intent == "drug_comparison" and "comparison_retrieval" in res18.trace.tools_called
    results.append(("18. Arabic comparison performs separate dual retrieval", p18, res18.trace.tools_called))
    print(f"Check 18: Arabic Comparison -> Intent: {res18.trace.intent} | Tools: {res18.trace.tools_called} [{'PASS' if p18 else 'FAIL'}]")

    # 19. Arabic question receives Arabic response
    res19 = TamargiOrchestrator.orchestrate("ما هي دواعي استعمال الباراسيتامول؟", conversation_id="conv_norm_19", user_id="user_norm_19")
    p19 = res19.language_detected == "ar" and any('\u0600' <= c <= '\u06FF' for c in res19.answer[:50])
    results.append(("19. Arabic question receives Arabic response", p19, res19.language_detected))
    print(f"Check 19: Arabic Response -> Lang: {res19.language_detected} [{'PASS' if p19 else 'FAIL'}]")

    # 20. English question receives English response
    res20 = TamargiOrchestrator.orchestrate("What is the mechanism of action of metformin?", conversation_id="conv_norm_20", user_id="user_norm_20")
    p20 = res20.language_detected == "en" and not any('\u0600' <= c <= '\u06FF' for c in res20.answer[:50])
    results.append(("20. English question receives English response", p20, res20.language_detected))
    print(f"Check 20: English Response -> Lang: {res20.language_detected} [{'PASS' if p20 else 'FAIL'}]")

    # -------------------------------------------------------------
    # 21. Evaluate the Curated 52-Utterance Test Dataset
    # -------------------------------------------------------------
    print("-" * 95)
    print("Evaluating Curated 52-Utterance Egyptian Dataset...")
    df_cases = pd.read_csv('c:/Users/user/Downloads/tamargi-pharma-rag/data/processed/arabic_normalization_test_dataset.csv')
    dataset_passed = 0
    dataset_total = len(df_cases)

    for _, row in df_cases.iterrows():
        utt = str(row['utterance'])
        exp_generics = [g.strip() for g in str(row['expected_generics']).split(',')] if pd.notna(row['expected_generics']) and str(row['expected_generics']).strip() else []
        exp_symptoms = [s.strip() for s in str(row['expected_symptoms']).split(',')] if pd.notna(row['expected_symptoms']) and str(row['expected_symptoms']).strip() else []
        exp_conditions = [c.strip() for c in str(row['expected_conditions']).split(',')] if pd.notna(row['expected_conditions']) and str(row['expected_conditions']).strip() else []

        meds = extract_all_medications(utt)
        act_generics = [m.canonical_generic for m in meds]
        act_symptoms = extract_symptoms(utt)
        act_conditions = extract_conditions(utt)

        gen_ok = all(g in act_generics for g in exp_generics) if exp_generics else True
        sym_ok = all(s in act_symptoms for s in exp_symptoms) if exp_symptoms else True
        cond_ok = all(c in act_conditions for c in exp_conditions) if exp_conditions else True

        if gen_ok and sym_ok and cond_ok:
            dataset_passed += 1
        else:
            print(f"Failed row {row['id']}: '{utt}' | ExpG: {exp_generics}, ActG: {act_generics} | ExpS: {exp_symptoms}, ActS: {act_symptoms} | ExpC: {exp_conditions}, ActC: {act_conditions}")

    print(f"Curated Dataset Evaluation: {dataset_passed}/{dataset_total} Utterances Passed ({dataset_passed/dataset_total*100:.1f}%)")
    results.append(("21. 52-Utterance Egyptian Normalization Dataset >= 95%", dataset_passed >= 50, f"{dataset_passed}/{dataset_total}"))

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    all_passed = all(r[1] for r in results)
    print("=" * 95)
    print(f"FINAL RESULT: {'ALL 21 RESOLUTION CHECKS PASSED (100%)' if all_passed else 'SOME CHECKS FAILED'}")
    print("=" * 95)

    return all_passed

if __name__ == "__main__":
    success = run_all_resolution_tests()
    if not success:
        sys.exit(1)
