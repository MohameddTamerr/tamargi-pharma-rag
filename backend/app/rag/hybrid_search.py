from typing import Optional, List
from app.rag.dense_search import dense_search
from app.rag.bm25_search import bm25_search
from app.rag.rrf import compute_rrf_scores
from app.rag.loader import rag_loader
from app.config import settings

def hybrid_search(
    query: str,
    dense_k: int = None,
    bm25_k: int = None,
    final_k: int = None,
    rrf_k: int = None,
    dense_weight: float = None,
    bm25_weight: float = None,
    candidate_indices: Optional[List[int]] = None
) -> list[dict]:
    """
    Runs dense vector search and sparse BM25 search, fusing results via RRF.
    If candidate_indices is provided, fuses results within that scoped pool.
    """
    dense_k = dense_k or settings.DENSE_K
    bm25_k = bm25_k or settings.BM25_K
    final_k = final_k or settings.CANDIDATE_K
    rrf_k = rrf_k or settings.RRF_K
    dense_weight = dense_weight or settings.DENSE_WEIGHT
    bm25_weight = bm25_weight or settings.BM25_WEIGHT

    if not rag_loader.is_loaded:
        rag_loader.load()

    dense_results = dense_search(query, top_k=dense_k, candidate_indices=candidate_indices)
    bm25_results = bm25_search(query, top_k=bm25_k, candidate_indices=candidate_indices)

    rrf_scores = compute_rrf_scores(
        dense_results,
        bm25_results,
        rrf_k=rrf_k,
        dense_weight=dense_weight,
        bm25_weight=bm25_weight
    )

    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for rank, (index, score) in enumerate(sorted_results[:final_k], start=1):
        row = rag_loader.chunks_df.iloc[index]
        results.append({
            "index": int(index),
            "rank": rank,
            "rrf_score": float(score),
            "file": str(row["file"]),
            "source_file": str(row.get("source_file", row["file"])),
            "page": int(row["page"]),
            "chunk_id": int(row["chunk_id"]),
            "canonical_drug": str(row.get("canonical_drug", "")),
            "monograph_name": str(row.get("monograph_name", "")),
            "section": str(row.get("section", "other")),
            "text": str(row["text"])
        })

    return results
