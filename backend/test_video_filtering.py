import sys
import csv
from pathlib import Path
from app.extraction.normalizer import classify_patient_self_use, normalize_route

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_filtering_tests():
    project_root = Path(__file__).resolve().parent.parent
    final_csv_path = project_root / "data" / "processed" / "final_video_candidates.csv"

    print("=" * 85)
    print("TAMARGI.AI — PATIENT SELF-USE VIDEO FILTERING TEST SUITE")
    print("=" * 85)

    test_cases = [
        # 1. Ordinary swallowed tablet -> no
        {
            "name": "1. Ordinary Swallowed Tablet",
            "args": {"norm_form": "tablet", "norm_routes": ["Oral"], "generic_name": "Paracetamol"},
            "expected_relevance": "no",
            "expected_tech": "solid_oral"
        },
        # 2. Ordinary capsule -> no
        {
            "name": "2. Ordinary Capsule",
            "args": {"norm_form": "capsule", "norm_routes": ["Oral"], "generic_name": "Amoxicillin"},
            "expected_relevance": "no",
            "expected_tech": "solid_oral"
        },
        # 3. Ordinary oral syrup -> no
        {
            "name": "3. Ordinary Oral Syrup",
            "args": {"norm_form": "oral_syrup", "norm_routes": ["Oral"], "generic_name": "Dicyclomine"},
            "expected_relevance": "no",
            "expected_dev_cat": "oral_liquid"
        },
        # 4. IV infusion -> no
        {
            "name": "4. IV Infusion (Hospital)",
            "args": {"norm_form": "iv_infusion", "norm_routes": ["IV"], "generic_name": "Ciprofloxacin"},
            "expected_relevance": "no",
            "expected_dev_cat": "hospital_parenteral"
        },
        # 5. Generic IM hospital injection -> no (not auto yes)
        {
            "name": "5. Generic IM Hospital Injection",
            "args": {"norm_form": "injection", "norm_routes": ["IM", "IV"], "generic_name": "Gentamicin", "raw_dosage_form": "Ampoule 80mg"},
            "expected_relevance": "no",
            "expected_dev_cat": "hospital_parenteral"
        },
        # 6. Insulin pen -> yes
        {
            "name": "6. Insulin Pen",
            "args": {"norm_form": "injection", "norm_routes": ["SC"], "generic_name": "Insulin Glargine", "raw_dosage_form": "Prefilled Pen 100 units/ml"},
            "expected_relevance": "yes",
            "expected_tech": "insulin_pen",
            "expected_exact_req": True
        },
        # 7. Eye drops -> yes
        {
            "name": "7. Eye Drops",
            "args": {"norm_form": "eye_drops", "norm_routes": ["Ophthalmic"], "generic_name": "Timolol"},
            "expected_relevance": "yes",
            "expected_tech": "eye_drops",
            "expected_exact_req": False
        },
        # 8. Ear drops -> yes
        {
            "name": "8. Ear Drops",
            "args": {"norm_form": "ear_drops", "norm_routes": ["Otic"], "generic_name": "Ofloxacin"},
            "expected_relevance": "yes",
            "expected_tech": "ear_drops"
        },
        # 9. Nasal spray -> yes
        {
            "name": "9. Nasal Spray",
            "args": {"norm_form": "nasal_spray", "norm_routes": ["Nasal"], "generic_name": "Fluticasone"},
            "expected_relevance": "yes",
            "expected_tech": "nasal_spray"
        },
        # 10. Suppository -> yes
        {
            "name": "10. Rectal Suppository",
            "args": {"norm_form": "suppository", "norm_routes": ["Rectal"], "generic_name": "Glycerin"},
            "expected_relevance": "yes",
            "expected_tech": "suppository"
        },
        # 11. Transdermal patch -> yes
        {
            "name": "11. Transdermal Patch",
            "args": {"norm_form": "transdermal_patch", "norm_routes": ["Topical"], "generic_name": "Fentanyl"},
            "expected_relevance": "yes",
            "expected_tech": "transdermal_patch"
        },
        # 12. Inhaler -> yes
        {
            "name": "12. Dry Powder Inhaler (DPI)",
            "args": {"norm_form": "inhalation_powder", "norm_routes": ["Inhalation"], "generic_name": "Budesonide"},
            "expected_relevance": "yes",
            "expected_tech": "dpi_inhaler",
            "expected_dev_cat": "inhaler",
            "expected_exact_req": True
        },
        # 13. Nebulizer solution -> device_category = nebulizer, NOT inhaler (Tobramycin fix!)
        {
            "name": "13. Tobramycin Nebulizer Solution (Bug Fix Verification)",
            "args": {"norm_form": "nebulizer_solution", "norm_routes": ["Inhalation"], "generic_name": "Tobramycin", "raw_dosage_form": "Inhalation Solution 300 mg/5ml"},
            "expected_relevance": "yes",
            "expected_tech": "nebulizer",
            "expected_dev_cat": "nebulizer", # MUST be nebulizer, NOT inhaler
            "expected_exact_req": False
        },
        # 14. Generic inhaler without exact device -> exact_device_review_required = True
        {
            "name": "14. Generic Inhaler (Exact Device Review Required)",
            "args": {"norm_form": "inhalation_aerosol", "norm_routes": ["Inhalation"], "generic_name": "Salbutamol"},
            "expected_exact_req": True
        }
    ]

    all_passed = True
    for t in test_cases:
        res = classify_patient_self_use(**t["args"])
        passed = True
        if "expected_relevance" in t and res["self_use_video_relevance"] != t["expected_relevance"]:
            passed = False
        if "expected_tech" in t and res["technique_category"] != t["expected_tech"]:
            passed = False
        if "expected_dev_cat" in t and res["device_category"] != t["expected_dev_cat"]:
            passed = False
        if "expected_exact_req" in t and res["exact_device_review_required"] != t["expected_exact_req"]:
            passed = False

        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"Test {t['name']}")
        print(f"  -> Output: relevance={res['self_use_video_relevance']}, tech={res['technique_category']}, dev_cat={res['device_category']}, exact_req={res['exact_device_review_required']}")
        print(f"  -> Result: [{status}]\n")

    # CSV File Check
    print("Checking final_video_candidates.csv integrity...")
    if not final_csv_path.exists():
        print("FAILED: final_video_candidates.csv not found.")
        return False

    with open(final_csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Verify no 'no' rows made it into final candidates
    has_no_rows = any(r["self_use_video_relevance"] == "no" for r in rows)
    # Verify all rows have source file and page
    has_provenance = all(r["source_file"] and r["source_page"] for r in rows)
    # Verify Tobramycin in CSV is classified as nebulizer
    tobra_rows = [r for r in rows if "tobramycin" in r["generic_name"].lower() and "nebulizer" in r["dosage_form_normalized"]]
    tobra_is_nebulizer = all(r["device_category"] == "nebulizer" for r in tobra_rows) if tobra_rows else True

    csv_checks_passed = (not has_no_rows) and has_provenance and tobra_is_nebulizer
    print(f"  -> Total Candidates in CSV: {len(rows)}")
    print(f"  -> Zero 'no' records in CSV: {not has_no_rows}")
    print(f"  -> 100% Provenance Preserved: {has_provenance}")
    print(f"  -> Tobramycin Nebulizer Category Correct: {tobra_is_nebulizer}")
    print(f"  -> CSV Checks: [{'PASS' if csv_checks_passed else 'FAIL'}]\n")

    overall = all_passed and csv_checks_passed
    print("=" * 85)
    print(f"TEST SUITE FINAL RESULT: {'ALL TESTS PASSED (100%)' if overall else 'SOME TESTS FAILED'}")
    print("=" * 85)
    return overall

if __name__ == "__main__":
    success = run_filtering_tests()
    if not success:
        sys.exit(1)
