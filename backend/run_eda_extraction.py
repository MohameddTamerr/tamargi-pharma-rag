import sys
import io
from pathlib import Path
from app.extraction.pipeline import run_extraction_pipeline

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "raw" / "eda"
    output_dir = project_root / "data" / "processed"

    print("=" * 80)
    print("TAMARGI.AI — EDA PDF DATA EXTRACTION PIPELINE")
    print("=" * 80)
    print(f"Source EDA Directory: {data_dir}")
    print(f"Output Directory:     {output_dir}\n")

    summary = run_extraction_pipeline(data_dir=data_dir, output_dir=output_dir)

    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Unique Drugs Extracted:       {summary['total_unique_drugs']}")
    print(f"Total Dosage Form Records:          {summary['total_dosage_form_rows']}")
    print(f"Video-Relevant Dosage Forms:        {summary['video_relevant_count']}")
    print(f"Device Review Candidates (Pending): {summary['device_review_candidates_count']}")
    print(f"Quality Control Flags:              {summary['qc_flagged_count']}")
    print(f"Parsing Failures / Unhandled PDFs:  {len(summary['parsing_failures'])}")

    print("\nTop 10 Normalized Dosage Forms:")
    for form, count in list(summary["dosage_form_distribution"].items())[:10]:
        print(f"  - {form:<28} : {count} records")

    print("\nTop 8 Device Categories:")
    for cat, count in list(summary["device_category_distribution"].items())[:8]:
        print(f"  - {cat:<28} : {count} records")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION FINISHED SUCCESSFULLY")
    print("=" * 80)
