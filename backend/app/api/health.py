from fastapi import APIRouter
from app.rag.loader import rag_loader
from app.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Tamargi.ai RAG Backend",
        "rag_loaded": rag_loader.is_loaded,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
        "gemini_model": settings.GEMINI_MODEL
    }
