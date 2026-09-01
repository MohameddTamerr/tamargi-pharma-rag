from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank_results
from app.rag.loader import rag_loader
from app.rag.acceptance import filter_and_accept_evidence
from app.config import settings
from app.normalization.medication_resolver import extract_all_medications
from app.normalization.query_translator import detect_query_section

FORMULARY_PRIMARY_MAP = {
    "warfarin": "egypt_blood_disorders_formulary_2025.pdf",
    "enoxaparin": "egypt_blood_disorders_formulary_2025.pdf",
    "heparin": "egypt_blood_disorders_formulary_2025.pdf",
    "omeprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "pantoprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "furosemide": "egypt_cardiovascular_formulary_2024.pdf",
    "spironolactone": "egypt_cardiovascular_formulary_2024.pdf",
    "bisoprolol": "egypt_cardiovascular_formulary_2024.pdf",
    "captopril": "egypt_cardiovascular_formulary_2024.pdf",
    "propranolol": "egypt_cardiovascular_formulary_2024.pdf",
    "nitroglycerin": "egypt_cardiovascular_formulary_2024.pdf",
    "clopidogrel": "egypt_cardiovascular_formulary_2024.pdf",
    "atorvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "simvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "amoxicillin": "egypt_antimicrobial_formulary_2023.pdf",
    "ciprofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "levofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "clarithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "azithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "sulfamethoxazole": "egypt_antimicrobial_formulary_2023.pdf",
    "dexamethasone": "egypt_endocrine_formulary_2024.pdf",
    "metformin": "egypt_endocrine_formulary_2024.pdf",
    "methotrexate": "egypt_conventional_anticancer_formulary_2024.pdf",
    "capecitabine": "egypt_targeted_anticancer_formulary_2025.pdf",
    "sildenafil": "egypt_cardiovascular_formulary_2024.pdf",
    "ibuprofen": "egypt_blood_disorders_formulary_2025.pdf",
    "paracetamol": "egypt_otc_drug_list_2026.pdf",
    "aspirin": "egypt_otc_drug_list_2026.pdf",
    "acetylsalicylic acid": "egypt_otc_drug_list_2026.pdf"
}

def get_candidate_scope_indices(
    target_medications: Optional[List[str]],
    target_section: Optional[str],
    query_lower: str
) -> Optional[List[int]]:
    """
    Stage 1 Scope:
    Identifies candidate chunk indices belonging to the target medication monograph(s),
    relevant sections, or specialized documents (High-Alert, Do-Not-Crush, OTC).
    Returns None if no specific scope is detected (triggering global retrieval).
    """
    if not rag_loader.is_loaded:
        rag_loader.load()

    df = rag_loader.chunks_df
    candidate_indices = set()

    is_ha = any(k in query_lower for k in ["high alert", "high-alert", "عالي الخطورة", "عالية الخطورة"])
    is_dnc = any(k in query_lower for k in ["do not crush", "crush", "طحن", "كسر", "extended release", "enteric coated"])
    is_otc = any(k in query_lower for k in ["otc", "over the counter", "الجرعة القصوى", "بدون وصفة"])

    # 1. Specialized document scope
    if is_ha:
        ha_idx = df[df["file"].str.contains("high_alert", case=False, na=False)].index.tolist()
        candidate_indices.update(ha_idx)
        return sorted(list(candidate_indices))

    if is_dnc:
        dnc_idx = df[df["file"].str.contains("do_not_crush", case=False, na=False)].index.tolist()
        candidate_indices.update(dnc_idx)
        return sorted(list(candidate_indices))

    if is_otc:
        otc_idx = df[df["file"].str.contains("otc", case=False, na=False)].index.tolist()
        candidate_indices.update(otc_idx)
        return sorted(list(candidate_indices))

    # 2. Medication monograph scope
    if target_medications:
        for med in target_medications:
            m_clean = med.lower().strip()
            exp_file = FORMULARY_PRIMARY_MAP.get(m_clean, "")

            # A. Exact matching canonical_drug chunks in the primary formulary
            if exp_file:
                m_rows = df[(df["canonical_drug"].astype(str).str.lower() == m_clean) & (df["file"] == exp_file)]
                if m_rows.empty:
                    m_rows = df[(df["file"] == exp_file) & (df["text"].astype(str).str.lower().str.contains(m_clean, na=False))]
            else:
                m_rows = df[df["canonical_drug"].astype(str).str.lower() == m_clean]
                if m_rows.empty:
                    m_rows = df[df["canonical_drug"].astype(str).str.lower().str.contains(m_clean, na=False)]

            if not m_rows.empty:
                # Include full contiguous monograph page window (min_page-2 to max_page+2)
                min_p = max(1, int(m_rows["page"].min()) - 2)
                max_p = int(m_rows["page"].max()) + 2
                f_name = m_rows.iloc[0]["file"]
                range_idx = df[(df["file"] == f_name) & (df["page"] >= min_p) & (df["page"] <= max_p)].index.tolist()
                candidate_indices.update(range_idx)
            else:
                sub_idx = df[df["text"].astype(str).str.lower().str.contains(m_clean, na=False)].index.tolist()
                candidate_indices.update(sub_idx[:50])

    if candidate_indices:
        return sorted(list(candidate_indices))

    return None

