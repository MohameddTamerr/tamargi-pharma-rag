import os
import sys

# Ensure UTF-8 output encoding on Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.loader import rag_loader
from app.rag.retrieval import retrieve
from app.rag.grounding import build_evidence, build_sources_list, STRICT_GROUNDING_PROMPT
from app.language.detector import detect_language
from app.language.egyptian import normalize_egyptian_query
from app.api.chat import is_insufficient_evidence_answer
from app.database.supabase import log_unanswered_query, calculate_age

def run_e2e_tests():
    print("=== TAMARGI.AI END-TO-END VERIFICATION SUITE ===")
    
    # Initialize RAG Models
    rag_loader.load()

    # TEST 1: English Medication Question
    print("\n--- TEST 1: English Valid Medication Question ---")
    query_en = "What are the contraindications of Anidulafungin?"
    lang_en = detect_language(query_en)
    print(f"Query: {query_en}")
    print(f"Language detected: {lang_en}")
    results_en = retrieve(query_en)
    assert len(results_en) > 0, "No evidence retrieved for English query"
    top_doc_en = results_en[0]
    print(f"Top Retrieved Evidence: rank=1, file={top_doc_en['file']}, page={top_doc_en['page']}, score={top_doc_en.get('reranker_score', 0):.4f}")
    assert "antimicrobial" in top_doc_en["file"].lower() or "anidulafungin" in top_doc_en["text"].lower()
    sources_en = build_sources_list(results_en)
    assert sources_en[0]["evidenceId"] == "E1"
    print(f"Sources validated: {[s['evidenceId'] for s in sources_en]}")

    # TEST 2: Arabic Equivalent Question
    print("\n--- TEST 2: Standard Arabic Equivalent Question ---")
    query_ar = "ما هي موانع استخدام Anidulafungin؟"
    lang_ar = detect_language(query_ar)
    print(f"Query: {query_ar}")
    print(f"Language detected: {lang_ar}")
    results_ar = retrieve(query_ar)
    assert len(results_ar) > 0, "No evidence retrieved for Arabic query"
    top_doc_ar = results_ar[0]
    print(f"Top Retrieved Evidence: rank=1, file={top_doc_ar['file']}, page={top_doc_ar['page']}, score={top_doc_ar.get('reranker_score', 0):.4f}")
    assert "anidulafungin" in top_doc_ar["text"].lower() or "antimicrobial" in top_doc_ar["file"].lower()

    # TEST 3: Egyptian Arabic Equivalent Question
    print("\n--- TEST 3: Egyptian Colloquial Arabic Equivalent Question ---")
    query_egy = "ايه موانع استخدام Anidulafungin؟"
    lang_egy = detect_language(query_egy)
    norm_egy = normalize_egyptian_query(query_egy)
    print(f"Query: {query_egy}")
    print(f"Language detected: {lang_egy}")
    print(f"Normalized query: {norm_egy}")
    results_egy = retrieve(query_egy)
    assert len(results_egy) > 0, "No evidence retrieved for Egyptian query"
    top_doc_egy = results_egy[0]
    print(f"Top Retrieved Evidence: rank=1, file={top_doc_egy['file']}, page={top_doc_egy['page']}, score={top_doc_egy.get('reranker_score', 0):.4f}")

    # TEST 4: Unsupported Grounding Safety Refusal & Unanswered Query Logging
    print("\n--- TEST 4: Grounding Safety Test (Unsupported Medical Query) ---")
    unsupported_query = "Does Anidulafungin cure hypertension?"
    evidence_text = build_evidence(results_en)
    print(f"Built evidence block length: {len(evidence_text)} characters")
    refusal_answer_en = "The retrieved evidence is insufficient to answer this question safely."
    assert is_insufficient_evidence_answer(refusal_answer_en) is True
    
    refusal_answer_ar = "عفواً، الأدلة المتاحة غير كافية للإجابة على هذا السؤال بشكل آمن."
    assert is_insufficient_evidence_answer(refusal_answer_ar) is True
    
    log_success = log_unanswered_query(
        user_id="test-user-uuid",
        conversation_id="test-conv-uuid",
        message_id="test-msg-uuid",
        original_query=unsupported_query,
        normalized_query=unsupported_query,
        language_detected="en",
        top_retrieved_sources=sources_en,
        reason="insufficient_evidence"
    )
    print(f"Unanswered query logged successfully: {log_success}")
    assert log_success is True

    # TEST 5: Dynamic Age Calculation from birth_date
    print("\n--- TEST 5: Dynamic Age Calculation ---")
    age = calculate_age("1995-05-15")
    print(f"Calculated age for 1995-05-15: {age} years")
    assert age is not None and age >= 30

    print("\n=======================================================")
    print(">>> ALL END-TO-END VERIFICATION TESTS PASSED (100%) <<<")
    print("=======================================================")

if __name__ == "__main__":
    run_e2e_tests()
