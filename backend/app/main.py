import sys
import io

# Ensure UTF-8 output across Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, chat, voice, conversations, video, patient, plans
from app.rag.loader import rag_loader
from app.rag.reranker import reranker_instance
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Initializing Tamargi.ai Hybrid RAG Models...")
    try:
        rag_loader.load()
        reranker_instance.load()
        print("[Startup] All models preloaded and ready!")
    except Exception as e:
        print(f"[Startup Warning] Preloading models failed: {e}")
    yield
    print("[Shutdown] Cleaning up server resources...")

app = FastAPI(
    title="Tamargi.ai — Explainable Medication Evidence Assistant API",
    description="Backend API wrapping Python Hybrid RAG (E5 + BM25 + RRF + CrossEncoder + Strict Gemini Grounding)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(voice.router, prefix="/api", tags=["Voice"])
app.include_router(video.router, prefix="/api/video", tags=["Video"])
app.include_router(patient.router, tags=["Patient Profile"])
app.include_router(plans.router, prefix="/api/plans", tags=["Medication Plans"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Tamargi.ai Medication Evidence Assistant API",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
