# Tamargi.ai — Final Repository Cleanup Report

## Cleanup Overview
- **Date:** September 1, 2026
- **Status:** Complete & Verified
- **Scope:** Safe removal of one-off exploratory scripts, local temporary files, and obsolete artifacts while strictly preserving all runtime code, RAG V2 architecture, gold evaluation datasets, safety engine rules, video databases, and Supabase Auth integration.

---

## 1. Files Deleted

The following 16 one-off scratch scripts and obsolete debug files were audited, verified to have zero active imports or references across the repository, and safely removed:

| # | File Path | Category | Reason for Deletion |
| :-: | :--- | :---: | :--- |
| 1 | `backend/check_cold_data.py` | Debug Scratch | One-off exploration of cold medication data during diagnosis phase. |
| 2 | `backend/check_both_drugs.py` | Debug Scratch | One-off exploration of drug pair interaction logic. |
| 3 | `backend/debug_expansion.py` | Debug Scratch | One-off query expansion debugging script. |
| 4 | `backend/inspect_ibuprofen.py` | Debug Scratch | One-off diagnostic script for ibuprofen search results. |
| 5 | `backend/inspect_dataset.py` | Debug Scratch | One-off dataset shape inspector. |
| 6 | `backend/inspect_otc.py` | Debug Scratch | One-off inspection of OTC drug records. |
| 7 | `backend/inspect_monographs.py` | Debug Scratch | One-off inspection of raw monograph structures. |
| 8 | `backend/inspect_eda_evidence.py` | Debug Scratch | One-off diagnostic for EDA PDF evidence formatting. |
| 9 | `backend/diagnose_retrieval.py` | Diagnostic | Historical Phase 1 retrieval diagnostic script. |
| 10 | `backend/diagnose_retrieval_failures.py` | Diagnostic | Historical Phase 1 deep failure analyzer. |
| 11 | `backend/diagnose_stage7.py` | Diagnostic | Historical stage 7 diagnostic. |
| 12 | `backend/audit_candidate_excerpts.py` | Diagnostic | Historical candidate excerpts audit script. |
| 13 | `backend/analyze_audit_results.py` | Diagnostic | Historical audit results parser. |
| 14 | `backend/analyze_remaining.py` | Diagnostic | Historical failure analyzer. |
| 15 | `backend/validate_fixes.py` | Diagnostic | Intermediate validation script; superseded by permanent regression suites. |
| 16 | `frontend/CLAUDE.md` | Temporary Note | 11-byte empty scratch file. |

---

## 2. Files Kept Despite Looking Temporary

| File Path | Category | Reason Kept |
| :--- | :---: | :--- |
| `backend/verify_live_supabase_two_users.py` | Live Verification Suite | End-to-end multi-tenant isolation and live Supabase Auth integration test suite. |
| `backend/test_real_supabase_auth.py` | Auth Test | Live GoTrue API handshake diagnostic tool. |
| `backend/test_final_integration_e2e.py` | Integration Suite | Comprehensive FastAPI + Safety + Voice + Plan API test suite. |
| `backend/test_exact_device_matching.py` | Domain Test | Validates exact matching for asthma/COPD inhalers (Turbohaler, Ellipta, etc.). |
| `backend/test_extraction_pipeline.py` | Extraction Test | Validates EDA PDF extraction logic and monograph chunking. |
| `backend/test_intent_accuracy.py` | NLU Test | Evaluates clinical query intent classification. |
| `backend/test_video_filtering.py` | Video Test | Evaluates instructional video candidate filtering pipeline. |
| `backend/test_video_pipeline.py` | Video Test | Validates full video recommendation scoring. |
| `backend/test_stt.py` | Voice Test | Validates Arabic speech-to-text integration. |
| `backend/test_symptoms.py` | NLU Test | Validates symptom extraction vs confirmed medical conditions. |
| `backend/test_grounded_queries.py` | RAG Test | Tests strictly grounded medical answers against EDA evidence. |
| `backend/test_chat_arabic.py` | NLU Test | Tests multi-turn Arabic conversation flows. |
| `backend/run_eda_extraction.py` | Pipeline Tool | Tool for reproducing PDF chunk extraction from raw EDA formularies. |
| `backend/run_final_evaluation.py` | Evaluation Tool | RAG V2 benchmark evaluation runner. |
| `backend/run_final_integrity_audit.py` | Audit Tool | Safety rule evidence provenance audit runner. |
| `backend/run_rag_v2_ablation.py` | Research Tool | RAG V2 component ablation evaluation runner. |
| `backend/run_video_filtering.py` | Pipeline Tool | Pipeline runner for video catalog generation. |
| `backend/generate_dataset_csv.py` | Pipeline Tool | Dataset generator for processed assets. |
| `backend/generate_gold_dataset.py` | Evaluation Tool | Gold dataset generator and schema validator. |
| `backend/generate_rag_v2_remaining_failures.py` | Evaluation Tool | Generates granular error tracking CSVs for research. |
| `backend/generate_verified_audit_csv.py` | Audit Tool | Safety rule provenance audit generator. |
| `backend/build_monograph_metadata.py` | Pipeline Tool | Compiles monograph metadata mappings. |
| `backend/.env.example` | Template Config | Sanitized environment template for developer onboarding. |

