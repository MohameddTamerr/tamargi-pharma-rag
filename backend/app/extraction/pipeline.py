import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from app.extraction.pdf_extractor import parse_eda_pdf
from app.database.supabase import get_supabase_client

def run_extraction_pipeline(data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Executes the full EDA PDF extraction pipeline across all available PDF files in data_dir.
    Saves outputs to output_dir and computes full summary metrics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    all_extracted_rows: List[Dict[str, Any]] = []
    pdf_stats: List[Dict[str, Any]] = []
    parsing_failures: List[Dict[str, Any]] = []

    pdf_files = sorted(list(data_dir.rglob("*.pdf")))
    print(f"[Pipeline] Found {len(pdf_files)} PDF files in {data_dir}")

    for pdf_path in pdf_files:
        try:
            print(f"[Pipeline] Processing: {pdf_path.name} ...")
            rows = parse_eda_pdf(pdf_path)
            all_extracted_rows.extend(rows)
            pdf_stats.append({
                "file_name": pdf_path.name,
                "relative_path": str(pdf_path.relative_to(data_dir)),
                "records_extracted": len(rows),
                "unique_drugs": len(set(r["generic_name"] for r in rows))
            })
            print(f"  -> Extracted {len(rows)} dosage form rows ({len(set(r['generic_name'] for r in rows))} unique drugs)")
        except Exception as e:
            print(f"  [Error] Failed parsing {pdf_path.name}: {e}")
            parsing_failures.append({
                "file_name": pdf_path.name,
                "error": str(e)
            })

    # Quality Control & Deduplication
    unique_rows: List[Dict[str, Any]] = []
    seen_keys = set()
    qc_flagged = []

    for r in all_extracted_rows:
        key = (r["generic_name"].lower(), r["dosage_form_raw"].lower(), r["source_file"], r["source_page"])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # QC Check 1: Empty or invalid generic name
        if not r["generic_name"] or len(r["generic_name"]) < 2:
            qc_flagged.append({"reason": "invalid_generic_name", "record": r})
            continue

        # QC Check 2: Empty dosage form
        if not r["dosage_form_raw"] or len(r["dosage_form_raw"]) < 2:
            qc_flagged.append({"reason": "empty_dosage_form", "record": r})
            continue

        # QC Check 3: Suspiciously long dosage form (> 250 chars)
        if len(r["dosage_form_raw"]) > 250:
            qc_flagged.append({"reason": "long_dosage_form", "record": r})

        unique_rows.append(r)

    # Metrics aggregation
    total_drugs = len(set(r["generic_name"] for r in unique_rows))
    total_forms = len(unique_rows)
    
    dosage_form_dist = {}
    route_dist = {}
    category_dist = {}
    video_relevant_count = 0
    device_review_candidates = []

    for r in unique_rows:
        df = r["dosage_form_normalized"]
        dosage_form_dist[df] = dosage_form_dist.get(df, 0) + 1

        route = r["route_of_administration"] or "Unspecified"
        route_dist[route] = route_dist.get(route, 0) + 1

        cat = r["device_category"] or "unspecified"
        category_dist[cat] = category_dist.get(cat, 0) + 1

        if r["video_relevant"] in ("true", "needs_review"):
            video_relevant_count += 1
            device_review_candidates.append({
                "generic_name": r["generic_name"],
                "dosage_form_raw": r["dosage_form_raw"],
                "dosage_form_normalized": r["dosage_form_normalized"],
                "route": r["route_of_administration"],
                "device_category": r["device_category"],
                "source_file": r["source_file"],
                "source_page": r["source_page"],
                "exact_device_name": "", # Intentionally blank for manual review
                "review_status": "pending",
                "review_notes": "needs manual exact device verification"
            })

    # Save 1: Complete Extracted Medication Forms CSV
    extracted_csv_path = output_dir / "extracted_medication_forms.csv"
    fieldnames_all = [
        "generic_name", "dosage_form_raw", "dosage_form_normalized", "strength",
        "route_of_administration", "administration_instructions", "device_category",
        "exact_device_name", "exact_device_verified", "video_relevant",
        "source_file", "source_page", "active"
    ]
    with open(extracted_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_all)
        writer.writeheader()
        for r in unique_rows:
            writer.writerow(r)

    # Save 2: Manual Review Candidates CSV
    review_csv_path = output_dir / "device_review_candidates.csv"
    fieldnames_review = [
        "generic_name", "dosage_form_raw", "dosage_form_normalized", "route",
        "device_category", "source_file", "source_page", "exact_device_name",
        "review_status", "review_notes"
    ]
    with open(review_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_review)
        writer.writeheader()
        for c in device_review_candidates:
            writer.writerow(c)

    # Save 3: Detailed Summary JSON
    summary_data = {
        "total_pdf_files": len(pdf_files),
        "total_unique_drugs": total_drugs,
        "total_dosage_form_rows": total_forms,
        "video_relevant_count": video_relevant_count,
        "device_review_candidates_count": len(device_review_candidates),
        "qc_flagged_count": len(qc_flagged),
        "dosage_form_distribution": dict(sorted(dosage_form_dist.items(), key=lambda x: x[1], reverse=True)),
        "route_distribution": dict(sorted(route_dist.items(), key=lambda x: x[1], reverse=True)),
        "device_category_distribution": dict(sorted(category_dist.items(), key=lambda x: x[1], reverse=True)),
        "pdf_breakdown": pdf_stats,
        "parsing_failures": parsing_failures
    }

    summary_json_path = output_dir / "extraction_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"\n[Pipeline Complete] Output files generated in {output_dir}:")
    print(f"  1. {extracted_csv_path.name} ({total_forms} rows)")
    print(f"  2. {review_csv_path.name} ({len(device_review_candidates)} review candidates)")
    print(f"  3. {summary_json_path.name}")

    return summary_data
