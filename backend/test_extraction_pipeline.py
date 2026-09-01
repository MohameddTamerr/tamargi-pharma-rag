import sys
import csv
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_regression_tests():
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "data" / "processed" / "extracted_medication_forms.csv"
    review_csv_path = project_root / "data" / "processed" / "device_review_candidates.csv"

    print("=" * 85)
    print("TAMARGI.AI — EDA PDF EXTRACTION REGRESSION TEST SUITE")
    print("=" * 85)

    if not csv_path.exists():
        print(f"FAILED: Extracted CSV file not found at {csv_path}")
        return False

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))

    print(f"Loaded {len(records)} extracted medication form records for verification.\n")

    # Helper function to find records for a drug
    def find_drug(name_substr: str):
        return [r for r in records if name_substr.lower() in r["generic_name"].lower()]

    test_results = []

    # -------------------------------------------------------------
    # TEST 1: Dicyclomine (GIT Formulary)
    # -------------------------------------------------------------
    dicy_records = find_drug("Dicyclomine")
    dicy_forms = [r["dosage_form_normalized"] for r in dicy_records]
    has_syrup = "oral_syrup" in dicy_forms
    has_tablet = "tablet" in dicy_forms
    pass_dicy = has_syrup and has_tablet and any("Oral" in r["route_of_administration"] for r in dicy_records)
    test_results.append(("Dicyclomine Extraction (Oral syrup, Tablets, Oral route)", pass_dicy, dicy_records))
    print(f"Test 1: Dicyclomine Extraction")
    print(f"  -> Found Forms: {dicy_forms}")
    print(f"  -> Source: {[r['source_file'] + ' p.' + r['source_page'] for r in dicy_records]}")
    print(f"  -> Result: [{'PASS' if pass_dicy else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 2: Simethicone (GIT Formulary)
    # -------------------------------------------------------------
    sime_records = find_drug("Simethicone")
    sime_forms = [r["dosage_form_normalized"] for r in sime_records]
    has_chewable = "chewable_tablet" in sime_forms
    has_drops = "oral_drops" in sime_forms
    has_susp = "oral_suspension" in sime_forms
    has_emul = "oral_emulsion" in sime_forms
    pass_sime = has_chewable and has_drops and has_susp and has_emul
    test_results.append(("Simethicone Extraction (Chewable, Drops, Suspension, Emulsion)", pass_sime, sime_records))
    print(f"Test 2: Simethicone Extraction")
    print(f"  -> Found Forms: {sime_forms}")
    print(f"  -> Result: [{'PASS' if pass_sime else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 3: Domperidone (GIT Formulary)
    # -------------------------------------------------------------
    domp_records = find_drug("Domperidone")
    domp_forms = [r["dosage_form_normalized"] for r in domp_records]
    has_domp_susp = "oral_suspension" in domp_forms
    has_domp_tab = "tablet" in domp_forms
    has_domp_orodi = "orodispersible_tablet" in domp_forms
    has_domp_eff = "effervescent_granules" in domp_forms
    has_domp_soft = "soft_capsule" in domp_forms
    has_domp_supp = "suppository" in domp_forms
    pass_domp = has_domp_susp and has_domp_tab and has_domp_orodi and has_domp_eff and has_domp_soft and has_domp_supp
    test_results.append(("Domperidone Extraction (Suspension, Tablet, Orodispersible, Granules, Soft Capsule, Suppository)", pass_domp, domp_records))
    print(f"Test 3: Domperidone Extraction")
    print(f"  -> Found Forms: {domp_forms}")
    print(f"  -> Result: [{'PASS' if pass_domp else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 4: Phenytoin (Nervous System Formulary)
    # -------------------------------------------------------------
    phen_records = find_drug("Phenytoin")
    phen_forms = [r["dosage_form_normalized"] for r in phen_records]
    has_phen_cap = "capsule" in phen_forms
    has_phen_susp = "oral_suspension" in phen_forms
    has_phen_cream = "cream" in phen_forms
    has_phen_spray = "topical_spray" in phen_forms
    has_phen_inj = "injection" in phen_forms
    pass_phen = has_phen_cap and has_phen_susp and has_phen_cream and has_phen_spray and has_phen_inj
    test_results.append(("Phenytoin Extraction (Capsule, Suspension, Cream, Spray, Injection)", pass_phen, phen_records))
    print(f"Test 4: Phenytoin Extraction")
    print(f"  -> Found Forms: {phen_forms}")
    print(f"  -> Result: [{'PASS' if pass_phen else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 5: Strict No-Guessing Rule (exact_device_name must be NULL/empty)
    # -------------------------------------------------------------
    inferred_devices = [r for r in records if r["exact_device_name"] and r["exact_device_name"].strip()]
    pass_no_guess = len(inferred_devices) == 0
    test_results.append(("Strict No-Guessing Rule (exact_device_name is strictly NULL)", pass_no_guess, None))
    print(f"Test 5: Strict No-Guessing Rule")
    print(f"  -> Total Extracted Rows with Inferred exact_device_name: {len(inferred_devices)}")
    print(f"  -> Result: [{'PASS' if pass_no_guess else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 6: Device Review Candidates CSV Validation
    # -------------------------------------------------------------
    if not review_csv_path.exists():
        pass_review = False
    else:
        with open(review_csv_path, "r", encoding="utf-8-sig") as f:
            review_records = list(csv.DictReader(f))
        pass_review = len(review_records) > 0 and all(r["review_status"] == "pending" for r in review_records)
    test_results.append(("Device Review Candidates CSV Generated with Pending Status", pass_review, None))
    print(f"Test 6: Device Review Candidates CSV Validation")
    print(f"  -> Total Candidates for Manual Verification: {len(review_records) if pass_review else 0}")
    print(f"  -> Result: [{'PASS' if pass_review else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------
    all_passed = all(r[1] for r in test_results)
    print("=" * 85)
    print(f"REGRESSION TEST SUITE RESULT: {'ALL 6 TEST GROUPS PASSED (100%)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 85)

    return all_passed

if __name__ == "__main__":
    success = run_regression_tests()
    if not success:
        sys.exit(1)
