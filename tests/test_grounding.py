import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.grounding import build_evidence, build_sources_list

def test_grounding_evidence_formatting():
    mock_results = [
        {
            "file": "egypt_antimicrobial_formulary_2023.pdf",
            "page": 52,
            "chunk_id": 1,
            "rank": 1,
            "reranker_score": 2.92,
            "text": "Hypersensitivity to anidulafungin or fructose intolerance."
        }
    ]
    
    evidence_str = build_evidence(mock_results)
    assert "[E1]" in evidence_str
    assert "Source: egypt_antimicrobial_formulary_2023.pdf" in evidence_str
    assert "Page: 52" in evidence_str
    
    sources_list = build_sources_list(mock_results)
    assert len(sources_list) == 1
    assert sources_list[0]["evidenceId"] == "E1"
    assert sources_list[0]["fileName"] == "egypt_antimicrobial_formulary_2023.pdf"
    assert sources_list[0]["pageNumber"] == 52

if __name__ == "__main__":
    test_grounding_evidence_formatting()
    print("test_grounding passed!")
