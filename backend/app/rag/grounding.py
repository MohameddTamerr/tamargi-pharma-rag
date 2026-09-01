STRICT_GROUNDING_PROMPT = """
You are Tamargi.ai, an Egyptian medication and pharmacy evidence assistant.

Core Rules:
1. Grounding: Answer strictly from the provided retrieved evidence. Do not guess, speculate, or invent citations.
2. Citations: Every clinical or medication fact must be cited using [E1], [E2], etc.
3. Language & Tone: Match the user's dialect (Egyptian Arabic, Standard Arabic, or English) warmly, naturally, and accurately.
4. Symptom & Medication Inquiries: When a user asks about common symptoms (e.g., cold/flu برد, heartburn حموضة/حرقان, headache صداع) or medications, present the approved Egyptian OTC medications, active ingredients, dosage forms, strengths, and indications found in the retrieved evidence with citations [E1], [E2].
5. Insufficient Evidence: If and only if the retrieved evidence does not contain any relevant drug, indication, or clinical data for the query, answer:
   - In Arabic / Egyptian: "عفواً، الأدلة المتاحة غير كافية للإجابة على هذا السؤال بشكل آمن."
   - In English: "The retrieved evidence is insufficient to answer this question safely."
""".strip()

def build_evidence(results: list[dict]) -> str:
    """Builds evidence block string for Gemini prompt."""
    blocks = []
    for i, result in enumerate(results, start=1):
        block = (
            f"[E{i}]\n"
            f"Source: {result['file']}\n"
            f"Page: {result['page']}\n"
            f"Text: {result['text']}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)

def build_sources_list(results: list[dict]) -> list[dict]:
    """Builds structured verified metadata sources list for frontend UI and Supabase."""
    sources = []
    for i, result in enumerate(results, start=1):
        sources.append({
            "evidenceId": f"E{i}",
            "fileName": result["file"],
            "pageNumber": result["page"],
            "chunkId": result["chunk_id"],
            "rank": i,
            "score": result.get("reranker_score", result.get("rrf_score", 0.0)),
            "excerpt": result["text"]
        })
    return sources
