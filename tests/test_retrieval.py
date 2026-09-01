import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.rag.retrieval import retrieve
from app.language.egyptian import normalize_egyptian_query

def test_retrieval_anidulafungin():
    query = "What are the contraindications of Anidulafungin?"
    results = retrieve(query)
    
    assert len(results) > 0, "Retrieval returned empty results"
    top_result = results[0]
    
    assert "file" in top_result
    assert "page" in top_result
    assert top_result["file"] == "egypt_antimicrobial_formulary_2023.pdf"
    assert top_result["page"] == 52

def test_retrieval_egyptian_arabic():
    egyptian_query = "ايه موانع استخدام Anidulafungin؟"
    retrieval_query = normalize_egyptian_query(egyptian_query)
    
    results = retrieve(retrieval_query)
    assert len(results) > 0
    assert results[0]["file"] == "egypt_antimicrobial_formulary_2023.pdf"

if __name__ == "__main__":
    test_retrieval_anidulafungin()
    test_retrieval_egyptian_arabic()
    print("test_retrieval passed!")
