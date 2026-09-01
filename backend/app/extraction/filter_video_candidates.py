import csv
import json
from pathlib import Path
from typing import Dict, Any, List
from app.extraction.normalizer import classify_patient_self_use, normalize_route

def filter_video_candidates(extracted_csv_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Filters extracted medication forms down to genuine Patient Self-Use Video Candidates.
    Produces:
      - data/processed/final_video_candidates.csv
      - data/processed/video_candidate_summary.json
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(extracted_csv_path, "r", encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))

    total_rows = len(records)
    auto_yes_count = 0
    auto_no_count = 0
    needs_review_count = 0

    technique_dist = {}
    device_cat_dist = {}
    exact_device_req_count = 0

    injection_before = 0
    injection_after = 0
    oral_liquid_before = 0
    oral_liquid_after = 0
    inhalation_count = 0
    nebulizer_count = 0

    final_candidates: List[Dict[str, Any]] = []

    for r in records:
        gen_name = r.get("generic_name", "")
        raw_form = r.get("dosage_form_raw", "")
        norm_form = r.get("dosage_form_normalized", "")
        route_str = r.get("route_of_administration", "")
        admin_instr = r.get("administration_instructions", "")

        _, norm_routes = normalize_route(route_str)

        # Baseline category counts before filtering
        if "injection" in norm_form or "iv_infusion" in norm_form or any(rt in ("IV", "IM", "SC") for rt in norm_routes):
            injection_before += 1
        if norm_form in ("oral_drops", "oral_suspension", "oral_syrup", "oral_solution", "oral_emulsion"):
            oral_liquid_before += 1

        classification = classify_patient_self_use(
            norm_form=norm_form,
            norm_routes=norm_routes,
            generic_name=gen_name,
            admin_instructions=admin_instr,
            raw_dosage_form=raw_form
        )

        relevance = classification["self_use_video_relevance"]
        tech_cat = classification["technique_category"]
        dev_cat = classification["device_category"]
        dev_spec = classification["device_specificity"]
        exact_req = classification["exact_device_review_required"]
        reason = classification["classification_reason"]

        # Track metrics
        if relevance == "yes":
            auto_yes_count += 1
        elif relevance == "no":
            auto_no_count += 1
        else:
            needs_review_count += 1

        technique_dist[tech_cat] = technique_dist.get(tech_cat, 0) + 1
        device_cat_dist[dev_cat] = device_cat_dist.get(dev_cat, 0) + 1

        if exact_req:
            exact_device_req_count += 1

        # Check special categories
        if dev_cat == "inhaler":
            inhalation_count += 1
        elif dev_cat == "nebulizer":
            nebulizer_count += 1

        # Final candidate filtering (keep ONLY yes or needs_review)
        if relevance in ("yes", "needs_review"):
            if dev_cat in ("injection", "self_injection", "insulin_injection"):
                injection_after += 1
            if dev_cat == "oral_liquid":
                oral_liquid_after += 1

            final_candidates.append({
                "generic_name": gen_name,
                "dosage_form_raw": raw_form,
                "dosage_form_normalized": norm_form,
                "route": route_str,
                "administration_instructions": admin_instr or "",
                "device_category": dev_cat,
                "technique_category": tech_cat,
                "self_use_video_relevance": relevance,
                "device_specificity": dev_spec,
                "exact_device_review_required": "true" if exact_req else "false",
                "exact_device_name": "", # Intentionally blank for manual review
                "source_file": r.get("source_file", ""),
                "source_page": r.get("source_page", ""),
                "review_status": "pending",
                "review_notes": reason
            })

    # Save final_video_candidates.csv
    final_csv_path = output_dir / "final_video_candidates.csv"
    fieldnames = [
        "generic_name", "dosage_form_raw", "dosage_form_normalized", "route",
        "administration_instructions", "device_category", "technique_category",
        "self_use_video_relevance", "device_specificity", "exact_device_review_required",
        "exact_device_name", "source_file", "source_page", "review_status", "review_notes"
    ]
    with open(final_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in final_candidates:
            writer.writerow(c)

    summary_data = {
        "total_medication_form_rows": total_rows,
        "automatic_no_count": auto_no_count,
        "automatic_yes_count": auto_yes_count,
        "needs_review_count": needs_review_count,
        "final_candidate_count": len(final_candidates),
        "exact_device_review_required_count": exact_device_req_count,
        "inhalation_records_count": inhalation_count,
        "nebulizer_records_count": nebulizer_count,
        "injection_records_before_filtering": injection_before,
        "injection_records_after_filtering": injection_after,
        "oral_liquid_records_before_filtering": oral_liquid_before,
        "oral_liquid_records_after_filtering": oral_liquid_after,
        "technique_category_distribution": dict(sorted(technique_dist.items(), key=lambda x: x[1], reverse=True)),
        "device_category_distribution": dict(sorted(device_cat_dist.items(), key=lambda x: x[1], reverse=True))
    }

    summary_json_path = output_dir / "video_candidate_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    return summary_data
