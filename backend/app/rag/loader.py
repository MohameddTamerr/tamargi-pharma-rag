import re
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from app.config import settings, PROCESSED_DIR, CHUNKS_FILE, EMBEDDINGS_CACHE_FILE, BASE_DIR

class RAGLoader:
    _instance = None

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.chunks_df: pd.DataFrame = pd.DataFrame()
        self.embedding_model: SentenceTransformer = None
        self.embeddings: np.ndarray = None
        self.bm25: BM25Okapi = None
        self.is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RAGLoader()
        return cls._instance

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text for BM25 matching.
        
        Supports both Latin (English drug names) and Arabic script.
        The original implementation only matched [a-z0-9]+, which silently
        discarded all Arabic characters, making BM25 blind to Arabic queries.
        """
        if not text:
            return []
        text_lower = text.lower()
        # Match Latin alphanumeric tokens AND Arabic character runs
        tokens = re.findall(r"[a-z0-9]+|[\u0600-\u06FF]+", text_lower)
        return tokens

    def load(self):
        if self.is_loaded:
            return

        print(f"[RAGLoader] Device: {self.device}")
        print(f"[RAGLoader] RAG data directory: {PROCESSED_DIR}")
        
        # 1. Candidate paths for Chunks CSV
        candidate_chunk_paths = [
            PROCESSED_DIR / "chunks_with_metadata.csv",
            PROCESSED_DIR / "final_chunks.csv",
            Path(CHUNKS_FILE),
            BASE_DIR.parent / "data" / "processed" / "chunks_with_metadata.csv",
            BASE_DIR.parent / "data" / "processed" / "final_chunks.csv",
        ]
        
        chunks_file_to_load = None
        for candidate in candidate_chunk_paths:
            if candidate and candidate.exists():
                chunks_file_to_load = candidate.resolve()
                break

        if not chunks_file_to_load:
            searched = "\n  - ".join(str(p) for p in candidate_chunk_paths)
            raise FileNotFoundError(
                f"[RAGLoader Error] Processed chunks file not found. Searched candidate paths:\n  - {searched}"
            )

        print(f"[RAGLoader] {chunks_file_to_load.name}: FOUND (Loading from {chunks_file_to_load})...")
        self.chunks_df = pd.read_csv(chunks_file_to_load)
        print(f"[RAGLoader] Loaded {len(self.chunks_df)} chunks.")

        # 2. Load E5 Embedding Model
        print(f"[RAGLoader] Loading embedding model: {settings.EMBEDDING_MODEL}...")
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=self.device
        )

        # 3. Build / Load Chunks Embeddings Cache
        candidate_cache_paths = [
            EMBEDDINGS_CACHE_FILE,
            BASE_DIR / "embeddings_cache.npy",
            PROCESSED_DIR / "embeddings_cache.npy",
            BASE_DIR.parent / "backend" / "embeddings_cache.npy"
        ]
        
        cache_path_to_use = None
        for c_path in candidate_cache_paths:
            if c_path and Path(c_path).exists():
                cache_path_to_use = Path(c_path).resolve()
                break

        if cache_path_to_use and cache_path_to_use.exists():
            print(f"[RAGLoader] embeddings_cache.npy: FOUND (Loading from {cache_path_to_use})...")
            self.embeddings = np.load(str(cache_path_to_use))
            print(f"[RAGLoader] embeddings: FOUND (Shape: {self.embeddings.shape})")
        else:
            print("[RAGLoader] Encoding passages for dense search...")
            passages = ["passage: " + str(text) for text in self.chunks_df["text"]]
            self.embeddings = self.embedding_model.encode(
                passages,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            save_dest = BASE_DIR / "embeddings_cache.npy"
            try:
                np.save(str(save_dest), self.embeddings)
                print(f"[RAGLoader] Embeddings cached to {save_dest}")
            except Exception as e:
                print(f"[RAGLoader] Warning: Could not cache embeddings: {e}")
            print(f"[RAGLoader] embeddings: READY (Shape: {self.embeddings.shape})")

        # 4. Build BM25 Index with metadata enrichment
        print("[RAGLoader] Tokenizing chunks for metadata-enriched BM25 search...")
        searchable_corpus = []
        for _, row in self.chunks_df.iterrows():
            c_drug = str(row.get("canonical_drug", "")).strip() if pd.notna(row.get("canonical_drug")) else ""
            mono = str(row.get("monograph_name", "")).strip() if pd.notna(row.get("monograph_name")) else ""
            sec = str(row.get("section", "")).strip() if pd.notna(row.get("section")) else ""
            raw_text = str(row.get("text", "")).strip()
            enriched_text = f"{c_drug} {mono} {sec} {raw_text}".strip()
            searchable_corpus.append(enriched_text)

        tokenized_chunks = [self.tokenize(t) for t in searchable_corpus]
        self.bm25 = BM25Okapi(tokenized_chunks)
        print("[RAGLoader] BM25 index: FOUND (READY)")

        self.is_loaded = True

rag_loader = RAGLoader.get_instance()
