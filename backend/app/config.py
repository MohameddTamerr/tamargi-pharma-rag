import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

def resolve_processed_dir() -> Path:
    """Resolves the processed data directory across Railway deployment and local development.
    
    Resolution precedence:
    1. RAG_DATA_DIR env variable (if set and exists)
    2. BASE_DIR / 'data' / 'processed' (Railway deployment context: /backend/data/processed)
    3. PROJECT_ROOT / 'data' / 'processed' (Local monorepo context: /data/processed)
    """
    env_override = os.getenv("RAG_DATA_DIR")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p.resolve()

    backend_processed = BASE_DIR / "data" / "processed"
    if backend_processed.exists():
        return backend_processed.resolve()

    repo_processed = PROJECT_ROOT / "data" / "processed"
    if repo_processed.exists():
        return repo_processed.resolve()

    return backend_processed.resolve()

PROCESSED_DIR = resolve_processed_dir()
DATA_DIR = PROCESSED_DIR.parent
CHUNKS_FILE = PROCESSED_DIR / "chunks_with_metadata.csv" if (PROCESSED_DIR / "chunks_with_metadata.csv").exists() else PROCESSED_DIR / "final_chunks.csv"
SETTINGS_FILE = PROCESSED_DIR / "best_retrieval_settings.json"
ALIASES_FILE = PROCESSED_DIR / "medication_aliases.csv"
SAFETY_RULES_FILE = PROCESSED_DIR / "final_verified_safety_rules.csv"
VIDEOS_FILE = PROCESSED_DIR / "final_video_candidates.csv"
EMBEDDINGS_CACHE_FILE = BASE_DIR / "embeddings_cache.npy" if (BASE_DIR / "embeddings_cache.npy").exists() else PROCESSED_DIR / "embeddings_cache.npy"

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    
    # BYOK (Bring Your Own Key) Security & Rate Limits
    BYOK_ENCRYPTION_KEY: str = os.getenv("BYOK_ENCRYPTION_KEY", "tamargi-pharma-rag-default-encryption-secret-key-32b")
    ALLOW_PROJECT_GEMINI_FALLBACK: bool = os.getenv("ALLOW_PROJECT_GEMINI_FALLBACK", "false").lower() in ("true", "1", "yes")
    CHAT_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("CHAT_RATE_LIMIT_PER_MINUTE", "15"))
    CHAT_DAILY_LIMIT: int = int(os.getenv("CHAT_DAILY_LIMIT", "200"))
    
    # Supabase
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Models
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    RERANKER_MODEL: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    
    # RAG Parameters
    DENSE_K: int = 40
    BM25_K: int = 40
    RRF_K: int = 60
    DENSE_WEIGHT: float = 1.0
    BM25_WEIGHT: float = 1.2
    CANDIDATE_K: int = 40
    FINAL_K: int = 5
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
