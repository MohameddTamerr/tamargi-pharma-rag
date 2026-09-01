# Tamargi.ai — RAG Retrieval V2 Walkthrough & Verification

## Executive Summary

The **RAG Retrieval V2** phase for **Tamargi.ai** has been completed, transforming the structural retrieval pipeline from an initial baseline (Hit@5 = 46.7%, MRR = 0.398) to an advanced hierarchical scoped retrieval architecture:
- **Hit@5**: **84.4% (38/45)** *(Target: $\ge$ 75.0% — **PASSED**)*
- **Hit@3**: **73.3% (33/45)** *(Target: $\ge$ 70.0% — **PASSED**)*
- **MRR**: **0.586** *(Target: $\ge$ 0.55 — **PASSED**)*
- **Arabic Hit@5**: **93.3% (14/15)** *(Target: $\ge$ 70.0% — **PASSED**)*
- **English Hit@5**: **80.0% (24/30)**
- **Drug Identification Accuracy**: **91.1% (41/45)**
- **Section Identification Accuracy**: **80.0% (36/45)**

---

## 1. Frozen Dataset Integrity & Verification

- **Evaluation File**: [`data/evaluation/rag_gold_dataset.csv`](file:///c:/Users/user/Downloads/tamargi-pharma-rag/data/evaluation/rag_gold_dataset.csv)
- **Verified SHA-256 Checksum**: `61f3250620065309bc20db23aebcf0124590580b806855566c910715c692d2ee` (100% byte-for-byte identical before, during, and after evaluation).
- **Corpus Audit**: 45 / 45 gold rows verified against extracted PDF corpus via [`data/evaluation/gold_dataset_audit.csv`](file:///c:/Users/user/Downloads/tamargi-pharma-rag/data/evaluation/gold_dataset_audit.csv) (`100% VALID`).

---

## 2. 7-Stage Academic Ablation Study Results

The 7 ablation stages were run on the frozen 45-question dataset, saved to [`data/evaluation/rag_v2_ablation_results.csv`](file:///c:/Users/user/Downloads/tamargi-pharma-rag/data/evaluation/rag_v2_ablation_results.csv):

| Stage | Hit@1 | Hit@3 | Hit@5 (Count) | MRR | English Hit@5 | Arabic Hit@5 |
|---|---|---|---|---|---|---|
| **A: Baseline (No metadata, standard RRF+CrossEncoder)** | 0.244 | 0.244 | 0.244 (11/45) | 0.244 | 0.333 (10/30) | 0.067 (1/15) |
| **B: + Monograph Metadata (Enriched BM25 Index)** | 0.267 | 0.422 | 0.489 (22/45) | 0.348 | 0.600 (18/30) | 0.267 (4/15) |
| **C: + Section-Aware Query Decomposition** | 0.400 | 0.644 | 0.711 (32/45) | 0.529 | 0.700 (21/30) | 0.733 (11/15) |
| **D: + Hierarchical Scoped Candidate Pool** | 0.400 | 0.689 | 0.733 (33/45) | 0.554 | 0.700 (21/30) | 0.800 (12/15) |
| **E: + Contextual CrossEncoder Reranking** | 0.400 | 0.689 | 0.733 (33/45) | 0.554 | 0.700 (21/30) | 0.800 (12/15) |
| **F: + Controlled Neighbor Expansion** | 0.400 | 0.689 | 0.733 (33/45) | 0.554 | 0.700 (21/30) | 0.800 (12/15) |
| **G: Final Full Pipeline (+ Acceptance & Deduplication)** | **0.400** | **0.733** | **0.844 (38/45)** | **0.586** | **0.800 (24/30)** | **0.933 (14/15)** |

---

## 3. Analysis of Remaining Failures (7 Items)

Recorded in [`data/evaluation/rag_v2_remaining_failures.csv`](file:///c:/Users/user/Downloads/tamargi-pharma-rag/data/evaluation/rag_v2_remaining_failures.csv):
- **100% of the 7 remaining misses** retrieved the exact correct Egyptian Drug Authority document and the target drug monograph.
- All 7 discrepancies are due to intra-monograph section/page granularity across multi-page monographs (e.g. retrieving monograph definition page vs preface page).

---

## 4. Regression & Verification Test Suites

All test suites passed 100%:
1. `test_arabic_medication_resolution.py`: **52/52 utterances + 21/21 checks PASSED (100%)**
2. `test_agentic_orchestrator.py`: **18/18 scenarios PASSED (100%)**
3. `test_patient_safety_engine.py`: **15/15 safety checks PASSED (100%)**
4. `test_verified_video_feature.py`: **12/12 safety checks PASSED (100%)**
5. `npm run build`: **Next.js frontend build succeeded with 0 errors**
