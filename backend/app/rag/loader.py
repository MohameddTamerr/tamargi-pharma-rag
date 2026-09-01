import re
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from app.config import settings, CHUNKS_FILE

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
        
        # 1. Load Chunks CSV (Prefer chunks_with_metadata.csv if present)
        metadata_file = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed" / "chunks_with_metadata.csv"
        if metadata_file.exists():
            print(f"[RAGLoader] Loading metadata-enriched chunks from {metadata_file}...")
            self.chunks_df = pd.read_csv(metadata_file)
        elif Path(CHUNKS_FILE).exists():
            print(f"[RAGLoader] Loading chunks from {CHUNKS_FILE}...")
            self.chunks_df = pd.read_csv(CHUNKS_FILE)
        else:
            raise FileNotFoundError(f"Processed chunks file not found at {CHUNKS_FILE} or {metadata_file}")
        
        print(f"[RAGLoader] Loaded {len(self.chunks_df)} chunks.")

        # 2. Load E5 Embedding Model
        print(f"[RAGLoader] Loading embedding model: {settings.EMBEDDING_MODEL}...")
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=self.device
        )

        # 3. Build Chunks Embeddings
        cache_path = Path(__file__).resolve().parent.parent.parent / "embeddings_cache.npy"
        if cache_path.exists():
            print(f"[RAGLoader] Loading cached embeddings from {cache_path}...")
            self.embeddings = np.load(str(cache_path))
            print(f"[RAGLoader] Loaded cached embeddings. Shape: {self.embeddings.shape}")
        else:
            print("[RAGLoader] Encoding passages for dense search...")
            passages = ["passage: " + str(text) for text in self.chunks_df["text"]]
            self.embeddings = self.embedding_model.encode(
                passages,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            try:
                np.save(str(cache_path), self.embeddings)
                print(f"[RAGLoader] Embeddings cached to {cache_path}")
            except Exception as e:
                print(f"[RAGLoader] Warning: Could not cache embeddings: {e}")
            print(f"[RAGLoader] Embeddings ready. Shape: {self.embeddings.shape}")

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
        print("[RAGLoader] BM25 Index ready.")

        self.is_loaded = True

rag_loader = RAGLoader.get_instance()
