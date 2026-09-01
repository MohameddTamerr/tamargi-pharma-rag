def compute_rrf_scores(
    dense_results: list[dict],
    bm25_results: list[dict],
    rrf_k: int = 30,
    dense_weight: float = 0.8,
    bm25_weight: float = 0.8
) -> dict[int, float]:
    """
    Computes Reciprocal Rank Fusion (RRF) scores:
    RRF(d) = sum_{m in models} weight_m / (rrf_k + rank_m(d))
    """
    rrf_scores = {}

    for result in dense_results:
        idx = result["index"]
        rank = result["rank"]
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (dense_weight / (rrf_k + rank))

    for result in bm25_results:
        idx = result["index"]
        rank = result["rank"]
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (bm25_weight / (rrf_k + rank))

    return rrf_scores
