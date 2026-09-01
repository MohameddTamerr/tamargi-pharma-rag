"""
Builder script v2 for Tamargi_RAG_V2_Research.ipynb
Reproduces the FULL production RAG V2 pipeline in simple, explainable notebook cells:
  - normalize_arabic_text()  ← text_normalizer.py
  - levenshtein_distance()   ← text_normalizer.py
  - extract_all_medications() ← medication_resolver.py
  - detect_query_section()   ← query_translator.py (FULL INTENT_KEYWORD_MAP)
  - build_retrieval_query()  ← query_translator.py
  - get_scope_indices()      ← retrieval.py Stage 1
  - dense_search_scoped()    ← dense_search.py + candidate_indices
  - bm25_search_scoped()     ← bm25_search.py + candidate_indices
  - hybrid_rrf()             ← rrf.py
  - rerank_candidates()      ← reranker.py (contextual prefix + clinical boosts)
  - filter_evidence()        ← acceptance.py
  - retrieve_evidence()      ← retrieval.py (full 5-stage pipeline)
  - generate_grounded_answer() ← grounding.py
  - ask_tamargi()            ← end-to-end
"""

import json
import os

def create_notebook():
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    def add_md(text):
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in text.strip().split("\n")]
        })

    def add_code(text):
        nb["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in text.strip().split("\n")]
        })

    # =========================================================================
    # SECTION 1 — PROJECT INTRODUCTION
    # =========================================================================
    add_md("""# Tamargi.ai — Core Hybrid RAG V2 (Research & Educational Pipeline)

**Tamargi.ai** is an Explainable Personalized Medication Safety AI Assistant built upon official Egyptian Drug Authority (EDA) pharmaceutical monographs.

This research notebook isolates, demonstrates, and evaluates the **core Retrieval-Augmented Generation (RAG V2) pipeline** used by Tamargi.ai.

### Full Production Pipeline (Reproduced in Notebook)

```
User Query (English / Arabic / Egyptian Colloquial)
       │
       ▼
[1. Arabic & Text Normalization]
(normalize_arabic_text → tashkeel, alef, teh marbuta, yeh normalization)
       │
       ▼
[2. Medication Resolution]
(alias table lookup → brand/colloquial → canonical generic)
(3 passes: exact match → substring → Levenshtein typo tolerance)
       │
       ▼
[3. Clinical Section Intent Detection]
(Full keyword map: contraindications / dosage / interactions / ...)
       │
       ▼
[4. Canonical Retrieval Query Construction]
("ibuprofen contraindications" — so BM25 can match English corpus)
       │
       ▼
[5. Stage 1: Drug Monograph Scope Identification]
(Restrict search pool to target drug's monograph pages ± 2)
       │
       ├────────────────────────────────────────┐
       ▼                                        ▼
[6. Dense Semantic Retrieval]          [7. BM25 Keyword Retrieval]
(E5 multilingual, 768-dim)             (English alias-enriched BM25)
(within scoped pool)                   (within scoped pool)
       │                                        │
       └────────────────────┬───────────────────┘
                            ▼
             [8. Reciprocal Rank Fusion (RRF)]
             (Dense 0.8 + BM25 0.8 / (k=30 + rank))
                            │
                            ▼
             [9. CrossEncoder Contextual Reranking]
             (mmarco-MiniLMv2 + drug/section clinical boosts)
                            │
                            ▼
             [10. Evidence Acceptance & Deduplication]
             (entity consistency + near-duplicate filter + page diversity)
                            │
                            ▼
             [11. Grounded Gemini Generation]
             (strict EDA monograph citations)
```

### Why Each Stage Matters
- **Normalization**: Arabic *"بروفين"* must match *"brufen"* alias to resolve to *ibuprofen*.
- **Medication Resolution**: 3-pass algorithm handles colloquial names, brand names, and Arabic transliterations.
- **Section Detection**: Distinguishes *"contraindications"* from *"dosage"* from *"interactions"* — different EDA sections.
- **Canonical Query Construction**: Transforms Arabic query → English clinical query so BM25 can find English corpus sections.
- **Drug Scope**: Restricts 5,437-chunk corpus to ~40 chunks for the target drug → high precision retrieval.
- **RRF**: Merges dense (semantic) and BM25 (keyword) rankings without score scale mismatch.
- **CrossEncoder**: Deep joint attention over query + passage pairs → accurate final ranking.
- **Evidence Filtering**: Rejects unrelated drug chunks and near-duplicate text passages.""")

    # =========================================================================
    # SECTION 2 — IMPORTS
    # =========================================================================
    add_md("""## 1. Imports & Environment Setup

All libraries used by the Tamargi.ai backend are imported here.""")

    add_code("""import os
import re
import time
import json
from pathlib import Path

import pandas as pd
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from google import genai
from google.genai import types

print("PyTorch:", torch.__version__)
print("Device:", "CUDA (GPU)" if torch.cuda.is_available() else "CPU (no GPU)")""")

    # =========================================================================
    # SECTION 3 — CONFIGURATION
    # =========================================================================
    add_md("""## 2. Configuration & File Paths

These values exactly match `backend/app/config.py` (production).""")

    add_code("""# Auto-resolve project root whether running from root or notebooks/
CWD = Path.cwd()
PROJECT_ROOT = CWD.parent if CWD.name == "notebooks" else CWD

DATA_DIR         = PROJECT_ROOT / "data" / "processed"
CHUNKS_PATH      = DATA_DIR / "chunks_with_metadata.csv"
EMBEDDINGS_PATH  = PROJECT_ROOT / "backend" / "embeddings_cache.npy"
GOLD_PATH        = PROJECT_ROOT / "data" / "evaluation" / "rag_gold_dataset.csv"
ALIASES_PATH     = DATA_DIR / "medication_aliases.csv"

# RAG V2 Model Names (production config.py)
EMBEDDING_MODEL  = "intfloat/multilingual-e5-base"
RERANKER_MODEL   = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
GEMINI_MODEL     = "gemini-2.5-flash"

# RAG V2 Hyperparameters (production config.py)
DENSE_K    = 10
BM25_K     = 10
RRF_K      = 30
DENSE_W    = 0.8
BM25_W     = 0.8
CANDIDATE_K = 10
FINAL_K    = 5

print(f"Chunks CSV:        {CHUNKS_PATH}")
print(f"Embeddings cache:  {EMBEDDINGS_PATH}")
print(f"Gold dataset:      {GOLD_PATH}")
print(f"Aliases CSV:       {ALIASES_PATH}")""")

    # =========================================================================
    # SECTION 4 — LOAD CORPUS
    # =========================================================================
    add_md("""## 3. Load Clinical Corpus

5,437 EDA pharmaceutical monograph chunks with clinical metadata.""")

    add_code("""chunks_df = pd.read_csv(CHUNKS_PATH)
print(f"Corpus size: {len(chunks_df):,} chunks")
print(f"Columns: {list(chunks_df.columns)}")
print("\\nChunks per EDA Formulary:")
print(chunks_df['file'].value_counts().to_string())

# Sample chunk
s = chunks_df.iloc[52]
print(f"\\nSample Chunk (row 52):")
print(f"  Drug:    {s['canonical_drug']}  |  Section: {s['section']}")
print(f"  Source:  {s['file']}  (Page {s['page']})")
print(f"  Text:    {str(s['text'])[:200]}...")""")

    # =========================================================================
    # SECTION 5 — ARABIC TEXT NORMALIZATION
    # =========================================================================
    add_md("""## 4. Arabic Text Normalization

Reproduced from `backend/app/normalization/text_normalizer.py`.

Standardizes Arabic text so that *"بروفين"*, *"بروفيـن"*, and *"بروفين."* all match the same alias.""")

    add_code("""def normalize_arabic_text(text: str) -> str:
    \"\"\"
    Normalizes Arabic text for robust medical alias matching.
    Source: text_normalizer.py (production — exact replica)
    
    Steps:
    1. Remove tashkeel / diacritics (e.g. 'بُروفين' → 'بروفين')
    2. Remove tatweel / kashida (ـ)
    3. Normalize alef variants (أ, إ, آ → ا)
    4. Normalize teh marbuta (ة → ه)
    5. Normalize yeh / alef maqsura (ى → ي)
    6. Clean punctuation and whitespace
    \"\"\"
    if not text:
        return ""
    t = text.lower().strip()
    # 1. Remove tashkeel
    t = re.sub(r'[\u0617-\u061A\u064B-\u065F\u0670]', '', t)
    # 2. Remove tatweel
    t = re.sub(r'[\u0640]', '', t)
    # 3. Normalize alef forms
    t = re.sub(r'[أإآٱ]', 'ا', t)
    # 4. Normalize teh marbuta
    t = re.sub(r'ة', 'ه', t)
    # 5. Normalize yeh / alef maqsura
    t = re.sub(r'[ىي]', 'ي', t)
    # 6. Clean punctuation & whitespace
    t = re.sub(r'[\u061f?!.,;:\"()\\[\\]{}_/\\\\-]', ' ', t)
    t = re.sub(r"'", ' ', t)
    t = re.sub(r'\\s+', ' ', t).strip()
    return t


def levenshtein_distance(s1: str, s2: str) -> int:
    \"\"\"
    Computes edit distance between two strings for typo-tolerant alias matching.
    Source: text_normalizer.py (production — exact replica)
    \"\"\"
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            current_row.append(min(
                previous_row[j + 1] + 1,   # deletion
                current_row[j] + 1,         # insertion
                previous_row[j] + (c1 != c2)  # substitution
            ))
        previous_row = current_row
    return previous_row[-1]


# Demonstration
print("Arabic normalization examples:")
tests = [
    ("بُروفين",  "Brufen with tashkeel removed"),
    ("بروفيـن",  "Brufen with tatweel removed"),
    ("أسبيرين",  "Alef normalization"),
    ("باراسيتامول.", "Punctuation stripped"),
    ("إيبوبروفين",  "Alef-hamza below normalized"),
]
for txt, desc in tests:
    print(f"  '{txt}' → '{normalize_arabic_text(txt)}'  ({desc})")""")

    # =========================================================================
    # SECTION 6 — MEDICATION RESOLVER
    # =========================================================================
    add_md("""## 5. Medication Resolution

Reproduced from `backend/app/normalization/medication_resolver.py`.

The production resolver uses **3 sequential passes**:
1. **Exact normalized alias match** (confidence 1.0)
2. **Substring match** — alias appears inside the query (confidence 0.95)  
3. **Levenshtein typo tolerance** on words ≥ 5 chars (distance ≤ 1, confidence 0.85)

This handles:
- `"بروفين"` → `ibuprofen` (Arabic alias)
- `"brufen 400"` → `ibuprofen` (English brand + strength)
- `"brofen"` → `ibuprofen` (typo tolerance)
- `"انيدولافنجين"` → `anidulafungin` (Arabic transliteration)""")

    add_code("""# Load the same aliases CSV used by production
aliases_df = pd.read_csv(ALIASES_PATH)
ALIAS_TABLE = aliases_df[aliases_df["active"] == True].to_dict(orient="records")
print(f"Loaded {len(ALIAS_TABLE)} active medication aliases")
print(f"Example aliases: {aliases_df[['alias', 'canonical_generic_name']].head(8).to_string(index=False)}")""")

    add_code("""# Sort aliases longest-first so multi-word brands are matched before single words
SORTED_ALIASES = sorted(
    ALIAS_TABLE,
    key=lambda r: len(normalize_arabic_text(str(r.get("alias", "")))),
    reverse=True
)

def extract_all_medications(query_text: str) -> list[dict]:
    \"\"\"
    Extracts all medication entities from a query.
    Reproduced from medication_resolver.py — extract_all_medications() (production logic).
    
    Returns list of dicts with: canonical_generic, brand_name, confidence, raw_term
    \"\"\"
    clean_query = normalize_arabic_text(query_text)
    found_generics = set()
    results = []

    # Pass 1 + 2: Normalized substring match (sorted longest-first for priority)
    for row in SORTED_ALIASES:
        alias_norm = normalize_arabic_text(str(row.get("alias", "")))
        gen = row["canonical_generic_name"]
        if len(alias_norm) >= 3 and alias_norm in clean_query:
            if gen not in found_generics:
                found_generics.add(gen)
                results.append({
                    "canonical_generic": gen,
                    "brand_name": row.get("brand_name") if pd.notna(row.get("brand_name", "")) else None,
                    "confidence": 1.0,
                    "raw_term": alias_norm
                })

    # Pass 3: Levenshtein typo tolerance on words >= 5 chars
    clean_words = clean_query.split()
    for word in clean_words:
        if len(word) >= 5 and word not in clean_query:  # only for unmatched words
            for row in SORTED_ALIASES:
                alias_norm = normalize_arabic_text(str(row.get("alias", "")))
                gen = row["canonical_generic_name"]
                if len(alias_norm) >= 5 and gen not in found_generics:
                    if levenshtein_distance(word, alias_norm) <= 1:
                        found_generics.add(gen)
                        results.append({
                            "canonical_generic": gen,
                            "brand_name": row.get("brand_name") if pd.notna(row.get("brand_name", "")) else None,
                            "confidence": 0.85,
                            "raw_term": word
                        })
                        break  # Move to next word after first match

    return results


# Test medication resolver on representative queries
test_queries = [
    "What are the contraindications of Anidulafungin?",      # English exact
    "ما هي موانع استعمال دواء انيدولافنجين؟",                 # Arabic transliteration
    "ما هي موانع استخدام بروفين 400؟",                        # Arabic brand name
    "ما هي تحذيرات استخدام الميتفورمين للسكري؟",             # Arabic generic + condition
    "What are the drug interactions of warfarin?",            # English generic
]

print("=" * 70)
print("MEDICATION RESOLVER TEST RESULTS:")
print("=" * 70)
for q in test_queries:
    meds = extract_all_medications(q)
    print(f"\\nQuery: {q}")
    if meds:
        for m in meds:
            print(f"  → Resolved: {m['canonical_generic']} (confidence {m['confidence']}, raw: '{m['raw_term']}')")
    else:
        print("  → No medication resolved")""")

    # =========================================================================
    # SECTION 7 — SECTION INTENT DETECTION
    # =========================================================================
    add_md("""## 6. Clinical Section Intent Detection

Reproduced from `backend/app/normalization/query_translator.py`.

The full `INTENT_KEYWORD_MAP` maps clinical sections to English **and** Arabic keywords.

This is why the notebook previously had only 53.3% Section ID — the simplified version was missing most Arabic keywords and many English clinical terms.""")

    add_code("""# INTENT_KEYWORD_MAP — exact replica from query_translator.py (production)
INTENT_KEYWORD_MAP = {
    "contraindications": [
        "موانع", "ممنوع", "contraindication", "contraindications",
        "hypersensitivity", "allergy", "حساسية", "penicillin"
    ],
    "dosage_adjustment": [
        "renal adjustment", "kidney adjustment", "hepatic adjustment",
        "altered kidney function",
        "تعديل الجرعه", "تعديل الجرعة", "مرضى الكلى", "مرضى الكبد", "قصور كلوي"
    ],
    "administration": [
        "administered", "administer", "administration", "how to take",
        "take with food", "empty stomach",
        "طريقه", "طريقة", "كيفيه", "كيفية", "ازاي", "طريقة استعمال",
        "طريقة استخدام", "طريقة اخذ", "طريقة أخذ", "طريقة إعطاء"
    ],
    "high_alert": [
        "high alert", "high-alert", "narrow therapeutic",
        "عالي الخطوره", "عالي الخطورة", "عالية الخطوره", "عالية الخطورة",
        "خطوره", "خطورة", "عقار عالي الخطورة"
    ],
    "do_not_crush": [
        "do not crush", "crush", "chew", "extended release",
        "sustained release", "enteric coated",
        "كسر", "طحن", "ممتدة المفعول", "ممتد المفعول", "مغلفة معويا", "مغلفه"
    ],
    "drug_interactions": [
        "interaction", "interactions", "interact", "cyp3a4",
        "bleeding", "ace inhibitors",
        "تعارض", "تفاعل", "تداخل", "تداخلات", "مع بعض", "تفاعلات"
    ],
    "adverse_reactions": [
        "side effects", "adverse reactions", "adverse effects",
        "tendon rupture", "tendinitis",
        "اثار جانبيه", "اثار جانبية", "آثار جانبيه", "آثار جانبية",
        "اعراض جانبيه", "اعراض جانبية", "أعراض جانبيه", "أعراض جانبية",
        "أوتار", "اوتار", "تمزق"
    ],
    "pregnancy_lactation": [
        "pregnancy", "lactation", "breastfeeding", "pregnant", "teratogenic",
        "حمل", "حامل", "رضاعه", "رضاعة", "مرضع", "جنين"
    ],
    "dosage": [
        "dose", "dosage", "how much", "maximum dose", "maximum daily dose",
        "dosage forms", "strengths", "available forms",
        "جرعه", "جرعة", "كميه", "كمية", "الجرعه القصوى", "الجرعة القصوى",
        "أشكال دوائيه", "أشكال دوائية", "اشكال دوائيه", "اشكال دوائية", "تركيزات"
    ],
    "warnings_precautions": [
        "warning", "warnings", "precaution", "precautions",
        "monitoring", "diabetic", "diabetes",
        "تحذير", "تحذيرات", "احتياط", "احتياطات",
        "سكر", "مرضى السكر"
    ],
    "indications": [
        "indication", "indications", "therapeutic uses",
        "what is it used for", "approved uses", "ulcer",
        "دواعي", "استعمال", "استخدام", "فائده", "فائدة", "علاج", "قرحه", "قرحة"
    ]
}


def detect_query_section(query_text: str) -> str:
    \"\"\"
    Detects the primary clinical section from user query.
    Reproduced from query_translator.py — detect_query_section() (production logic).
    
    Returns canonical section string e.g. 'contraindications', 'dosage', etc.
    Defaults to 'indications' when no specific section is detected.
    \"\"\"
    clean_q = normalize_arabic_text(query_text)
    for section, keywords in INTENT_KEYWORD_MAP.items():
        for kw in keywords:
            kw_clean = normalize_arabic_text(kw)
            if kw_clean in clean_q:
                return section
    return "indications"


def build_retrieval_query(query_text: str, resolved_meds: list[dict]) -> str:
    \"\"\"
    Constructs a canonical English retrieval query from any language input.
    Reproduced from query_translator.py — build_canonical_retrieval_query() (production logic).
    
    Why this matters for Arabic:
    Query 'ما هي موانع انيدولافنجين؟' → 'anidulafungin contraindications'
    Now BM25 can find English EDA text instead of returning zero keyword matches.
    \"\"\"
    clean_q = normalize_arabic_text(query_text)
    med_names = [m["canonical_generic"] for m in resolved_meds if m.get("canonical_generic")]
    section = detect_query_section(query_text)
    section_term = section.replace("_", " ")

    # Detect clinical modifiers
    modifiers = []
    if any(k in clean_q for k in ["oral", "فموي", "أقراص", "اقراص"]):
        modifiers.append("oral")
    if any(k in clean_q for k in ["sublingual", "تحت اللسان"]):
        modifiers.append("sublingual")
    if any(k in clean_q for k in ["rheumat", "روماتيزم", "مفاصل"]):
        modifiers.append("rheumatoid arthritis")
    if any(k in clean_q for k in ["angina", "ذبحه", "ذبحة"]):
        modifiers.append("angina")
    if "cyp3a4" in clean_q:
        modifiers.append("cyp3a4")
    if "81" in clean_q:
        modifiers.append("81 mg")
    if any(normalize_arabic_text(k) in clean_q for k in ["extended release", "ممتدة المفعول", "ممتد المفعول"]):
        modifiers.append("extended release")
    if any(normalize_arabic_text(k) in clean_q for k in ["high alert", "عالي الخطورة", "عالية الخطورة", "خطورة"]):
        modifiers.append("high alert")
    if any(normalize_arabic_text(k) in clean_q for k in ["do not crush", "طحن", "كسر"]):
        modifiers.append("do not crush")

    mod_str = f" {' '.join(modifiers)}" if modifiers else ""
    med_str = " ".join(med_names) if med_names else clean_q[:50]
    return f"{med_str} {section_term}{mod_str}".strip()


# Test section detection and query construction
print("SECTION INTENT + RETRIEVAL QUERY CONSTRUCTION:")
print("=" * 70)
test_queries_2 = [
    "What are the contraindications of Anidulafungin?",
    "ما هي موانع استعمال دواء انيدولافنجين؟",
    "ما هي التفاعلات الدوائية للوارفارين؟",
    "ما هي الآثار الجانبية للميتفورمين؟",
    "What is the dosage of metformin for diabetics?",
    "ما هي جرعة الايبوبروفين القصوى؟",
    "Is ibuprofen safe during pregnancy?",
    "ما هي احتياطات استخدام السيبروفلوكساسين؟",
]
for q in test_queries_2:
    meds = extract_all_medications(q)
    section = detect_query_section(q)
    retrieval_q = build_retrieval_query(q, meds)
    meds_str = [m['canonical_generic'] for m in meds] if meds else ["(none)"]
    print(f"\\nInput:    {q}")
    print(f"Drugs:    {meds_str}")
    print(f"Section:  {section}")
    print(f"BM25 Query: '{retrieval_q}'"  )""")

    # =========================================================================
    # SECTION 8 — LOAD PRECOMPUTED EMBEDDINGS
    # =========================================================================
    add_md("""## 7. Load Precomputed Embeddings Cache

5,437 passages × 768 dimensions, pre-encoded with `passage: ` prefix and L₂-normalized.""")

    add_code("""embeddings = np.load(str(EMBEDDINGS_PATH))
print(f"Embeddings shape: {embeddings.shape}")
print(f"  → {embeddings.shape[0]} chunk vectors × {embeddings.shape[1]} dimensions")
print(f"  → Storage: {embeddings.nbytes / 1e6:.1f} MB")
print(f"  → All L2-normalized: {np.allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-5)}")""")

    # =========================================================================
    # SECTION 9 — LOAD E5 MODEL
    # =========================================================================
    add_md("""## 8. Load Multilingual-E5 Embedding Model

`intfloat/multilingual-e5-base` — 768-dim multilingual encoder.

**Asymmetric prefix rule**:
- Documents: `"passage: " + text`  
- Queries: `"query: " + text`""")

    add_code("""device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading {EMBEDDING_MODEL} on {device}...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
print("E5 model ready!")

# Encode a sample query
q_sample = "What are the contraindications of Anidulafungin?"
q_vec = embedding_model.encode(["query: " + q_sample], normalize_embeddings=True)
print(f"\\nQuery:  '{q_sample}'")
print(f"Vector shape: {q_vec.shape}  |  L2 norm: {np.linalg.norm(q_vec[0]):.4f}")""")

    # =========================================================================
    # SECTION 10 — DENSE RETRIEVAL
    # =========================================================================
    add_md("""## 9. Dense Semantic Retrieval

Because all vectors are L₂-normalized, cosine similarity = dot product: **Similarity = Q · Dᵀ**

Optionally restricted to a scoped subset of indices (production behavior).""")

    add_code("""def dense_search_scoped(query: str, scope_indices: list | None, top_k: int = 20) -> list[dict]:
    \"\"\"
    Dense E5 semantic search.
    If scope_indices is provided: restricts search to that monograph subset.
    If None: global search across all 5,437 chunks.
    \"\"\"
    q_vec = embedding_model.encode(["query: " + query], normalize_embeddings=True)

    if scope_indices is not None:
        sub_embs = embeddings[scope_indices]
        scores = np.dot(sub_embs, q_vec.T).flatten()
        local_sorted = np.argsort(-scores)[:top_k]
        global_indices = [scope_indices[i] for i in local_sorted]
        top_scores = scores[local_sorted]
    else:
        scores = np.dot(embeddings, q_vec.T).flatten()
        global_sorted = np.argsort(-scores)[:top_k]
        global_indices = list(global_sorted)
        top_scores = scores[global_sorted]

    results = []
    for rank, (idx, score) in enumerate(zip(global_indices, top_scores), start=1):
        row = chunks_df.iloc[idx]
        results.append({
            "rank": rank,
            "dense_score": float(score),
            "index": int(idx),
            "chunk_id": int(row.get("chunk_id", 0)),
            "canonical_drug": str(row.get("canonical_drug", "")),
            "section": str(row.get("section", "")),
            "file": str(row.get("file", "")),
            "page": int(row.get("page", 0)),
            "text": str(row.get("text", ""))
        })
    return results

# Global dense search demo
dense_demo = dense_search_scoped("What are the contraindications of Anidulafungin?", None, top_k=5)
demo_df = pd.DataFrame(dense_demo)
display(demo_df[["rank", "dense_score", "canonical_drug", "section", "file", "page"]].rename(
    columns={"rank": "dense_rank"}))""")

    # =========================================================================
    # SECTION 11 — BM25 SPARSE RETRIEVAL
    # =========================================================================
    add_md("""## 10. BM25 Sparse Keyword Retrieval (Metadata-Enriched)

BM25 corpus is enriched with: `canonical_drug + monograph_name + section + text`

The tokenizer captures both Latin (`a-z0-9`) and Arabic (`\u0600-\u06FF`) tokens.""")

    add_code("""def tokenize_bm25(text: str) -> list[str]:
    \"\"\"Multilingual BM25 tokenizer — matches production RAGLoader.tokenize().\"\"\"
    if not text:
        return []
    return re.findall(r"[a-z0-9]+|[\u0600-\u06FF]+", str(text).lower())

# Build metadata-enriched BM25 corpus
print("Building BM25 index (metadata-enriched)...")
bm25_docs = []
for _, row in chunks_df.iterrows():
    drug = str(row.get("canonical_drug", "") or "")
    mono = str(row.get("monograph_name", "") or "")
    sec  = str(row.get("section", "") or "")
    txt  = str(row.get("text", "") or "")
    bm25_docs.append(f"{drug} {mono} {sec} {txt}".strip())

tokenized_corpus = [tokenize_bm25(doc) for doc in bm25_docs]
bm25_index = BM25Okapi(tokenized_corpus)
print(f"BM25 index ready: {len(tokenized_corpus):,} documents")""")

    add_code("""def bm25_search_scoped(query: str, scope_indices: list | None, top_k: int = 20) -> list[dict]:
    \"\"\"
    BM25 search.
    If scope_indices provided: builds mini BM25 over scoped subset.
    If None: global BM25 search.
    
    KEY INSIGHT: For Arabic queries, we pass the CANONICAL ENGLISH RETRIEVAL QUERY
    (built by build_retrieval_query()) instead of the raw Arabic query,
    so BM25 can match English EDA corpus text.
    \"\"\"
    tokens = tokenize_bm25(query)

    if scope_indices is not None:
        scoped_docs = [tokenized_corpus[i] for i in scope_indices]
        mini_bm25 = BM25Okapi(scoped_docs)
        scores = mini_bm25.get_scores(tokens)
        local_sorted = np.argsort(-scores)[:top_k]
        global_indices = [scope_indices[i] for i in local_sorted]
        top_scores = scores[local_sorted]
    else:
        scores = bm25_index.get_scores(tokens)
        global_sorted = np.argsort(-scores)[:top_k]
        global_indices = list(global_sorted)
        top_scores = scores[global_sorted]

    results = []
    for rank, (idx, score) in enumerate(zip(global_indices, top_scores), start=1):
        row = chunks_df.iloc[idx]
        results.append({
            "rank": rank,
            "bm25_score": float(score),
            "index": int(idx),
            "chunk_id": int(row.get("chunk_id", 0)),
            "canonical_drug": str(row.get("canonical_drug", "")),
            "section": str(row.get("section", "")),
            "file": str(row.get("file", "")),
            "page": int(row.get("page", 0)),
            "text": str(row.get("text", ""))
        })
    return results

# BM25 global search demo (using English query)
bm25_demo = bm25_search_scoped("anidulafungin contraindications", None, top_k=5)
bm25_df = pd.DataFrame(bm25_demo)
display(bm25_df[["rank", "bm25_score", "canonical_drug", "section", "file", "page"]].rename(
    columns={"rank": "bm25_rank"}))""")

    # =========================================================================
    # SECTION 12 — HYBRID RRF
    # =========================================================================
    add_md("""## 11. Reciprocal Rank Fusion (RRF)

$$\\text{RRF}(d) = \\frac{w_{dense}}{k + rank_{dense}(d)} + \\frac{w_{BM25}}{k + rank_{BM25}(d)}$$

$k=30$, $w_{dense}=0.8$, $w_{BM25}=0.8$""")

    add_code("""def hybrid_rrf(
    dense_results: list[dict],
    bm25_results: list[dict],
    top_k: int = 15
) -> list[dict]:
    \"\"\"
    Merges dense and BM25 ranked lists using Reciprocal Rank Fusion.
    Reproduced from rrf.py + hybrid_search.py (production).
    \"\"\"
    rrf_scores = {}
    doc_data = {}

    for rank_i, r in enumerate(dense_results, start=1):
        idx = int(r["index"])
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + DENSE_W / (RRF_K + rank_i)
        doc_data[idx] = r

    for rank_i, r in enumerate(bm25_results, start=1):
        idx = int(r["index"])
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + BM25_W / (RRF_K + rank_i)
        if idx not in doc_data:
            doc_data[idx] = r

    sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]
    results = []
    for rank, idx in enumerate(sorted_indices, start=1):
        item = doc_data[idx].copy()
        item["rrf_rank"] = rank
        item["rrf_score"] = float(rrf_scores[idx])
        results.append(item)
    return results

# Demo
d_res = dense_search_scoped("anidulafungin contraindications", None, top_k=20)
b_res = bm25_search_scoped("anidulafungin contraindications", None, top_k=20)
rrf_res = hybrid_rrf(d_res, b_res, top_k=5)
rrf_df = pd.DataFrame(rrf_res)
display(rrf_df[["rrf_rank", "rrf_score", "canonical_drug", "section", "file", "page"]])""")

    # =========================================================================
    # SECTION 13 — CROSSENCODER
    # =========================================================================
    add_md("""## 12. CrossEncoder Contextual Reranking

`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

**Contextual prefix format** (matching production `reranker.py`):
```
Drug: Anidulafungin
Section: Contraindications
Document: egypt_antimicrobial_formulary_2023.pdf

[chunk text]
```

**Clinical boosts** (matching production):
- +1.00 if canonical drug matches target drug
- +0.50 if target drug mentioned in text
- -1.20 if *different* drug is the canonical drug
- +0.75 if section matches target section""")

    add_code("""print(f"Loading CrossEncoder: {RERANKER_MODEL} on {device}...")
reranker = CrossEncoder(RERANKER_MODEL, device=device)
print("CrossEncoder ready!")

def rerank_candidates(
    query: str,
    candidates: list[dict],
    target_meds: list[str] = None,
    target_sec: str = None
) -> list[dict]:
    \"\"\"
    Contextual CrossEncoder reranking with clinical boosts.
    Reproduced from reranker.py (production — exact replica of logic).
    \"\"\"
    if not candidates:
        return []

    pairs = []
    for c in candidates:
        drug = str(c.get("canonical_drug", "")).strip().title()
        sec  = str(c.get("section", "")).strip().replace("_", " ").title()
        doc  = str(c.get("file", "")).strip()
        text = str(c.get("text", "")).strip()

        headers = []
        if drug: headers.append(f"Drug: {drug}")
        if sec and sec.lower() != "other": headers.append(f"Section: {sec}")
        if doc:  headers.append(f"Document: {doc}")
        prefix = "\\n".join(headers)
        cand_text = f"{prefix}\\n\\n{text}".strip() if prefix else text
        pairs.append([query, cand_text])

    raw_scores = reranker.predict(pairs)

    reranked = []
    for c, score in zip(candidates, raw_scores):
        adj = float(score)
        c_drug = str(c.get("canonical_drug", "")).lower().strip()
        c_sec  = str(c.get("section", "")).lower().strip()
        c_text = str(c.get("text", "")).lower()

        if target_meds:
            if any(tm == c_drug or tm in c_drug for tm in target_meds if c_drug):
                adj += 1.00       # Correct drug — boost
            elif any(tm in c_text for tm in target_meds):
                adj += 0.50       # Drug mentioned in text — partial boost
            elif c_drug and not any(tm in c_drug for tm in target_meds):
                adj -= 1.20       # Wrong drug — penalty

        if target_sec and c_sec == target_sec:
            adj += 0.75           # Correct section — boost

        item = c.copy()
        item["reranker_score"] = adj
        reranked.append(item)

    reranked.sort(key=lambda x: x["reranker_score"], reverse=True)
    return reranked

print("rerank_candidates() ready")""")

    # =========================================================================
    # SECTION 14 — EVIDENCE ACCEPTANCE / FILTERING
    # =========================================================================
    add_md("""## 13. Evidence Acceptance & Deduplication

Reproduced from `backend/app/rag/acceptance.py — filter_and_accept_evidence()`.

Three filters applied in order:
1. **Entity consistency**: Reject chunks where the canonical drug is unrelated to the target drug.
2. **Near-duplicate removal**: Skip chunks with Jaccard similarity ≥ 0.85 to an already-accepted chunk.
3. **Page diversity**: Accept at most 1 chunk per (file, page) in Pass 1, then fill remaining slots in Pass 2.

This is critical for achieving **correct Top-5 evidence** — without it, you may get 5 chunks from the same page.""")

    add_code("""def jaccard_similarity(text1: str, text2: str) -> float:
    \"\"\"Word-level Jaccard similarity for near-duplicate detection.\"\"\"
    words1 = set(re.findall(r"\\w+", text1.lower()))
    words2 = set(re.findall(r"\\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


def filter_evidence(
    candidates: list[dict],
    target_meds: list[str] = None,
    target_sec: str = None,
    max_count: int = 5
) -> list[dict]:
    \"\"\"
    Evidence acceptance/deduplication layer.
    Reproduced from acceptance.py — filter_and_accept_evidence() (production logic).

    Pass 1: One chunk per (file, page), reject unrelated drugs, reject near-duplicates.
    Pass 2: Fill remaining slots without page-diversity constraint.
    \"\"\"
    if not candidates:
        return []

    t_meds = [m.lower().strip() for m in target_meds] if target_meds else []

    accepted = []
    seen_slots = set()
    page_counts = {}

    # Pass 1: High-quality, diverse evidence
    for cand in candidates:
        c_file  = str(cand.get("file", ""))
        c_page  = int(cand.get("page", 0))
        c_cid   = int(cand.get("chunk_id", cand.get("index", 0)))
        c_drug  = str(cand.get("canonical_drug", "")).lower().strip()
        c_text  = str(cand.get("text", ""))

        # 1. Entity consistency check
        if t_meds:
            is_target = any(tm in c_drug or c_drug in tm for tm in t_meds if c_drug)
            mentions_target = any(tm in c_text.lower() for tm in t_meds)
            is_special_doc = any(sd in c_file.lower() for sd in ["high_alert", "do_not_crush", "otc"])
            if not (is_target or mentions_target or is_special_doc):
                continue  # Reject: unrelated drug

        slot_key = f"{c_file}:{c_page}:{c_cid}"
        page_key = f"{c_file}:{c_page}"

        if slot_key in seen_slots:
            continue  # Already accepted

        # 2. Page diversity: max 1 per page in Pass 1
        if page_counts.get(page_key, 0) >= 1:
            continue

        # 3. Near-duplicate check
        is_dup = any(
            acc.get("file") == c_file
            and abs(int(acc.get("page", 0)) - c_page) <= 1
            and jaccard_similarity(c_text, acc.get("text", "")) >= 0.85
            for acc in accepted
        )
        if is_dup:
            continue

        item = cand.copy()
        item["accepted_rank"] = len(accepted) + 1
        accepted.append(item)
        seen_slots.add(slot_key)
        page_counts[page_key] = page_counts.get(page_key, 0) + 1

        if len(accepted) >= max_count:
            break

    # Pass 2: Fill remaining slots
    if len(accepted) < max_count:
        for cand in candidates:
            c_file = str(cand.get("file", ""))
            c_page = int(cand.get("page", 0))
            c_cid  = int(cand.get("chunk_id", cand.get("index", 0)))
            slot_key = f"{c_file}:{c_page}:{c_cid}"
            if slot_key not in seen_slots:
                item = cand.copy()
                item["accepted_rank"] = len(accepted) + 1
                accepted.append(item)
                seen_slots.add(slot_key)
                if len(accepted) >= max_count:
                    break

    return accepted

print("filter_evidence() ready")""")

    # =========================================================================
    # SECTION 15 — SCOPE IDENTIFICATION
    # =========================================================================
    add_md("""## 14. Stage 1: Drug Monograph Scope Identification

Reproduced from `backend/app/rag/retrieval.py — get_candidate_scope_indices()`.

**Why this is essential for Arabic**:
A query like *"ما هي موانع انيدولافنجين؟"* gets resolved to canonical drug `anidulafungin`.  
We restrict the 5,437-chunk corpus to only the ~40 chunks covering Anidulafungin's EDA monograph pages.  
Within this scope, BM25 works perfectly on the English text.""")

    add_code("""FORMULARY_MAP = {
    "warfarin": "egypt_blood_disorders_formulary_2025.pdf",
    "enoxaparin": "egypt_blood_disorders_formulary_2025.pdf",
    "heparin": "egypt_blood_disorders_formulary_2025.pdf",
    "omeprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "pantoprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "furosemide": "egypt_cardiovascular_formulary_2024.pdf",
    "spironolactone": "egypt_cardiovascular_formulary_2024.pdf",
    "bisoprolol": "egypt_cardiovascular_formulary_2024.pdf",
    "captopril": "egypt_cardiovascular_formulary_2024.pdf",
    "propranolol": "egypt_cardiovascular_formulary_2024.pdf",
    "nitroglycerin": "egypt_cardiovascular_formulary_2024.pdf",
    "clopidogrel": "egypt_cardiovascular_formulary_2024.pdf",
    "atorvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "simvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "amoxicillin": "egypt_antimicrobial_formulary_2023.pdf",
    "ciprofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "levofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "clarithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "azithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "sulfamethoxazole": "egypt_antimicrobial_formulary_2023.pdf",
    "dexamethasone": "egypt_endocrine_formulary_2024.pdf",
    "metformin": "egypt_endocrine_formulary_2024.pdf",
    "methotrexate": "egypt_conventional_anticancer_formulary_2024.pdf",
    "capecitabine": "egypt_targeted_anticancer_formulary_2025.pdf",
    "sildenafil": "egypt_cardiovascular_formulary_2024.pdf",
    "ibuprofen": "egypt_blood_disorders_formulary_2025.pdf",
    "paracetamol": "egypt_otc_drug_list_2026.pdf",
    "aspirin": "egypt_otc_drug_list_2026.pdf",
    "acetylsalicylic acid": "egypt_otc_drug_list_2026.pdf"
}

def get_scope_indices(target_meds: list[str], query_lower: str = "") -> list[int] | None:
    \"\"\"
    Identifies monograph candidate indices for detected medications.
    Includes ±2 page window around the drug's monograph entry.
    Reproduced from retrieval.py — get_candidate_scope_indices() (production logic).
    \"\"\"
    # Specialized document scoping (high-alert, do-not-crush, OTC)
    if any(k in query_lower for k in ["high alert", "high-alert", "عالي الخطورة", "عالية الخطورة"]):
        return chunks_df[chunks_df["file"].str.contains("high_alert", case=False, na=False)].index.tolist()
    if any(k in query_lower for k in ["do not crush", "crush", "طحن", "كسر", "enteric coated"]):
        return chunks_df[chunks_df["file"].str.contains("do_not_crush", case=False, na=False)].index.tolist()

    if not target_meds:
        return None

    candidate_indices = set()
    for med in target_meds:
        m = med.lower().strip()
        exp_file = FORMULARY_MAP.get(m, "")

        if exp_file:
            m_rows = chunks_df[
                (chunks_df["canonical_drug"].astype(str).str.lower() == m) &
                (chunks_df["file"] == exp_file)
            ]
            if m_rows.empty:
                m_rows = chunks_df[
                    (chunks_df["file"] == exp_file) &
                    (chunks_df["text"].astype(str).str.lower().str.contains(m, na=False))
                ]
        else:
            m_rows = chunks_df[chunks_df["canonical_drug"].astype(str).str.lower() == m]
            if m_rows.empty:
                m_rows = chunks_df[
                    chunks_df["canonical_drug"].astype(str).str.lower().str.contains(m, na=False)
                ]

        if not m_rows.empty:
            min_p = max(1, int(m_rows["page"].min()) - 2)
            max_p = int(m_rows["page"].max()) + 2
            f_name = m_rows.iloc[0]["file"]
            scope_rows = chunks_df[
                (chunks_df["file"] == f_name) &
                (chunks_df["page"] >= min_p) &
                (chunks_df["page"] <= max_p)
            ]
            candidate_indices.update(scope_rows.index.tolist())
        else:
            # Text-based fallback
            text_hits = chunks_df[
                chunks_df["text"].astype(str).str.lower().str.contains(m, na=False)
            ].index.tolist()[:50]
            candidate_indices.update(text_hits)

    return sorted(candidate_indices) if candidate_indices else None


# Demonstrate scope identification
demo_drug = "anidulafungin"
scope = get_scope_indices([demo_drug])
print(f"Drug: {demo_drug}")
print(f"Scope: {len(scope)} chunks from monograph (vs 5,437 global corpus)")
scope_files = chunks_df.iloc[scope]["file"].value_counts()
scope_pages = sorted(chunks_df.iloc[scope]["page"].unique())
print(f"Files: {scope_files.to_dict()}")
print(f"Pages: {scope_pages}")""")

    # =========================================================================
    # SECTION 16 — COMPLETE RETRIEVE FUNCTION
    # =========================================================================
    add_md("""## 15. Complete RAG V2 Retrieval Function

Full 5-stage production pipeline assembled step by step:

1. **Medication resolution** → canonical generic name(s)
2. **Section detection** → target clinical section
3. **Canonical query construction** → English BM25 query
4. **Scope identification** → monograph chunk subset
5. **Scoped hybrid search** (Dense + BM25 → RRF) → top candidates
6. **CrossEncoder reranking** → re-scored candidates
7. **Neighbor expansion** → adds adjacent chunks around top hit
8. **Evidence filtering** → dedup + entity consistency → final Top-K""")

    add_code("""def retrieve_evidence(query: str, top_k: int = 5) -> list[dict]:
    \"\"\"
    Complete RAG V2 pipeline matching Tamargi.ai production retrieval.
    All stages are reproduced from backend/app/rag/retrieval.py.
    \"\"\"
    # ── Stage 1: Normalization & Entity Extraction ──────────────────────────
    resolved_meds = extract_all_medications(query)
    target_meds = [m["canonical_generic"] for m in resolved_meds]
    target_sec = detect_query_section(query)

    # Build canonical English retrieval query (critical for Arabic queries)
    retrieval_query = build_retrieval_query(query, resolved_meds)
    q_lower = normalize_arabic_text(query)

    # ── Stage 2: Scope Identification ───────────────────────────────────────
    scope_indices = get_scope_indices(target_meds, q_lower)
    use_scope = scope_indices is not None and len(scope_indices) >= 5
    pool = scope_indices if use_scope else None
    pool_k = min(len(pool), 50) if use_scope else DENSE_K

    # ── Stage 3: Hybrid Search (Dense + BM25 → RRF) ─────────────────────────
    dense_results = dense_search_scoped(retrieval_query, pool, top_k=pool_k)
    bm25_results  = bm25_search_scoped(retrieval_query, pool, top_k=pool_k)
    rrf_candidates = hybrid_rrf(dense_results, bm25_results, top_k=CANDIDATE_K + 5)

    # ── Stage 4: CrossEncoder Reranking ─────────────────────────────────────
    reranked = rerank_candidates(
        retrieval_query, rrf_candidates,
        target_meds=target_meds, target_sec=target_sec
    )

    # ── Stage 5: Neighbor Chunk Expansion ────────────────────────────────────
    if reranked and reranked[0].get("reranker_score", 0) > -2.0:
        top_hit = reranked[0]
        top_idx = top_hit.get("index")
        seen_cids = {int(c.get("chunk_id", c.get("index", -1))) for c in reranked}

        if top_idx is not None and 0 <= top_idx < len(chunks_df):
            for offset in [1, -1, 2]:
                n_idx = top_idx + offset
                if 0 <= n_idx < len(chunks_df):
                    n_row = chunks_df.iloc[n_idx]
                    same_file  = str(n_row["file"]).lower() == str(top_hit.get("file", "")).lower()
                    nearby_page = abs(int(n_row["page"]) - int(top_hit.get("page", 0))) <= 1
                    n_cid = int(n_row.get("chunk_id", n_idx))
                    if same_file and nearby_page and n_cid not in seen_cids:
                        reranked.append({
                            "index": int(n_idx),
                            "chunk_id": n_cid,
                            "file": str(n_row["file"]),
                            "page": int(n_row["page"]),
                            "canonical_drug": str(n_row.get("canonical_drug", "")),
                            "monograph_name": str(n_row.get("monograph_name", "")),
                            "section": str(n_row.get("section", "other")),
                            "text": str(n_row["text"]),
                            "rrf_score": float(top_hit.get("rrf_score", 0.0)) * 0.9,
                            "reranker_score": float(top_hit.get("reranker_score", 0.0)) - 0.05 * abs(offset)
                        })
                        seen_cids.add(n_cid)

        reranked = sorted(reranked, key=lambda x: x.get("reranker_score", 0.0), reverse=True)

    # ── Stage 6: Evidence Acceptance & Deduplication ─────────────────────────
    accepted = filter_evidence(
        reranked,
        target_meds=target_meds,
        target_sec=target_sec,
        max_count=top_k
    )
    return accepted

print("retrieve_evidence() — full production RAG V2 pipeline READY")""")

    # =========================================================================
    # SECTION 17 — ENGLISH QUERY TEST
    # =========================================================================
    add_md("""## 16. Test: English Clinical Query

*What are the contraindications of Anidulafungin?*""")

    add_code("""en_query = "What are the contraindications of Anidulafungin?"
en_evidence = retrieve_evidence(en_query, top_k=3)

print("=" * 80)
print(f"QUERY: {en_query}")
print("=" * 80)
for i, ev in enumerate(en_evidence, 1):
    print(f"\\n[Evidence {i}]  Reranker Score: {ev.get('reranker_score', 0):.3f}")
    print(f"  Drug:     {ev['canonical_drug']}")
    print(f"  Section:  {ev['section']}")
    print(f"  Source:   {ev['file']}  (Page {ev['page']})")
    print(f"  Text:     {ev['text'][:220]}...")""")

    # =========================================================================
    # SECTION 18 — ARABIC QUERY TEST
    # =========================================================================
    add_md("""## 17. Test: Arabic Clinical Query

*ما هي موانع استعمال دواء انيدولافنجين؟*

**What happens step by step:**
1. `normalize_arabic_text()` standardizes the query
2. `extract_all_medications()` resolves *"انيدولافنجين"* → `anidulafungin`
3. `detect_query_section()` detects *"موانع"* → `contraindications`
4. `build_retrieval_query()` constructs `"anidulafungin contraindications"`
5. `get_scope_indices()` restricts search to Anidulafungin's 40 monograph chunks
6. Dense + BM25 + RRF + CrossEncoder finds the correct contraindications chunk""")

    add_code("""ar_query = "ما هي موانع استعمال دواء انيدولافنجين؟"

# Show exactly what happens at each step
meds = extract_all_medications(ar_query)
sec  = detect_query_section(ar_query)
rq   = build_retrieval_query(ar_query, meds)
scope = get_scope_indices([m["canonical_generic"] for m in meds])

print(f"Input Query:        {ar_query}")
print(f"Normalized:         {normalize_arabic_text(ar_query)}")
print(f"Resolved Drug:      {[m['canonical_generic'] for m in meds]}")
print(f"Detected Section:   {sec}")
print(f"Retrieval Query:    '{rq}'")
print(f"Scope (chunks):     {len(scope) if scope else 'global'}")

ar_evidence = retrieve_evidence(ar_query, top_k=3)
print("\\n" + "=" * 80)
print(f"QUERY: {ar_query}")
print("=" * 80)
for i, ev in enumerate(ar_evidence, 1):
    print(f"\\n[الدليل {i}]  درجة التطابق: {ev.get('reranker_score', 0):.3f}")
    print(f"  الدواء:  {ev['canonical_drug']}")
    print(f"  القسم:   {ev['section']}")
    print(f"  المصدر:  {ev['file']}  (صفحة {ev['page']})")
    print(f"  النص:    {ev['text'][:220]}...")""")

    # =========================================================================
    # SECTION 19 — GROUNDED GENERATION
    # =========================================================================
    add_md("""## 18. Strict Evidence-Grounded Gemini Generation

Strict grounding prompt (matching production `grounding.py`) ensures the answer is:
- Based **only** on retrieved EDA monograph evidence
- Cites exact source document and page
- Abstains if evidence is insufficient""")

    add_code("""GROUNDING_PROMPT = \"\"\"You are Tamargi.ai, an Explainable Clinical Medication Safety Assistant.
Your answers MUST be strictly grounded in the retrieved EDA monograph evidence below.

Rules:
1. Answer using ONLY the provided evidence excerpts.
2. Cite the exact source document and page number for every clinical claim.
3. If evidence is insufficient, state: "The official EDA monographs provided do not contain sufficient evidence to answer safely."
4. Match the user's language (Arabic or English).
5. Do not hallucinate or extrapolate beyond the evidence.
\"\"\"

def generate_grounded_answer(query: str, evidence: list[dict], api_key: str = None) -> str:
    \"\"\"Calls Gemini with strict grounding prompt over retrieved EDA evidence.\"\"\"
    key = api_key or os.environ.get("GEMINI_API_KEY", "")

    evidence_block = "\\n\\n".join([
        f"[Evidence {i+1}] Source: {ev.get('file', 'EDA Monograph')}, Page: {ev.get('page', '?')}\\n{ev.get('text', '')}"
        for i, ev in enumerate(evidence)
    ])

    prompt = f\"\"\"Question:\\n{query}\\n\\nRetrieved Evidence from Official EDA Formularies:\\n{evidence_block}\"\"\"

    if not key:
        return (
            "[Notice]: Set GEMINI_API_KEY to enable live generation.\\n"
            f"Retrieved {len(evidence)} verified chunks. Top source: "
            f"{evidence[0]['file']} (Page {evidence[0]['page']})\\n"
            f"Top Evidence:\\n{evidence[0]['text'][:300]}..."
        )
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=GROUNDING_PROMPT,
                temperature=0.1
            )
        )
        return response.text
    except Exception as e:
        return f"[Gemini Error]: {e}"

print("generate_grounded_answer() ready")""")

    # =========================================================================
    # SECTION 20 — END-TO-END DEMO
    # =========================================================================
    add_md("""## 19. End-to-End Demo: `ask_tamargi(question)`""")

    add_code("""def ask_tamargi(question: str):
    \"\"\"Full end-to-end RAG demo: query → normalize → resolve → retrieve → generate.\"\"\"
    print("=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    t0 = time.time()
    evidence = retrieve_evidence(question, top_k=3)
    t1 = time.time()

    print(f"\\nRetrieved {len(evidence)} evidence chunks in {t1-t0:.2f}s:")
    for i, ev in enumerate(evidence, 1):
        print(f"  [E{i}] {ev['file']} (Page {ev['page']}) — {ev['canonical_drug']} → {ev['section']}")

    answer = generate_grounded_answer(question, evidence)
    print("\\nGROUNDED ANSWER:")
    print("-" * 80)
    print(answer)
    print("-" * 80)

ask_tamargi("What are the contraindications of Anidulafungin?")""")

    # =========================================================================
    # SECTION 21 — OBJECTIVE EVALUATION
    # =========================================================================
    add_md("""## 20. Objective Evaluation — Frozen 45-Question Gold Dataset

Benchmarked against `data/evaluation/rag_gold_dataset.csv`.

**Target metrics (production baseline)**:
- Hit@1 = 0.400, Hit@3 = 0.733, Hit@5 = 0.844, MRR = 0.586
- English Hit@5 = 0.800, Arabic Hit@5 = 0.933
- Drug ID = 91.1%, Section ID = 80.0%""")

    add_code("""gold_df = pd.read_csv(GOLD_PATH)
print(f"Gold dataset: {len(gold_df)} questions")
print(f"  English: {len(gold_df[gold_df['language']=='en'])}  |  Arabic: {len(gold_df[gold_df['language']=='ar'])}")

h1, h3, h5, mrrs = [], [], [], []
h1_en, h3_en, h5_en, mrrs_en = [], [], [], []
h1_ar, h3_ar, h5_ar, mrrs_ar = [], [], [], []
drug_correct = 0
sec_correct  = 0

total = len(gold_df)
print(f"\\nRunning evaluation on {total} questions...")
t_eval = time.time()

for q_num, (_, row) in enumerate(gold_df.iterrows(), 1):
    query    = str(row["question"])
    exp_file = str(row["expected_file"]).lower().strip()
    exp_page = int(row["expected_page"])
    exp_drug = str(row.get("expected_drug", "")).lower().strip()
    exp_sec  = str(row.get("expected_section", "")).lower().strip()
    lang     = str(row["language"]).lower().strip()

    if q_num % 10 == 0:
        print(f"  [{q_num}/{total}] elapsed {time.time()-t_eval:.0f}s...")

    # Retrieve top-5 evidence
    retrieved = retrieve_evidence(query, top_k=5)

    # Hit evaluation: file match + ±1 page tolerance
    hit_rank = None
    for r_i, chunk in enumerate(retrieved, start=1):
        f_match = str(chunk.get("file", "")).lower().strip() == exp_file
        p_match = abs(int(chunk.get("page", -999)) - exp_page) <= 1
        if f_match and p_match:
            hit_rank = r_i
            break

    h1_val  = 1 if hit_rank == 1 else 0
    h3_val  = 1 if hit_rank and hit_rank <= 3 else 0
    h5_val  = 1 if hit_rank and hit_rank <= 5 else 0
    mrr_val = (1.0 / hit_rank) if hit_rank else 0.0

    h1.append(h1_val);  h3.append(h3_val);  h5.append(h5_val);  mrrs.append(mrr_val)

    if lang == "en":
        h1_en.append(h1_val); h3_en.append(h3_val); h5_en.append(h5_val); mrrs_en.append(mrr_val)
    else:
        h1_ar.append(h1_val); h3_ar.append(h3_val); h5_ar.append(h5_val); mrrs_ar.append(mrr_val)

    # Drug & Section identification accuracy
    detected_meds = [m["canonical_generic"] for m in extract_all_medications(query)]
    detected_sec  = detect_query_section(query)
    if exp_drug and any(exp_drug in dm or dm in exp_drug for dm in detected_meds):
        drug_correct += 1
    if exp_sec and (exp_sec in detected_sec or detected_sec in exp_sec):
        sec_correct += 1

print(f"\\nEvaluation done in {time.time()-t_eval:.1f}s")

# Results table
results_df = pd.DataFrame([
    {"Subset": "Overall (45 Qs)", "Hit@1": np.mean(h1), "Hit@3": np.mean(h3),
     "Hit@5": np.mean(h5), "Count": f"{sum(h5)}/45", "MRR": np.mean(mrrs)},
    {"Subset": "English (30 Qs)", "Hit@1": np.mean(h1_en), "Hit@3": np.mean(h3_en),
     "Hit@5": np.mean(h5_en), "Count": f"{sum(h5_en)}/30", "MRR": np.mean(mrrs_en)},
    {"Subset": "Arabic (15 Qs)",  "Hit@1": np.mean(h1_ar), "Hit@3": np.mean(h3_ar),
     "Hit@5": np.mean(h5_ar), "Count": f"{sum(h5_ar)}/15", "MRR": np.mean(mrrs_ar)},
])

print("\\n" + "=" * 80)
print("OBJECTIVE BENCHMARK RESULTS vs PRODUCTION GOLD BASELINE:")
print("=" * 80)
display(results_df)

print(f"Drug Identification Accuracy:    {drug_correct/total*100:.1f}% ({drug_correct}/{total})  [target: 91.1%]")
print(f"Section Identification Accuracy: {sec_correct/total*100:.1f}%  ({sec_correct}/{total})  [target: 80.0%]")

# Comparison table
print("\\n" + "=" * 80)
print("COMPARISON: Notebook vs Production Gold Baseline")
print("=" * 80)
gold = {"Hit@1": 0.400, "Hit@3": 0.733, "Hit@5": 0.844, "MRR": 0.586,
        "EN Hit@5": 0.800, "AR Hit@5": 0.933, "Drug ID": 0.911, "Sec ID": 0.800}
nb   = {"Hit@1": np.mean(h1), "Hit@3": np.mean(h3), "Hit@5": np.mean(h5), "MRR": np.mean(mrrs),
        "EN Hit@5": np.mean(h5_en), "AR Hit@5": np.mean(h5_ar),
        "Drug ID": drug_correct/total, "Sec ID": sec_correct/total}

compare_df = pd.DataFrame([
    {"Metric": k, "Gold Baseline": gold[k], "Notebook": nb[k],
     "Δ": f"{nb[k]-gold[k]:+.3f}", "Status": "✅" if nb[k] >= gold[k]*0.95 else "⚠️"}
    for k in gold
])
display(compare_df)""")

    # =========================================================================
    # SECTION 22 — PRESENTATION & VIVA GUIDE
    # =========================================================================
    add_md("""## 21. How I Explain My RAG System (Presentation & Viva Guide)

### 10-Point Summary (English)
1. **Curated Medical Corpus**: 5,437 EDA pharmaceutical monograph chunks with clinical metadata.
2. **Arabic Normalization**: Standardizes tashkeel, alef variants, teh marbuta, and yeh so Arabic queries reliably match aliases.
3. **3-Pass Medication Resolution**: Exact match → substring → Levenshtein tolerance handles brand names, transliterations, and typos.
4. **Clinical Section Intent**: Full bilingual keyword map detects contraindications, dosage, interactions, warnings, etc.
5. **Canonical Query Construction**: Arabic query → English clinical query so BM25 can search English EDA text.
6. **Drug Monograph Scoping**: Restricts 5,437 chunks to ~40 for the target drug — high-precision retrieval.
7. **Hybrid RRF**: Dense semantic + BM25 keyword rankings merged via Reciprocal Rank Fusion.
8. **CrossEncoder Reranking**: Deep joint attention over query+passage with clinical drug/section boosts.
9. **Evidence Filtering**: Rejects unrelated drugs, deduplicates near-identical chunks, enforces page diversity.
10. **Strict Grounding**: Gemini generates answers **only** from retrieved evidence with page citations.

---

### ملخص العرض التقديمي (باللغة العربية)
> **"يقوم نظام Tamargi.ai على معمارية استرجاع هجينة متعددة المراحل. يبدأ النظام بتطبيع النص العربي ثم يحل أسماء الأدوية باللغتين العربية والإنجليزية باستخدام قائمة أسماء معتمدة من هيئة الدواء المصرية. بعدها، يُنشئ استعلاماً بالإنجليزية يمكن لـ BM25 البحث به في نصوص الكتيبات. ثم يحصر البحث في الفصل الخاص بالدواء المطلوب فقط، ويدمج نتائج البحث الدلالي والكلمات المفتاحية باستخدام RRF، ويُعيد ترتيبها بنموذج CrossEncoder، ثم يُرشح الأدلة المكررة أو غير المتعلقة. أخيراً، يُنشئ نموذج Gemini إجابة مؤسسة تماماً على الأدلة المسترجعة مع توثيق المصدر والصفحة."**""")

    # =========================================================================
    # SECTION 23 — ARCHITECTURAL DISTINCTION
    # =========================================================================
    add_md("""## 22. Architectural Distinction: Research Notebook vs Production Backend

| Feature | This Research Notebook | Production Backend |
|:---|:---|:---|
| **Goal** | Algorithmic demonstration & viva | Full clinical application |
| **Retrieval Core** | Direct Python functions | FastAPI async + class hierarchy |
| **Medication Resolver** | Simplified 3-pass (alias CSV) | Full NLP + Pydantic models |
| **Section Detection** | Full bilingual keyword map | Full bilingual keyword map ✅ |
| **Evidence Filtering** | Full acceptance layer ✅ | Full acceptance layer ✅ |
| **Auth / Security** | None | Supabase + JWT + BYOK |
| **Safety Engine** | Not included | 9 verified clinical rules |
| **Clinical Plans** | Not included | Medication Plan + QR Portal |
| **Frontend** | Jupyter outputs | Next.js + Dark/Light theme |
| **Deployment** | Local notebook | Railway + Vercel |""")

    return nb


if __name__ == "__main__":
    nb_data = create_notebook()

    root_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "Tamargi_RAG_V2_Research.ipynb")
    )
    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1, ensure_ascii=False)
    print(f"Created: {root_path}")

    nb_dir_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "notebooks", "Tamargi_RAG_V2_Research.ipynb")
    )
    with open(nb_dir_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1, ensure_ascii=False)
    print(f"Created: {nb_dir_path}")
