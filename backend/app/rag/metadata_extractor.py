import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from app.normalization.section_normalizer import detect_section_in_text, normalize_section_heading
from app.safety.normalizer import normalize_medication_name

def clean_monograph_title(raw_title: str) -> str:
    """Cleans header artifact prefixes from detected monograph title."""
    t = raw_title.strip()
    # Strip common Egyptian header prefixes
    t = re.sub(r"^.*?Formulary\s*[-–:]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?system\s*[-–:]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?medicines\s*[-–:]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?disorders\s*[-–:]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?Inhibitors\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?Antagonists\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?Drugs\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^.*?Antifolate\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^[0-9\.\s\-A-Za-z]+?\s+(?=[A-Z][a-z])", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_monograph_start(text: str, filename: str, page: int) -> Optional[str]:
    """
    Detects if a chunk represents the beginning of a drug monograph.
    """
    # 1. Pattern: [Drug Name] Generic Name [Drug Name]
    m1 = re.search(r"([A-Z0-9\.\s\-]{2,40}?)\s+Generic\s+Name", text[:350], re.IGNORECASE)
    if m1:
        title = clean_monograph_title(m1.group(1))
        if len(title) > 2 and not any(k in title.lower() for k in ["table of contents", "preface", "index", "introduction"]):
            return title

    # 2. Pattern: Generic Name : [Drug Name]
    m2 = re.search(r"Generic\s+Name\s*[:\-]\s*([A-Za-z0-9\s\-]{3,40})", text[:350], re.IGNORECASE)
    if m2:
        title = clean_monograph_title(m2.group(1))
        if len(title) > 2:
            return title

    # 3. Pattern: Monograph Title in Header Lines
    lines = [l.strip() for l in text[:250].split("\n") if l.strip()]
    for line in lines[:2]:
        m3 = re.match(r"^([A-Z][a-zA-Z\s\-]{3,35})\s+Monograph", line, re.IGNORECASE)
        if m3:
            return clean_monograph_title(m3.group(1))

    return None

def extract_metadata_for_corpus(chunks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches raw extracted chunks with lightweight hierarchical metadata:
    - canonical_drug
    - monograph_name
    - section (with continuation inheritance)
    - previous_chunk_id
    - next_chunk_id
    """
    enriched_rows = []

    for fname, grp in chunks_df.groupby("file", sort=False):
        grp_sorted = grp.sort_values(by=["page", "chunk_id"]).copy()
        n_chunks = len(grp_sorted)

        # State machine tracking for active monograph & section
        current_monograph: Optional[str] = None
        current_canonical_drug: Optional[str] = None
        current_section: str = "other"

        # Special document defaults
        is_high_alert_doc = "high_alert" in fname.lower()
        is_do_not_crush_doc = "do_not_crush" in fname.lower()
        is_otc_doc = "otc" in fname.lower()

        if is_high_alert_doc:
            current_monograph = "High Alert Medications List"
            current_section = "high_alert"
        elif is_do_not_crush_doc:
            current_monograph = "Do Not Crush Medications List"
            current_section = "do_not_crush"
        elif is_otc_doc:
            current_monograph = "Egyptian OTC Drug List"
            current_section = "indications"

        for idx, (original_idx, row) in enumerate(grp_sorted.iterrows()):
            cid = int(row["chunk_id"])
            page = int(row["page"])
            text = str(row["text"])
            wc = int(row.get("word_count", len(text.split())))

            # Check if this chunk starts a new monograph
            if not (is_high_alert_doc or is_do_not_crush_doc or is_otc_doc):
                new_mono = extract_monograph_start(text, fname, page)
                if new_mono:
                    current_monograph = new_mono
                    canon, _ = normalize_medication_name(new_mono)
                    current_canonical_drug = canon
                    current_section = "indications" # default start of monograph

                # Check if this chunk starts a new section
                detected_sec = detect_section_in_text(text)
                if detected_sec:
                    current_section = detected_sec
                elif not current_section:
                    current_section = "other"
            else:
                if is_high_alert_doc:
                    current_section = "high_alert"
                elif is_do_not_crush_doc:
                    current_section = "do_not_crush"
                elif is_otc_doc:
                    detected_sec = detect_section_in_text(text)
                    current_section = detected_sec if detected_sec else "indications"

            # Compute neighbor chunk links
            prev_cid = grp_sorted.iloc[idx - 1]["chunk_id"] if idx > 0 else -1
            next_cid = grp_sorted.iloc[idx + 1]["chunk_id"] if idx < n_chunks - 1 else -1

            # For OTC document, extract active ingredient if present in line
            row_canon_drug = current_canonical_drug
            if is_otc_doc:
                m_active = re.search(r"(?:Active|Active Ingredient)\s*[:\-]?\s*([A-Za-z\s\/\+]+?)(?:Dosage|Form|Strength|\n)", text, re.IGNORECASE)
                if m_active:
                    raw_act = m_active.group(1).strip()
                    c_act, _ = normalize_medication_name(raw_act)
                    if c_act:
                        row_canon_drug = c_act

            enriched_rows.append({
                "chunk_id": cid,
                "file": fname,
                "source_file": fname,
                "page": page,
                "canonical_drug": row_canon_drug if row_canon_drug else "",
                "monograph_name": current_monograph if current_monograph else "",
                "section": current_section,
                "previous_chunk_id": int(prev_cid),
                "next_chunk_id": int(next_cid),
                "text": text,
                "word_count": wc
            })

    return pd.DataFrame(enriched_rows)
