import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.api.chat import is_insufficient_evidence_answer
from app.database.supabase import log_unanswered_query, IN_MEMORY_UNANSWERED_LOG

def test_insufficient_answer_is_stored():
    IN_MEMORY_UNANSWERED_LOG.clear()
    
    insufficient_answer = "The retrieved evidence is insufficient to answer this question safely."
    assert is_insufficient_evidence_answer(insufficient_answer) == True
    
    original_query = "Does Anidulafungin cure hypertension?"
    sources = [
        {"fileName": "egypt_antimicrobial_formulary_2023.pdf", "pageNumber": 52, "chunkId": 1, "rank": 1, "score": 0.12}
    ]
    
    if is_insufficient_evidence_answer(insufficient_answer):
        log_unanswered_query(
            original_query=original_query,
            normalized_query=original_query,
            language_detected="en",
            user_id="test-user-id",
            top_sources=sources,
            reason="insufficient_evidence"
        )
    
    assert len(IN_MEMORY_UNANSWERED_LOG) == 1, "Expected insufficient query to be logged"
    logged = IN_MEMORY_UNANSWERED_LOG[0]
    assert logged["original_query"] == original_query
    assert logged["reason"] == "insufficient_evidence"
    assert len(logged["top_retrieved_sources"]) == 1
    assert logged["top_retrieved_sources"][0]["file_name"] == "egypt_antimicrobial_formulary_2023.pdf"
    assert "excerpt" not in logged["top_retrieved_sources"][0], "Excerpt text should NOT be stored in metadata JSON"

def test_normal_answer_is_not_stored():
    IN_MEMORY_UNANSWERED_LOG.clear()
    
    normal_answer = "Based on the retrieved evidence, the contraindications for Anidulafungin are hypersensitivity [E1]."
    assert is_insufficient_evidence_answer(normal_answer) == False
    
    original_query = "What are the contraindications of Anidulafungin?"
    sources = [
        {"fileName": "egypt_antimicrobial_formulary_2023.pdf", "pageNumber": 52, "chunkId": 1, "rank": 1, "score": 2.92}
    ]
    
    if is_insufficient_evidence_answer(normal_answer):
        log_unanswered_query(
            original_query=original_query,
            normalized_query=original_query,
            language_detected="en",
            user_id="test-user-id",
            top_sources=sources
        )
    
    assert len(IN_MEMORY_UNANSWERED_LOG) == 0, "Normal answer should NOT be logged into unanswered_queries"

if __name__ == "__main__":
    test_insufficient_answer_is_stored()
    test_normal_answer_is_not_stored()
    print("ALL UNANSWERED_QUERIES TESTS PASSED SUCCESSFULLY!")