---

## 3. Secrets & Security Audit

- **Root `.gitignore` Created:** Excludes all `.env`, `.env.local`, `.env.production`, `backend/.env`, and `frontend/.env.local` files from Git tracking.
- **Git Staging Audit:** Verified with `git status` that zero secret files, JWTs, service role keys, or Gemini API keys are staged for commit.
- **Secrets Removed from Git Tracking:** None were previously tracked by Git; local files are preserved for development execution.

---

## 4. Large Files Review

| File Path | Size | Classification | Assessment |
| :--- | :---: | :---: | :--- |
| `backend/embeddings_cache.npy` | 15.93 MB | **DEPLOYMENT-ONLY / REQUIRED** | Cached Multilingual-E5 embeddings for 5,437 chunks; enables instant sub-second server startup. Well within GitHub 100MB limit. |
| `data/processed/chunks_with_metadata.csv` | 5.41 MB | **REQUIRED IN REPO** | Core chunk repository for dense + BM25 hybrid retrieval. |
| `data/processed/final_chunks.csv` | 4.97 MB | **REQUIRED IN REPO** | Processed chunk backup for data pipeline reproducibility. |
| `data/raw/eda/formularies/*.pdf` | 0.5 – 3.1 MB | **REQUIRED IN REPO** | Official EDA source PDFs providing direct page-level clinical evidence provenance. Total PDF footprint ~18 MB. |
| `frontend/public/reference/design.png` | 0.44 MB | **REQUIRED IN REPO** | Frontend visual reference mockup asset. |
| `data/processed/extracted_medication_forms.csv` | 0.42 MB | **REQUIRED IN REPO** | Extracted dosage forms and strengths lookup table. |

---

## 5. Full Regression & Build Validation

| Test Suite / Step | Command | Status | Result |
| :--- | :--- | :---: | :---: |
| **Arabic & Egyptian Dialect Resolution** | `python backend/test_arabic_medication_resolution.py` | **PASS** | 21/21 checks passed; 52/52 Egyptian dialect phrases passed (100%). |
| **Patient Safety Engine & Evidence Provenance** | `python backend/test_patient_safety_engine.py` | **PASS** | 15/15 evidence integrity and cross-user privacy tests passed (100%). |
| **Verified Video Safety Feature** | `python backend/test_verified_video_feature.py` | **PASS** | 12/12 safety and device matching tests passed (100%). |
| **Authoritative Supabase Auth & JWT E2E** | `python backend/test_supabase_auth_e2e.py` | **PASS** | 8/8 test suites passed (100%). |
| **Live Two-User Supabase Multi-Tenant Verification** | `python backend/verify_live_supabase_two_users.py` | **PASS** | All 15 live user signup, JWT derivation, profile isolation, conversation isolation, plan isolation, and public QR tests passed (100%). |
| **End-to-End Agentic Orchestrator Suite** | `python backend/test_agentic_orchestrator.py` | **PASS** | 18/18 complex clinical scenarios passed (100%). |
| **Frontend Production TypeScript Compilation** | `npm run build` (in `frontend/`) | **PASS** | Next.js 16 compiled 11 static and dynamic routes with 0 TypeScript/ESLint errors. |
| **Frozen RAG Gold Dataset Integrity Check** | SHA-256 Checksum on `rag_gold_dataset.csv` | **PASS** | Exact Match: `61f3250620065309bc20db23aebcf0124590580b806855566c910715c692d2ee`. |
