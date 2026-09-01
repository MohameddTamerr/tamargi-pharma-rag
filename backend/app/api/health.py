from fastapi import APIRouter
from app.rag.loader import rag_loader
from app.config import settings, PROCESSED_DIR

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Tamargi.ai RAG Backend",
        "rag_loaded": bool(rag_loader.is_loaded),
        "rag_data_dir": str(PROCESSED_DIR),
        "chunks_count": len(rag_loader.chunks_df) if rag_loader.is_loaded else 0,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
        "gemini_model": settings.GEMINI_MODEL
    }
