from typing import Optional, List
import numpy as np
from app.rag.loader import rag_loader
from app.config import settings

def bm25_search(query: str, top_k: int = None, candidate_indices: Optional[List[int]] = None) -> list[dict]:
    """
    Tokenizes query and computes BM25Okapi relevance scores against chunk index.
    If candidate_indices is provided, computes rankings within the candidate pool.
    """
    if top_k is None:
        top_k = settings.BM25_K

    if not rag_loader.is_loaded:
        rag_loader.load()

    query_tokens = rag_loader.tokenize(query)
    scores = np.array(rag_loader.bm25.get_scores(query_tokens))

    if candidate_indices is not None and len(candidate_indices) > 0:
        cand_arr = np.array(candidate_indices)
        cand_scores = scores[cand_arr]
        rel_top = np.argsort(cand_scores)[::-1][:top_k]
        top_indices = cand_arr[rel_top]
    else:
        top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for rank, index in enumerate(top_indices, start=1):
        results.append({
            "index": int(index),
            "rank": rank,
            "bm25_score": float(scores[index])
        })

    return results