def retrieve(
    query: str,
    target_medications: Optional[List[str]] = None,
    target_section: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Hierarchical Two-Stage Retrieval Pipeline:
    Stage 1: Scope Identification (Monograph, Section, Specialized Doc)
    Stage 2: Scoped Hybrid Retrieval (Dense E5 + BM25 -> RRF) with Global Fallback
    Stage 3: Contextual CrossEncoder Reranking
    Stage 4: Controlled Neighbor Chunk Expansion
    Stage 5: Evidence Acceptance & Duplicate Filtering
    """
    if not rag_loader.is_loaded:
        rag_loader.load()

    # 1. Resolve target entities if not passed
    if target_medications is None:
        med_objs = extract_all_medications(query)
        target_medications = [m.canonical_generic for m in med_objs if m.canonical_generic]

    if target_section is None:
        target_section = detect_query_section(query)

    q_lower = query.lower()

    # 2. Stage 1: Scope Identification
    scope_indices = get_candidate_scope_indices(target_medications, target_section, q_lower)

    # 3. Stage 2: Retrieve within Scope (or Global Fallback if < 10 candidates)
    if scope_indices is not None and len(scope_indices) >= 5:
        scoped_pool_k = min(len(scope_indices), 60)
        candidates = hybrid_search(
            query,
            dense_k=scoped_pool_k,
            bm25_k=scoped_pool_k,
            final_k=scoped_pool_k,
            rrf_k=settings.RRF_K,
            dense_weight=settings.DENSE_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT,
            candidate_indices=scope_indices
        )
    else:
        # Global corpus search fallback
        candidates = hybrid_search(
            query,
            dense_k=settings.DENSE_K,
            bm25_k=settings.BM25_K,
            final_k=settings.CANDIDATE_K,
            rrf_k=settings.RRF_K,
            dense_weight=settings.DENSE_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT,
            candidate_indices=None
        )

    # 4. Stage 3: Contextual CrossEncoder Reranking
    rerank_pool_k = len(candidates)
    reranked = rerank_results(
        query=query,
        results=candidates,
        top_k=rerank_pool_k,
        target_medications=target_medications,
        target_section=target_section
    )

    # 5. Stage 4: Controlled Neighbor Chunk Expansion
    if reranked and reranked[0].get("reranker_score", 0) > -2.0:
        top_hit = reranked[0]
        top_idx = top_hit.get("index")
        seen_chunk_ids = {int(c.get("chunk_id", 0)) for c in reranked}

        if top_idx is not None and 0 <= top_idx < len(rag_loader.chunks_df):
            for offset in [1, -1, 2]:
                n_idx = top_idx + offset
                if 0 <= n_idx < len(rag_loader.chunks_df):
                    n_row = rag_loader.chunks_df.iloc[n_idx]
                    same_file = str(n_row["file"]).lower() == str(top_hit.get("file", "")).lower()
                    nearby_page = abs(int(n_row["page"]) - int(top_hit.get("page", 0))) <= 1

                    if same_file and nearby_page:
                        n_cid = int(n_row["chunk_id"])
                        if n_cid not in seen_chunk_ids:
                            n_item = {
                                "index": int(n_idx),
                                "file": str(n_row["file"]),
                                "source_file": str(n_row.get("source_file", n_row["file"])),
                                "page": int(n_row["page"]),
                                "chunk_id": n_cid,
                                "canonical_drug": str(n_row.get("canonical_drug", "")),
                                "monograph_name": str(n_row.get("monograph_name", "")),
                                "section": str(n_row.get("section", "other")),
                                "text": str(n_row["text"]),
                                "rrf_score": float(top_hit.get("rrf_score", 0.0)) * 0.9,
                                "reranker_score": float(top_hit.get("reranker_score", 0.0)) - 0.05 * abs(offset)
                            }
                            reranked.append(n_item)
                            seen_chunk_ids.add(n_cid)

    # Sort after neighbor expansion
    reranked = sorted(reranked, key=lambda x: x.get("reranker_score", 0.0), reverse=True)

    # 6. Stage 5: Evidence Acceptance & Deduplication Layer
    accepted = filter_and_accept_evidence(
        candidates=reranked,
        target_medications=target_medications,
        target_section=target_section,
        max_evidence_count=settings.FINAL_K
    )

    return accepted
