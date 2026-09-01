from typing import List, Dict, Any, Optional, Set
import re

def is_text_near_duplicate(text1: str, text2: str, threshold: float = 0.85) -> bool:
    """Checks if two chunks have nearly identical text content (Jaccard similarity)."""
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return False
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return (intersection / union) >= threshold

def filter_and_accept_evidence(
    candidates: List[Dict[str, Any]],
    target_medications: Optional[List[str]] = None,
    target_section: Optional[str] = None,
    max_evidence_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Acceptance layer that:
    1. Enforces entity consistency (rejects unrelated drugs when target drug is known).
    2. Filters out near-duplicate chunks.
    3. Enforces page-diversity within the candidate pool so Top-5 covers multiple distinct sections/pages.
    4. Marks used_in_answer = True for accepted evidence.
    """
    if not candidates:
        return []

    target_meds = [m.lower().strip() for m in target_medications if m] if target_medications else []
    accepted: List[Dict[str, Any]] = []
    seen_slots: Set[str] = set()
    page_counts: Dict[str, int] = {}

    # Pass 1: Select top chunk per (file, page) to maximize section/page diversity
    for cand in candidates:
        c_file = str(cand.get("file", cand.get("source_file", "")))
        c_page = int(cand.get("page", 0))
        c_cid = int(cand.get("chunk_id", 0))
        c_drug = str(cand.get("canonical_drug", "")).lower().strip()
        c_text = str(cand.get("text", ""))

        # Entity consistency check
        if target_meds:
            is_target_drug_mono = any(tm in c_drug or c_drug in tm for tm in target_meds)
            mentions_target_drug = any(tm in c_text.lower() for tm in target_meds)
            is_special_doc = any(sd in c_file.lower() for sd in ["high_alert", "do_not_crush", "otc"])

            if not (is_target_drug_mono or mentions_target_drug or is_special_doc):
                continue

        slot_key = f"{c_file}:{c_page}:{c_cid}"
        page_key = f"{c_file}:{c_page}"

        if slot_key in seen_slots:
            continue

        # Allow at most 1 chunk per page in Pass 1 to maximize document/section diversity
        if page_counts.get(page_key, 0) >= 1:
            continue

        # Near-duplicate check
        is_dup = False
        for acc in accepted:
            if acc.get("file") == c_file and abs(int(acc.get("page", 0)) - c_page) <= 1:
                if is_text_near_duplicate(c_text, acc.get("text", "")):
                    is_dup = True
                    break
        if is_dup:
            continue

        cand_accepted = cand.copy()
        cand_accepted["used_in_answer"] = True
        cand_accepted["accepted_rank"] = len(accepted) + 1
        accepted.append(cand_accepted)
        seen_slots.add(slot_key)
        page_counts[page_key] = page_counts.get(page_key, 0) + 1

        if len(accepted) >= max_evidence_count:
            break

    # Pass 2: Fill any remaining slots up to max_evidence_count
    if len(accepted) < max_evidence_count:
        for cand in candidates:
            c_file = str(cand.get("file", cand.get("source_file", "")))
            c_page = int(cand.get("page", 0))
            c_cid = int(cand.get("chunk_id", 0))
            slot_key = f"{c_file}:{c_page}:{c_cid}"
            page_key = f"{c_file}:{c_page}"

            if slot_key not in seen_slots:
                cand_accepted = cand.copy()
                cand_accepted["used_in_answer"] = True
                cand_accepted["accepted_rank"] = len(accepted) + 1
                accepted.append(cand_accepted)
                seen_slots.add(slot_key)
                page_counts[page_key] = page_counts.get(page_key, 0) + 1
                if len(accepted) >= max_evidence_count:
                    break

    return accepted
