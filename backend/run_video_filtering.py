import sys
from pathlib import Path
from app.extraction.filter_video_candidates import filter_video_candidates

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    extracted_csv_path = project_root / "data" / "processed" / "extracted_medication_forms.csv"
    output_dir = project_root / "data" / "processed"

    print("=" * 80)
    print("TAMARGI.AI — PATIENT SELF-USE VIDEO RELEVANCE FILTERING")
    print("=" * 80)
    print(f"Input Dataset:  {extracted_csv_path}")
    print(f"Output Directory: {output_dir}\n")

    summary = filter_video_candidates(extracted_csv_path=extracted_csv_path, output_dir=output_dir)

    print("\n" + "=" * 80)
    print("FILTERING RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Medication Form Rows:          {summary['total_medication_form_rows']}")
    print(f"Automatic NO Count (Non-video forms): {summary['automatic_no_count']}")
    print(f"Automatic YES Count (Self-use video): {summary['automatic_yes_count']}")
    print(f"NEEDS_REVIEW Count:                  {summary['needs_review_count']}")
    print(f"Final Patient Self-Use Candidates:   {summary['final_candidate_count']}")
    print(f"Exact Device Review Required Count:  {summary['exact_device_review_required_count']}")

    print("\nTarget Category Before/After Comparisons:")
    print(f"  - Injections:   {summary['injection_records_before_filtering']} before -> {summary['injection_records_after_filtering']} after")
    print(f"  - Oral Liquids: {summary['oral_liquid_records_before_filtering']} before -> {summary['oral_liquid_records_after_filtering']} after")
    print(f"  - Inhalers:     {summary['inhalation_records_count']}")
    print(f"  - Nebulizers:   {summary['nebulizer_records_count']}")

    print("\nTechnique Category Distribution:")
    for tech, count in summary["technique_category_distribution"].items():
        print(f"  - {tech:<28} : {count} records")

    print("\nDevice Category Distribution:")
    for dev, count in summary["device_category_distribution"].items():
        print(f"  - {dev:<28} : {count} records")

    print("\n" + "=" * 80)
    print("FILTERING PIPELINE COMPLETED")
    print("=" * 80)
