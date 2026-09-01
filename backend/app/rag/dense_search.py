from typing import Optional, List
import numpy as np
from app.rag.loader import rag_loader
from app.config import settings

def dense_search(query: str, top_k: int = None, candidate_indices: Optional[List[int]] = None) -> list[dict]:
    """
    Encodes query with 'query: ' prefix using intfloat/multilingual-e5-base
    and calculates cosine similarity against passage embeddings matrix.
    If candidate_indices is provided, computes rankings within the candidate pool.
    """
    if top_k is None:
        top_k = settings.DENSE_K

    if not rag_loader.is_loaded:
        rag_loader.load()

    query_embedding = rag_loader.embedding_model.encode(
        ["query: " + query],
        normalize_embeddings=True
    )[0]

    scores = rag_loader.embeddings @ query_embedding

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
            "dense_score": float(scores[index])
        })

    return results
