import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf as fitz
from app.extraction.normalizer import (
    extract_strength_and_form,
    normalize_dosage_form,
    normalize_route,
    classify_video_relevance
)

def clean_extracted_text(text: str) -> str:
    """Removes non-printable noise and normalizes newlines."""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    return t

def parse_formulary_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Parses an EDA Formulary PDF file (monograph format) into structured dosage form rows.
    """
    doc = fitz.open(pdf_path)
    file_name = pdf_path.name
    total_pages = len(doc)
    extracted_rows: List[Dict[str, Any]] = []

    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page_text = doc[page_idx].get_text()
        cleaned = clean_extracted_text(page_text)

        # Skip contents / preface pages
        if page_num <= 10 and ("table of contents" in cleaned.lower() or "alphabetical list of content" in cleaned.lower()):
            continue
        if "alphabetical list of content" in cleaned.lower():
            continue

        # Look for Generic Name patterns
        # e.g., "Generic Name\nPhenytoin" or "Generic Name:\nPhenytoin"
        generic_matches = list(re.finditer(r'(?:Generic\s+Name|Generic\s+name)\s*[:\n]\s*([^\n]+)', cleaned, re.IGNORECASE))
        if not generic_matches:
            continue

        for m in generic_matches:
            gen_name = m.group(1).strip()
            # Clean generic name
            gen_name = re.sub(r"^(?:drug|product|code:)\s*", "", gen_name, flags=re.IGNORECASE).strip()
            if len(gen_name) < 2 or "code:" in gen_name.lower() or "page" in gen_name.lower():
                continue

            start_pos = m.end()
            remaining = cleaned[start_pos:]

            # 1. Find Dosage Form section
            df_match = re.search(
                r'(?:Dosage\s*(?:Form|form)s?(?:/\s*Strengths?|\s*/\s*Strength)?)\s*[:\n]',
                remaining,
                re.IGNORECASE
            )
            if not df_match:
                continue

            df_start = df_match.end()
            df_block = remaining[df_start:]

            # Find boundary of dosage forms (next section)
            next_sec = re.search(
                r'\n\s*(?:Route\s*(?:of\s*Administration|of\s*administration)?|Pharmacologic\s*Category|Indications|ATC|Dosage\s*Regimen|Contra-indications|Contraindications)\s*[:\n]',
                df_block,
                re.IGNORECASE
            )
            if next_sec:
                raw_forms_block = df_block[:next_sec.start()].strip()
                after_df_block = df_block[next_sec.start():]
            else:
                raw_forms_block = df_block[:400].strip()
                after_df_block = df_block

            # 2. Find Route of Administration
            route_match = re.search(
                r'(?:Route\s*(?:of\s*Administration|of\s*administration)?)\s*[:\n]\s*([^\n]+(?:\n[^\n]+)?)',
                after_df_block,
                re.IGNORECASE
            )
            raw_route = ""
            if route_match:
                r_cand = route_match.group(1).strip()
                r_stop = re.split(r'\n\s*(?:Pharmacologic|Indications|ATC|Dosage|Adverse|Contra)', r_cand, flags=re.IGNORECASE)
                raw_route = r_stop[0].strip()

            clean_route, norm_routes = normalize_route(raw_route)

            # 3. Find Administration Instructions if present on page
            admin_match = re.search(
                r'\n\s*Administration\s*[:\n]\s*([^\n]+(?:\n[^\n]+){1,6})',
                remaining,
                re.IGNORECASE
            )
            admin_str = None
            if admin_match:
                a_cand = admin_match.group(1).strip()
                a_stop = re.split(r'\n\s*(?:Warnings|Storage|Special|Adverse|Monitoring|Contra|N\.B\.)', a_cand, flags=re.IGNORECASE)
                admin_str = a_stop[0].strip()

            # 4. Clean and split multiple dosage forms
            raw_lines = [l.strip().lstrip("•-* ") for l in raw_forms_block.split("\n") if l.strip()]
            merged_lines = []
            for l in raw_lines:
                l_lower = l.lower()
                # Skip header remnants & version stamps
                if l_lower in ("strengths", "strength", "form", "forms", "version 1.0", "version 1.0 /2025", "version 1.0 /2024", "version: 1.0"):
                    continue
                if any(l_lower.startswith(h) for h in ["route of", "pharmacologic", "indications", "atc code", "code:", "n.b.", "refer to"]):
                    continue
                
                # Check if this line is a continuation of the previous line (e.g. "and in combination with...")
                if merged_lines and (l_lower.startswith("and ") or l_lower.startswith("alone and") or l_lower.startswith("containing ") or l_lower.startswith("with ") or l_lower.startswith("or in ") or (not any(c in l_lower for c in [":", "mg", "ml", "tablet", "capsule", "syrup", "suspension", "cream", "injection", "drops", "spray", "suppository", "vial", "ampoule", "powder", "granule", "patch"]) and len(l) < 35)):
                    merged_lines[-1] = merged_lines[-1] + " " + l
                else:
                    merged_lines.append(l)

            for raw_line in merged_lines:
                if len(raw_line) < 2:
                    continue

                form_text, cleaned_raw_line, strength = extract_strength_and_form(raw_line)
                norm_form = normalize_dosage_form(form_text)
                video_rel, device_cat = classify_video_relevance(norm_form, norm_routes, generic_name=gen_name)

                extracted_rows.append({
                    "generic_name": gen_name,
                    "dosage_form_raw": cleaned_raw_line,
                    "dosage_form_normalized": norm_form,
                    "strength": strength,
                    "route_of_administration": clean_route,
                    "administration_instructions": admin_str,
                    "device_category": device_cat,
                    "exact_device_name": None, # Strictly NULL unless manually verified
                    "exact_device_verified": False,
                    "video_relevant": video_rel,
                    "source_file": file_name,
                    "source_page": page_num,
                    "active": True
                })

    return extracted_rows

def parse_otc_table_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Parses the Egyptian OTC Drug List PDF (table format) into structured dosage form rows.
    """
    doc = fitz.open(pdf_path)
    file_name = pdf_path.name
    extracted_rows: List[Dict[str, Any]] = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        page_text = page.get_text()
        cleaned = clean_extracted_text(page_text)
        
        # Split text into blocks or entries
        # OTC entries usually have: Trade Name, Active substance, Dosage form, Strength
        entries = re.split(r'\n(?=[A-Z0-9][a-zA-Z0-9\s®\-+]{2,35}\n(?:[A-Z][a-z]+|\d+))', cleaned)
        for entry in entries:
            lines = [l.strip() for l in entry.split("\n") if l.strip()]
            if len(lines) < 3:
                continue
            
            # Find active substance / dosage form lines
            trade_name = lines[0]
            if "trade name" in trade_name.lower() or "approved indication" in trade_name.lower():
                continue

            active_name = lines[1] if len(lines) > 1 else trade_name
            dosage_line = lines[2] if len(lines) > 2 else ""
            strength_line = lines[3] if len(lines) > 3 and any(c.isdigit() for c in lines[3]) else None

            # Skip table headers
            if "active" in active_name.lower() or "dosage form" in active_name.lower():
                continue

            raw_form_str = f"{dosage_line}: {strength_line}" if strength_line else dosage_line
            form_text, cleaned_raw_line, strength = extract_strength_and_form(raw_form_str)
            norm_form = normalize_dosage_form(form_text)
            clean_route, norm_routes = normalize_route("Oral" if "tablet" in norm_form or "oral" in norm_form or "capsule" in norm_form else ("Rectal" if "suppository" in norm_form else "Topical"))
            video_rel, device_cat = classify_video_relevance(norm_form, norm_routes, generic_name=active_name)

            extracted_rows.append({
                "generic_name": active_name,
                "dosage_form_raw": cleaned_raw_line if cleaned_raw_line else "Dosage form unspecified",
                "dosage_form_normalized": norm_form,
                "strength": strength or strength_line,
                "route_of_administration": clean_route,
                "administration_instructions": None,
                "device_category": device_cat,
                "exact_device_name": None,
                "exact_device_verified": False,
                "video_relevant": video_rel,
                "source_file": file_name,
                "source_page": page_num,
                "active": True
            })

    return extracted_rows

def parse_eda_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Main entrypoint that routes to formulary or OTC parser based on document type.
    """
    if "otc" in pdf_path.name.lower():
        return parse_otc_table_pdf(pdf_path)
    else:
        return parse_formulary_pdf(pdf_path)
