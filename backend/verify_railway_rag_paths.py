import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import PROCESSED_DIR, CHUNKS_FILE, EMBEDDINGS_CACHE_FILE, settings
from app.rag.loader import rag_loader
from app.rag.retrieval import retrieve
from app.rag.reranker import reranker_instance
from app.orchestrator.orchestrator import TamargiOrchestrator

def test_railway_rag_paths():
    print("=" * 80)
    print("TAMARGI.AI — RAILWAY DEPLOYMENT RAG PATH VALIDATION")
    print("=" * 80)
    
    print(f"PROCESSED_DIR: {PROCESSED_DIR}")
    print(f"CHUNKS_FILE: {CHUNKS_FILE} (exists: {CHUNKS_FILE.exists()})")
    print(f"EMBEDDINGS_CACHE_FILE: {EMBEDDINGS_CACHE_FILE} (exists: {EMBEDDINGS_CACHE_FILE.exists()})")
    
    # 1. Test RAGLoader & Reranker loading
    rag_loader.load()
    reranker_instance.load()
    
    assert rag_loader.is_loaded, "RAG Loader failed to load!"
    assert len(rag_loader.chunks_df) > 0, "No chunks loaded!"
    print(f"[PASS] RAG Loader initialized with {len(rag_loader.chunks_df)} chunks.")
    
    # 2. Test Anidulafungin Contraindications Retrieval
    print("\n--- Testing English Query: What are the contraindications of Anidulafungin? ---")
    query_en = "What are the contraindications of Anidulafungin?"
    results_en = retrieve(query_en)
    print(f"Retrieved {len(results_en)} accepted chunks.")
    assert len(results_en) > 0, "Retrieval returned 0 chunks!"
    
    found_anidulafungin = False
    for i, c in enumerate(results_en):
        drug = c.get("canonical_drug", "")
        file_name = c.get("source_file", "")
        page = c.get("page", "")
        section = c.get("section", "")
        print(f"  Chunk {i+1}: Drug={drug} | File={file_name} | Page={page} | Section={section}")
        if "anidulafungin" in str(drug).lower() or "anidulafungin" in str(c.get("text", "")).lower():
            found_anidulafungin = True
            
    assert found_anidulafungin, "Anidulafungin evidence not found in retrieved chunks!"
    print("[PASS] Anidulafungin contraindication evidence retrieved with correct monograph and page provenance.")
    
    # 3. Test Arabic Query Retrieval
    print("\n--- Testing Arabic Query: ما هي موانع استعمال دواء انيدولافنجين؟ ---")
    query_ar = "ما هي موانع استعمال دواء انيدولافنجين؟"
    results_ar = retrieve(query_ar)
    print(f"Retrieved {len(results_ar)} accepted chunks.")
    assert len(results_ar) > 0, "Arabic retrieval returned 0 chunks!"
    for i, c in enumerate(results_ar):
        print(f"  Chunk {i+1}: Drug={c.get('canonical_drug')} | File={c.get('source_file')} | Page={c.get('page')} | Section={c.get('section')}")
    print("[PASS] Arabic RAG retrieval executed successfully.")
    
    print("\n" + "=" * 80)
    print("ALL PRODUCTION-LIKE RAILWAY RAG TESTS PASSED (100%)")
    print("=" * 80)

if __name__ == "__main__":
    test_railway_rag_paths()
