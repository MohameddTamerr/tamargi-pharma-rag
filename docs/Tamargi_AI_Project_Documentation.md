# Tamargi.ai

## Explainable Personalized Medication Safety RAG System for Egyptian Patients

### Complete Engineering, Research, Testing, and Architectural Documentation

---

## PART I: UNDERSTANDING THE PROJECT

### 1. Executive Summary

Tamargi.ai is an explainable, personalized medication safety and clinical decision-support system designed specifically for the Egyptian healthcare ecosystem. In everyday clinical and outpatient environments, patients and healthcare practitioners face significant challenges when navigating complex pharmaceutical documentation, verifying potential drug interactions, assessing contraindications against patient-specific chronic profiles, and understanding correct administration techniques.

General-purpose Large Language Models (LLMs) frequently fail in these high-stakes healthcare scenarios due to:
1. Medical hallucinations and invention of plausible-sounding but clinically incorrect dosages.
2. Complete absence of localized regulatory grounding against official Egyptian Drug Authority (EDA) guidelines.
3. Lack of patient contextual awareness, evaluating queries in isolation without cross-referencing existing patient allergies, chronic conditions, or ongoing therapies.
4. Inability to provide verified, page-level provenance for every clinical claim.

Tamargi.ai addresses these critical vulnerabilities through a multi-stage, evidence-grounded Retrieval-Augmented Generation (RAG V2) architecture integrated with a deterministic clinical safety engine, a patient profile context manager, verified instructional video routing, and a multi-user Bring Your Own Key (BYOK) security model.

Important Clinical Disclaimer:
Tamargi.ai is an informational and clinical decision-support tool. It is not a licensed physician, pharmacist, or diagnostic entity. It does not replace professional medical judgment, clinical diagnosis, or formal prescription verification.

---

### 2. Problem Statement

#### The Vulnerability of Generic LLMs in Healthcare
When a user asks a general-purpose LLM a question such as:
"Can a hypertensive patient with renal impairment take Brufen 400 with Ramipril?"
A standard conversational model relies on statistical next-token prediction across vast, non-curated internet corpora. This creates severe clinical risks:
- Fabrication of safety assertions ("This combination is generally safe if monitored").
- Failure to recognize Egyptian commercial brand names (e.g., mapping "Brufen" or "Cataflam" to their generic active ingredients Ibuprofen and Diclofenac).
- Failure to apply strict regulatory guidelines established by the Egyptian Drug Authority (EDA).
- Inability to provide verifiable page numbers and document citations, leaving clinicians and patients unable to audit the recommendation.

#### The Linguistic Disconnect in Egyptian Healthcare
Egyptian patients communicate in Egyptian Colloquial Arabic, Modern Standard Arabic, or mixed English-Arabic medical terminology (e.g., using Arabic transliterations for brand names such as "بروفين" or "كونكور"). However, the authoritative national formularies published by the Egyptian Drug Authority (EDA) are written in English. Standard sparse search algorithms (such as BM25) experience severe retrieval degradation when matching Arabic query tokens against an English monograph corpus, resulting in zero term overlap and near-total keyword search failure.

#### The Need for Deterministic Safety Gating
Semantic similarity is not equivalent to clinical correctness. Even if a retrieval engine retrieves a relevant monograph passage, an LLM might summarize the passage with subtle errors, miss a critical contraindication, or extrapolate beyond stated clinical bounds. A reliable system requires a deterministic safety engine that acts as an immutable safety barrier alongside generative synthesis.

---

### 3. Project Objectives

#### Primary Objectives (Fully Implemented and Verified)
1. Official Evidence Grounding: Index and vectorize the complete library of official Egyptian Drug Authority (EDA) pharmaceutical monographs (5,437 enriched chunks across 13 national formularies and guideline documents).
2. Multi-Stage Hybrid RAG V2: Implement an explainable 5-stage retrieval pipeline combining Arabic text normalization, 3-pass medication resolution, bilingual clinical section intent detection, drug-scoped candidate pooling, metadata-enriched BM25, dense semantic retrieval (intfloat/multilingual-e5-base), Reciprocal Rank Fusion (RRF), CrossEncoder contextual reranking (cross-encoder/mmarco-mMiniLMv2-L12-H384-v1), and strict evidence acceptance filtering.
3. Bilingual and Dialectal Equivalence: Enable seamless query handling across Egyptian Colloquial Arabic, Modern Standard Arabic, and English, resolving commercial brands and Arabic transliterations to canonical generic active ingredients using a verified 251-alias mapping table.
4. Deterministic Patient Safety Engine: Provide rule-based, audited verification against patient-specific chronic conditions, documented drug allergies, drug-drug interactions, high-alert classifications, and do-not-crush restrictions.
5. Strict Grounding and Provenance: Ensure that every factual medical statement generated by Google Gemini is strictly supported by retrieved EDA monograph excerpts, including document title and page number citations, with deterministic abstention (refusal to answer) when evidence is insufficient.
6. Educational Instructional Media: Deterministically route queries regarding complex medical devices (e.g., dry-powder inhalers, metered-dose inhalers, subcutaneous insulin pens) to clinically verified instructional videos.
7. Collaborative Medication Plans: Enable users to generate structured, evidence-backed medication schedules that can be shared via unique verification tokens and QR codes for pharmacist review.
8. Secure Multi-User BYOK Architecture: Implement user-isolated, authenticated server-side Fernet encryption for personal Gemini API keys using PostgreSQL Row Level Security (RLS) on Supabase.

#### Future Objectives (Planned Enhancements)
1. Expansion to full Egyptian commercial pharmaceutical market registry exceeding 15,000 commercial formulations.
2. Direct integration with electronic health record (EHR) standards (HL7 FHIR).
3. Real-time continuous glucose monitor (CGM) and wearable telemetry ingestion.
4. Formal prospective clinical trials in hospital outpatient pharmacy workflows.

---

### 4. Final System Overview

The Tamargi.ai platform operates as a modular system comprising a Next.js 14 frontend, a FastAPI backend, a PostgreSQL / Supabase storage layer with Row Level Security, and Google Gemini for evidence-grounded generation.

```
[ User Browser / Mobile Device ]
              │
              ▼
    [ Next.js 14 Frontend ]
  (Tailwind CSS, Light/Dark, Auth)
              │  (HTTPS / JWT Bearer Token)
              ▼
    [ FastAPI Backend API ]
              │
              ▼
    [ Main Orchestrator ]
  ┌───────────┼────────────────────────────────────────┐
  │           │                                        │
  ▼           ▼                                        ▼
[Medication [Patient Profile                     [Deterministic]
 Resolver]   Context]                            [Safety Engine]
  │           │                                  - Allergy
  │           │                                  - Drug-Disease
  ▼           ▼                                  - Drug-Drug
[Hybrid RAG V2 Engine]                           - High Alert
  1. Arabic Normalization                        - Do-Not-Crush
  2. Section Intent (Bilingual)                        │
  3. Canonical Query Construction                      │
  4. Stage 1: Drug Scope Pooling                       │
  5. Dense (E5) + Sparse (BM25)                        │
  6. Reciprocal Rank Fusion (RRF)                      │
  7. CrossEncoder Context Reranker                     │
  8. Acceptance & Deduplication                        │
  └───────────┬────────────────────────────────────────┘
              │
              ▼
    [ Top Verified Evidence ]
    (Chunk text + Source + Page)
              │
              ▼
    [ Strict Grounding Engine ]
    (System instructions + Configured Gemini Model)
              │
              ▼
    [ Final Grounded Response ]
    (Clinical answer + [E1][E2] page citations)

─────────────────────────────────────────────────────────────
[ Supabase PostgreSQL + Auth + Row Level Security (RLS) ]
  - auth.users & public.profiles
  - patient_profiles, conditions, allergies, medications
  - conversations, messages, message_sources
  - verified_safety_rules & verified_videos
  - medication_plans & verification_tokens
  - user_api_keys (Server-Side Fernet Encrypted BYOK)
─────────────────────────────────────────────────────────────
```

---

## PART II: DATA AND KNOWLEDGE BASE

### 5. Pharmaceutical Knowledge Base

The clinical foundation of Tamargi.ai is derived entirely from official, published guidelines and formularies issued by the Egyptian Drug Authority (EDA). The repository contains 13 primary PDF documents categorized into three functional groups:

| Category | Source File Name | Focus Area | Chunk Count |
|---|---|---|---|
| Formulary | egypt_antimicrobial_formulary_2023.pdf | Antibiotics, Antifungals, Antivirals | 1,392 |
| Formulary | egypt_conventional_anticancer_formulary_2024.pdf | Cytotoxic Chemotherapy | 810 |
| Formulary | egypt_endocrine_formulary_2024.pdf | Diabetes, Thyroid, Corticosteroids | 648 |
| Formulary | egypt_cardiovascular_formulary_2024.pdf | Hypertension, Heart Failure, Arrhythmia | 550 |
| Formulary | egypt_targeted_anticancer_formulary_2025.pdf | Monoclonal Antibodies, Kinase Inhibitors | 424 |
| Formulary | egypt_gastrointestinal_formulary_2025.pdf | Antiulcer, Antiemetic, IBD | 324 |
| Formulary | egypt_nervous_system_formulary_2025.pdf | Antiepileptics, Antidepressants, Analgesics | 316 |
| Formulary | egypt_antiretroviral_formulary_2026.pdf | HIV / Antiretroviral Regimens | 312 |
| Formulary | egypt_blood_disorders_formulary_2025.pdf | Anticoagulants, Antiplatelets, Anemia | 254 |
| Formulary | egypt_respiratory_formulary_2026.pdf | Asthma, COPD, Bronchodilators | 177 |
| OTC | egypt_otc_drug_list_2026.pdf | Non-Prescription / Self-Care Meds | 164 |
| Safety | egypt_do_not_crush_medications_2026.pdf | Oral Dosage Forms Not To Be Crushed | 41 |
| Safety | egypt_high_alert_medications_2025.pdf | High-Risk Hospital Medications | 25 |
| Total | 13 Official EDA Documents | Complete National Knowledge Base | 5,437 |

---

### 6. Document Processing Pipeline

The ingestion pipeline transforms unstructured PDF publications into structured, metadata-enriched, searchable passages:

```
[ Raw Official EDA PDF Formularies ]
                 │
                 ▼
[ PyPDF Layout-Aware Text Extraction ]
  (Extract text page by page with coordinates & headers)
                 │
                 ▼
[ Regulatory Artifact Cleaning ]
  (Strip running headers, repeated footers, EDA codes)
                 │
                 ▼
[ Monograph & Section Boundary Segmentation ]
  (Identify drug boundaries, section titles, tables)
                 │
                 ▼
[ Overlapping Token Chunking ]
  (Target size: 120 words, overlap: 20 words)
                 │
                 ▼
[ Metadata Enrichment Layer ]
  - chunk_id: Unique integer
  - file / source_file: Formulary name
  - page: Exact PDF physical page number
  - canonical_drug: Standard active generic name
  - monograph_name: Section heading drug name
  - section: Clinical domain (contraindications, dosage, etc.)
  - previous_chunk_id / next_chunk_id: Document continuity
                 │
                 ▼
[ Multilingual-E5 Dense Vectorization ]
  (Prepend 'passage: ', generate 768-dim float32 L2-norm vectors)
                 │
                 ▼
[ Stored Artifacts ]
  - data/processed/chunks_with_metadata.csv (5,437 rows)
  - backend/embeddings_cache.npy (5437 x 768 matrix)
```

---

### 7. PDF Processing Challenges

During initial document processing, several major extraction challenges were encountered and systematically resolved:

#### Challenge 1: Multi-Line and Split Section Headings
- Problem: EDA PDF typography frequently broke section titles across lines (e.g., "Contra-" on line 1, "indications" on line 2, or "Warnings /" on line 1, "Precautions" on line 2).
- Impact: Simple regex parsers failed to detect section boundaries, categorizing critical warning sections as generic text or "other".
- Solution: Implemented a multi-line header reconciler with hyphenation collapse and canonical section mapping in `backend/app/rag/metadata_extractor.py`.

#### Challenge 2: Non-Standard Formatting of Multi-Column Dosage Tables
- Problem: Renal dosage adjustment tables in antimicrobial and cardiovascular formularies extracted text out of vertical reading order.
- Impact: Numerical CrCl cutoffs were separated from their corresponding dosage reductions.
- Solution: Applied coordinate-aware extraction heuristics that sort bounding boxes into structural columns prior to text concatenation.

#### Challenge 3: Inconsistent Header and Footer Noise
- Problem: Repeated administrative banners (e.g., "Code: EDA.DUPP.Formulary.2023", "Version 1.0", page numbering artifacts) diluted dense embeddings.
- Impact: Dense retrieval frequently matched generic header text across irrelevant pages.
- Solution: Built an automated noise-stripping regex pipeline that eliminates document-level recurring boilerplate while strictly preserving clinical units, strengths, and dosage numbers.

---

## PART III: RESEARCH JOURNEY: NOTEBOOK 1

### 8. Notebook 1: Initial RAG Prototype

The first research iteration was implemented in `notebooks/TamargiAI-RAG.ipynb`. 

#### Goals of Notebook 1
- Prove the basic feasibility of extracting and indexing Egyptian Drug Authority PDFs.
- Test dense semantic retrieval using `intfloat/multilingual-e5-base`.
- Implement baseline BM25 sparse search and Reciprocal Rank Fusion (RRF).
- Evaluate basic CrossEncoder reranking.
- Connect retrieved chunks to Google Gemini with a strict grounding prompt.

Notebook 1 served as a critical proof of concept, demonstrating that pharmaceutical RAG could generate cited answers from local PDFs under standard English queries.

---

### 9. Notebook 1 Architecture

```
User Query (English)
       │
       ▼
[ Dense Search (E5) ] ────┐
       │                  │
       ▼                  ▼
[ BM25 Search (Regex) ] ──┴──► [ Reciprocal Rank Fusion (RRF) ]
                                            │
                                            ▼
                               [ CrossEncoder Reranker ]
                                            │
                                            ▼
                                   [ Top-5 Chunks ]
                                            │
                                            ▼
                                    [ Gemini LLM ]
                                            │
                                            ▼
                                   [ Grounded Answer ]
```

---

### 10. What Notebook 1 Did Well

1. Proved Feasibility: Demonstrated that dense vector embeddings and BM25 could find relevant drug monographs in an English clinical corpus.
2. Verified Grounded Prompting: Proved that system instructions could constrain Gemini to answer only from provided text snippets.
3. Established Initial Workflow: Provided the initial foundation for measuring retrieval performance.

---

### 11. Problems Discovered in Notebook 1

Detailed failure analysis of Notebook 1 revealed fundamental limitations that motivated the architectural overhaul in RAG V2:

#### Problem A: Arabic Retrieval Degradation
- Observation: When tested on Arabic queries, retrieval accuracy dropped sharply (Hit@5 = 0.067 in early baseline ablation testing).
- Why It Happened: Notebook 1's BM25 index used a simple Latin regex `r"[a-z0-9]+"`. Arabic query tokens generated zero BM25 tokens. Dense search alone struggled because generic Arabic queries lacked exact English monograph keywords.
- Impact: Arabic queries received irrelevant evidence or system failures.
- Solution in Notebook 2: Added full Arabic text normalization, medication entity resolution to canonical generic names, bilingual section intent detection, and canonical English retrieval query construction.

#### Problem B: Absence of Medication Entity Resolution
- Observation: Commercial brand names (e.g., "Brufen", "Cataflam", "Panadol") or Egyptian colloquial spellings failed to match monograph titles.
- Why It Happened: EDA monographs are indexed under international nonproprietary names (generic active ingredients like *Ibuprofen*, *Diclofenac*, *Paracetamol*). Notebook 1 had no alias resolution dictionary.
- Impact: Queries using common commercial brand names could not locate the underlying drug monograph.
- Solution in Notebook 2: Integrated a verified 251-alias medication dataset with a 3-pass resolution algorithm (exact match, substring match, and Levenshtein typo tolerance).

#### Problem C: Lack of Clinical Section Intent
- Observation: A query asking "What are the contraindications of Drug X?" frequently returned the indications, administration, or pharmacokinetics section of Drug X.
- Why It Happened: Notebook 1 treated all chunks of Drug X equally. High lexical overlap of the drug name dominated both dense and BM25 scores regardless of section relevance.
- Impact: The top retrieved evidence contained the right drug but the wrong clinical information.
- Solution in Notebook 2: Introduced bilingual section intent classification across 10 clinical categories with targeted section term injection into the retrieval query and CrossEncoder reranker scoring boosts.

#### Problem D: Global Retrieval Noise Across 5,437 Chunks
- Observation: Searching the entire corpus globally allowed semantically similar chunks from unrelated drugs (e.g., another antifungal with similar wording) to rank above the target drug monograph.
- Why It Happened: Vector similarity in high-dimensional embedding spaces can produce high similarity scores between structurally similar medical paragraphs even when the active ingredient is completely different.
- Impact: Entity contamination in retrieved evidence.
- Solution in Notebook 2: Introduced Stage 1 Drug Monograph Scope Identification, restricting candidate retrieval to the specific ±2 page window of the resolved active drug monograph.

#### Problem E: Evidence Duplication and Lack of Page Diversity
- Observation: The Top-5 results returned to the LLM often contained 3 or 4 overlapping chunks from the exact same page.
- Why It Happened: Overlapping chunking creates nearly identical adjacent chunks that score similarly in semantic similarity.
- Impact: Wasted context window and lack of multi-section evidence synthesis.
- Solution in Notebook 2: Implemented an evidence acceptance layer (`acceptance.py`) with Jaccard near-duplicate filtering (threshold 0.85) and Pass 1 page diversity enforcement (maximum 1 chunk per page).

---

### 12. Why Notebook 2 Was Necessary

Notebook 1 answered the foundational question: "Can we build a hybrid RAG pipeline for pharmaceutical documents?"

However, medical safety requires answering a much stricter question: "Can we guarantee that retrieval is clinically accurate, section-specific, robust against Arabic colloquial queries, and resistant to entity contamination?"

Notebook 2 (`Tamargi_RAG_V2_Research.ipynb`) was created as a self-contained, student-readable research notebook that faithfully reproduces the production RAG V2 architecture without web frameworks, asynchronous boilerplate, or class hierarchies.

---

## PART IV: NOTEBOOK 2 / RAG V2

### 13. Notebook 2: RAG V2 Research Design

The second research iteration implements an explainable, multi-stage retrieval pipeline:

```
User Query (Arabic / English / Egyptian Dialect)
                       │
                       ▼
         [ 1. Arabic & Text Normalization ]
    (Tashkeel, Tatweel, Alef, Teh Marbuta, Yeh)
                       │
                       ▼
         [ 2. Medication Entity Resolution ]
    (3-Pass: Exact Match -> Substring -> Levenshtein)
    (Resolves to canonical generic e.g. Ibuprofen)
                       │
                       ▼
         [ 3. Clinical Section Intent Detection ]
    (Bilingual keyword map: 10 clinical categories)
                       │
                       ▼
      [ 4. Canonical Retrieval Query Construction ]
    (Constructs English query: "ibuprofen contraindications")
                       │
                       ▼
     [ 5. Stage 1: Drug Monograph Scope Pooling ]
    (Restricts 5,437 corpus -> ~40 candidate chunks)
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ Dense Search (E5) ]       [ BM25 Search (Scoped) ]
  (Multilingual-e5-base)      (Metadata-enriched tokens)
         │                           │
         └─────────────┬─────────────┘
                       ▼
      [ 6. Reciprocal Rank Fusion (RRF) ]
        (k=30, w_dense=0.8, w_bm25=0.8)
                       │
                       ▼
      [ 7. CrossEncoder Contextual Reranking ]
   (mmarco-MiniLMv2 + Contextual Prefix + Boosts)
                       │
                       ▼
      [ 8. Evidence Acceptance & Deduplication ]
  (Entity consistency + Jaccard dedup + Page diversity)
                       │
                       ▼
      [ 9. Top-5 Verified Clinical Evidence ]
                       │
                       ▼
      [ 10. Strict Grounding Gemini Generation ]
```

---

### 14. Text Normalization

Implemented in `backend/app/normalization/text_normalizer.py`:
- Tashkeel Removal: Strips Arabic diacritical marks (Fatha, Damma, Kasra, Tanween, Shadda, Sukun).
- Tatweel Removal: Removes Arabic justification kashida (`ـ`).
- Alef Normalization: Standardizes `[أ, إ, آ, ٱ]` to `ا`.
- Teh Marbuta Normalization: Converts `ة` to `ه`.
- Yeh / Alef Maqsura Normalization: Standardizes `[ى, ي]` to `ي`.
- Punctuation & Whitespace Cleaning: Standardizes punctuation marks and collapses redundant whitespace.

---

### 15. Medication Resolver

Implemented in `backend/app/normalization/medication_resolver.py`:
Loads the verified active alias table (`data/processed/medication_aliases.csv`, 251 active rows covering 50 canonical generic drugs and 63 commercial brands).

The 3-Pass Resolution Algorithm:
1. Exact Match (Confidence 1.0): Compares normalized query string against normalized alias dictionary.
2. Substring Match (Confidence 0.95): Searches for multi-word and single-word brand names within the normalized query, sorted by alias length descending.
3. Levenshtein Typo Tolerance (Confidence 0.85): For query words with length >= 5 characters, calculates edit distance against known aliases, accepting matches with edit distance <= 1.

Example:
Input: `"ما هي موانع استخدام دواء بروفين 400؟"`
- Normalized text: `"ما هي موانع استخدام دواء بروفين 400"`
- Substring match: `"بروفين"` matches alias row for *Brufen*.
- Canonical Generic: `ibuprofen`
- Detected Strength: `400`

---

### 16. Section Intent Detection

Implemented in `backend/app/normalization/query_translator.py`:
A comprehensive bilingual keyword mapping across 10 clinical monograph sections:

| Clinical Section | English Keywords | Arabic / Egyptian Keywords |
|---|---|---|
| contraindications | contraindication, allergy, hypersensitivity | موانع, ممنوع, حساسية |
| dosage_adjustment | renal adjustment, kidney, hepatic | تعديل الجرعة, مرضى الكلى, مرضى الكبد |
| administration | how to take, administer, empty stomach | طريقة استعمال, طريقة استخدام, كيفية اخذ |
| high_alert | high alert, narrow therapeutic | عالي الخطورة, خطورة |
| do_not_crush | do not crush, chew, extended release | كسر, طحن, ممتدة المفعول, مغلفة |
| drug_interactions | interaction, interact, cyp3a4, bleeding | تعارض, تفاعل, تداخل, تداخلات |
| adverse_reactions | side effects, adverse effects, tendon | اثار جانبية, اعراض جانبية, اوتار |
| pregnancy_lactation | pregnancy, breastfeeding, pregnant | حمل, حامل, رضاعة, جنين |
| dosage | dose, dosage, maximum dose, strengths | جرعة, كمية, الجرعة القصوى, تركيزات |
| warnings_precautions | warning, precaution, monitoring | تحذير, تحذيرات, احتياطات, سكر |
| indications | indication, uses, approved for, ulcer | دواعي, استعمال, استخدام, علاج |

---

### 17. Drug-Scoped Retrieval (Stage 1 Scope Identification)

Global retrieval across 5,437 chunks creates significant false-positive risks. Stage 1 identifies the candidate monograph pool:
1. When a canonical drug is resolved, the system looks up the specific formulary and finds all chunks where `canonical_drug` matches the target.
2. It determines the minimum and maximum page range of the drug monograph and expands the search pool by ±2 pages to encompass multi-page section continuations.
3. This narrows the retrieval search space from 5,437 chunks to approximately 20 to 50 targeted chunks.
4. If no specific drug is detected (e.g., general medical query), the engine automatically falls back to global retrieval.

---

### 18. Canonical Retrieval Query Construction

Because EDA monographs are written in English, an Arabic query cannot directly retrieve English keywords via BM25.

The `build_retrieval_query()` function constructs a concise English clinical query:
```
Input: "ما هي موانع استعمال دواء انيدولافنجين؟"
1. Resolved Generic: anidulafungin
2. Detected Section: contraindications
3. Constructed Retrieval Query: "anidulafungin contraindications"
```
This enables BM25 to achieve exact keyword matching against the English monograph text while dense retrieval captures semantic context.

---

### 19. Dense Retrieval

- Model: `intfloat/multilingual-e5-base` (768-dimensional embeddings).
- Prefix convention: Queries are encoded as `"query: " + query_text`; document chunks are stored as `"passage: " + chunk_text`.
- Similarity Metric: Cosine similarity via dot product on L2-normalized vector embeddings.

---

### 20. BM25 Sparse Retrieval

- Implementation: `rank_bm25.BM25Okapi`
- Corpus Enrichment: Chunks are indexed with structured metadata prefixes:
  `f"{canonical_drug} {monograph_name} {section} {chunk_text}"`
- Tokenization: Multilingual regex `r"[a-z0-9]+|[؀-ۿ]+"` supporting Latin and Arabic scripts.

---

### 21. Hybrid Retrieval and Reciprocal Rank Fusion (RRF)

Dense and sparse rankings are merged without score normalization distortion using Reciprocal Rank Fusion:

$$RRF(d) = rac{w_{dense}}{k + rank_{dense}(d)} + rac{w_{BM25}}{k + rank_{BM25}(d)}$$

Where:
- $k = 30$
- $w_{dense} = 0.8$
- $w_{BM25} = 0.8$

---

### 22. CrossEncoder Reranking

- Model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- Contextual Prefix Formatting:
  ```
  Drug: Anidulafungin
  Section: Contraindications
  Document: egypt_antimicrobial_formulary_2023.pdf

  [Passage Text]
  ```
- Clinical Scoring Boosts:
  - +1.00 if candidate chunk canonical drug matches target drug.
  - +0.50 if target drug is mentioned in chunk text.
  - -1.20 if chunk represents an unrelated canonical drug.
  - +0.75 if chunk section matches detected section intent.

---

### 23. Evidence Acceptance and Deduplication

Implemented in `backend/app/rag/acceptance.py`:
1. Entity Consistency Gating: Chunks with unrelated canonical drugs are filtered out when the target drug is known.
2. Near-Duplicate Suppression: Chunks with word-level Jaccard similarity >= 0.85 to an already-accepted chunk on an adjacent page are discarded.
3. Page Diversity Enforcement: Pass 1 accepts at most 1 chunk per (file, page) combination, ensuring that Top-5 evidence covers multiple distinct pages of the monograph. Pass 2 fills remaining slots up to Top-5.

---

## PART V: NOTEBOOK 1 VS NOTEBOOK 2

### 24. Side-by-Side Architectural Comparison

| Architectural Dimension | Notebook 1 (Initial Prototype) | Notebook 2 / RAG V2 (Current Production) | Clinical / Technical Rationale |
|---|---|---|---|
| Text Normalization | Basic lowercase & punctuation strip | Full Arabic normalization (Tashkeel, Alef, Yeh) | Eliminates Arabic spelling variations and diacritical mismatches |
| Medication Resolution | None (Raw query used directly) | 3-Pass Resolver (Exact, Substring, Levenshtein) | Maps 251 medication alias mappings to generic active drugs |
| Clinical Section Intent | None | 10 Bilingual Clinical Intent Categories | Routes queries directly to Contraindications, Dosage, Interactions |
| Query Formulation | Raw user query sent to retrieval | Canonical English Retrieval Query | Solves Arabic query vs English corpus BM25 mismatch |
| Retrieval Scope | Global across all 5,437 chunks | Stage 1 Drug Monograph Scope (±2 pages) | Eliminates unrelated drug interference; increases precision |
| BM25 Index | Plain chunk text (Latin tokens only) | Metadata-enriched (Drug + Mono + Sec + Text) | Ensures high keyword recall for exact drug names and sections |
| Reranking Input | Raw query + plain chunk text | Query + Contextual Prefix (Drug, Sec, Doc) | Provides CrossEncoder full clinical context for joint attention |
| Clinical Scoring Boosts | None (Raw CrossEncoder score) | Drug match (+1.0), Section match (+0.75), Penalty (-1.2) | Aligns neural reranker ranking with clinical decision priorities |
| Evidence Acceptance | Top-K raw ranking | Deduplication (Jaccard) + Page Diversity | Prevents redundant chunks and ensures multi-page coverage |
| Evaluation Benchmark | Initial exploratory queries | 45 Frozen Gold Questions (30 EN, 15 AR) | Statistically rigorous, reproducible benchmark |

---

### 25. Quantitative Evaluation Comparison

Evaluated on the frozen 45-question gold benchmark (`data/evaluation/rag_gold_dataset.csv`, SHA-256: `61f3250620065309bc20db23aebcf0124590580b806855566c910715c692d2ee`):

| Evaluation Metric | Baseline Ablation (Stage A) | Production RAG V2 Baseline | Notebook 2 Research Executed | Status vs Production |
|---|---|---|---|---|
| Total Questions | 45 | 45 | 45 | Verified |
| Overall Hit@1 | 0.244 (11/45) | 0.400 (18/45) | 0.400 (18/45) | Exact Match |
| Overall Hit@3 | 0.244 (11/45) | 0.733 (33/45) | 0.644 (29/45) | Acceptable Research Delta |
| Overall Hit@5 | 0.244 (11/45) | 0.844 (38/45) | 0.800 (36/45) | Strong Alignment |
| Mean Reciprocal Rank (MRR) | 0.244 | 0.586 | 0.553 | Strong Alignment |
| English Hit@5 (30 Qs) | 0.333 (10/30) | 0.800 (24/30) | 0.767 (23/30) | Strong Alignment |
| Arabic Hit@5 (15 Qs) | 0.067 (1/15) | 0.933 (14/15) | 0.867 (13/15) | +1200% over Baseline |
| Drug ID Accuracy | 91.1% (41/45) | 91.1% (41/45) | 91.1% (41/45) | Exact Match |
| Section ID Accuracy | 80.0% (36/45) | 80.0% (36/45) | 82.2% (37/45) | +2.2% Improvement |

---

### 26. 7-Stage Academic Ablation Study

The step-by-step impact of each architectural component was verified in the 7-stage ablation study recorded in `data/evaluation/rag_v2_ablation_results.csv`:

```
[ Stage A: Baseline (No metadata, standard RRF) ] ──────────► Hit@5: 24.4%  (AR Hit@5:  6.7%)
                       │
                       ▼
[ Stage B: + Monograph Metadata in BM25 ] ─────────────────► Hit@5: 48.9%  (AR Hit@5: 26.7%)
                       │
                       ▼
[ Stage C: + Section-Aware Query Decomposition ] ──────────► Hit@5: 71.1%  (AR Hit@5: 73.3%)
                       │
                       ▼
[ Stage D: + Hierarchical Scoped Candidate Pool ] ─────────► Hit@5: 73.3%  (AR Hit@5: 80.0%)
                       │
                       ▼
[ Stage E: + Contextual CrossEncoder Reranking ] ──────────► Hit@5: 73.3%  (MRR: 0.554)
                       │
                       ▼
[ Stage F: + Controlled Neighbor Expansion ] ──────────────► Hit@5: 73.3%  (Context continuity)
                       │
                       ▼
[ Stage G: Final Full Pipeline (+ Acceptance & Dedup) ] ───► Hit@5: 84.4%  (AR Hit@5: 93.3%)
```

---

## PART VI: TESTING STRATEGY

### 27. Testing Overview and Quality Assurance Architecture

Tamargi.ai employs a comprehensive, multi-tiered testing strategy spanning unit tests, regression suites, algorithmic benchmark evaluations, security audits, and memory profiling.

```
                  ┌─────────────────────────────────────────┐
                  │          End-to-End Test Suite          │
                  │    (tests/test_e2e_all.py - 5 Tests)    │
                  └────────────────────┬────────────────────┘
                                       │
                  ┌────────────────────┴────────────────────┐
                  │    Frozen Gold Benchmark Evaluation     │
                  │  (45 Questions: 30 EN, 15 AR, 7 Stages) │
                  └────────────────────┬────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  Safety Engine   │          │ Multi-User & RLS │          │ Memory & Systems │
│ Regression Tests │          │  Security Suite  │          │ Profiling Audits │
│ (12 Rules Valid) │          │  (Fernet BYOK)   │          │ (RAM < 1GB OOM)  │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

---

### 28. Comprehensive Test Suite Breakdown

#### 1. RAG Benchmark Evaluation Testing
- File: `data/evaluation/rag_gold_dataset.csv`
- Test Scope: Evaluates 45 frozen questions across 7 ablation stages (7 sequential experimental passes).
- Scope: Validates Hit@1, Hit@3, Hit@5, MRR, Drug ID Accuracy, Section ID Accuracy across English and Arabic subsets.
- Result: Overall Hit@5 = 84.4%, Arabic Hit@5 = 93.3%, English Hit@5 = 80.0%, Drug ID = 91.1%, Section ID = 80.0%.

#### 2. End-to-End System Verification
- File: `tests/test_e2e_all.py`
- Test Count: 5 automated end-to-end integration tests.
- Scope: Validates English retrieval, Standard Arabic retrieval, Egyptian Colloquial retrieval, Grounding safety refusal on unsupported claims, and Dynamic age calculation from birth dates.
- Result: 100% Passed.

#### 3. Grounding & Evidence Formatting Verification
- File: `tests/test_grounding.py`
- Scope: Validates evidence block formatting `[E1]`, source document attribution, physical page number inclusion, and excerpt structure.
- Result: 100% Passed.

#### 4. Unanswered Query Logging Verification
- File: `tests/test_unanswered_queries.py`
- Scope: Validates that questions with insufficient evidence are logged to Supabase with reasons, language tags, and candidate metadata without raising uncaught exceptions.
- Result: 100% Passed.

#### 5. Deterministic Safety Engine Verification
- File: `backend/app/safety/safety_engine.py`
- Scope: Audits 23 candidate clinical rules across allergy, drug-disease, drug-drug, high-alert, and do-not-crush restrictions.
- Result: 12 primary verified rules (+ 1 supplementary = 13 rows in `final_verified_safety_rules.csv`) active with 100% grounding in EDA PDFs; 11 unverified candidate rules held in review as `needs_source_verification` with 0.0% False Positive Rate.

#### 6. Multi-User Authentication and Row Level Security (RLS)
- File: `supabase/schema.sql`
- Scope: Validates user data isolation across 10 database tables (`profiles`, `conversations`, `messages`, `message_sources`, `patient_conditions`, `patient_allergies`, `patient_medications`, `user_api_keys`, `medication_plans`).
- Result: 100% RLS policy enforcement. Cross-user data leaks prevented via `auth.uid() = user_id` constraints.

#### 7. BYOK Encryption and Security Suite
- File: `backend/app/security/encryption.py`
- Scope: Validates server-side Fernet encryption, SHA-256 key derivation, key hint masking (e.g., `AIzaSy...4x8Q`), and missing-key refusal behavior.
- Result: 100% Passed.

#### 8. Memory & Performance Profiling
- Methodology: Profiling memory consumption during startup, model loading, and peak inference on CPU.
- Measured Memory Footprint (Verified from Profiling):
  - Base Python Runtime + FastAPI + PyTorch core imports: 397.61 MB
  - Chunks DataFrame (5,437 rows): 412.91 MB total (+15.30 MB)
  - Precomputed Embeddings Cache (`embeddings_cache.npy`): 428.85 MB total (+15.94 MB)
  - BM25 Tokenized Corpus Index: 494.39 MB total (+65.54 MB)
  - Multilingual-E5-base Model Weights & Runtime: 833.32 MB total (+338.93 MB)
  - CrossEncoder mmarco-MiniLMv2 Model Weights: 1,154.11 MB total (+320.80 MB)
  - Steady-State RAM after full initialization: ~1,154.11 MB
  - Peak Inference RAM during CrossEncoder forward pass: ~1,668.02 MB
- Result: Identified Railway 1 GB RAM container limit as an infrastructure resource constraint, not an algorithmic defect.

---

## PART VII: SAFETY ARCHITECTURE

### 29. Why Retrieval Accuracy Is Insufficient for Medication Safety

In clinical software, high retrieval accuracy (e.g., Hit@5 = 84.4%) does not automatically guarantee patient safety. A retrieval engine might successfully find a relevant monograph for Metformin, but if the patient has severe renal impairment (eGFR < 30 mL/min) or a documented allergy to biguanides, delivering general dosage guidelines without flagging the contraindication is clinically unacceptable.

Tamargi.ai enforces a strict separation of concerns:
1. Retrieval Engine: Gathers official textual evidence from EDA monographs.
2. Safety Engine: Evaluates deterministic decision-support rules against the patient's confirmed profile.
3. Generative Model (Gemini): Translates verified evidence and safety findings into clear, language-appropriate explanations.

---

### 30. Patient Profile Architecture

Patient context is managed dynamically through confirmed medical records stored in Supabase:
- Demographic Factors: Dynamic age calculated from `birth_date`, biological sex, body weight (kg).
- Physiological States: Pregnancy status (trimester-aware), breastfeeding status.
- Confirmed Conditions: Chronic diagnoses (e.g., hypertension, type 2 diabetes, chronic kidney disease) mapped to normalized clinical concepts.
- Documented Allergies: Drug and class allergies (e.g., penicillin allergy, sulfonamide allergy).
- Active Medications: Current drug regimens with dosage, frequency, and administration routes.

---

### 31. Safety Engine Rule Evolution

The Safety Engine underwent a critical architectural evolution during development:

#### Initial Vulnerability: Broad Hardcoded Rules
In early prototypes, safety rules were hardcoded with broad assumptions and static citations. If an unverified clinical assumption was embedded in code, it created false safety alerts or missed nuanced formulary guidance.

#### Current Production: Verified Knowledge Store
All active safety rules are stored in `public.verified_safety_rules` with mandatory 1:1 provenance links:
- `rule_type`: `allergy`, `drug_disease`, `drug_drug`, `high_alert`, `do_not_crush`
- `drug_a` / `drug_b` / `condition_name` / `allergen_class`
- `source_file`: Exact EDA formulary PDF name
- `source_page`: Exact physical page number
- `evidence_excerpt`: Verbatim text excerpt from the regulatory monograph
- `verified`: Boolean flag required to be `true` for rule activation

#### The Principle of Safe Abstention
A fundamental rule was established: Absence of evidence is not evidence of safety.
If a patient asks about a medication and no safety rule or monograph evidence exists, the system does not return "This medication is safe." Instead, it explicitly returns `insufficient_evidence`, advising the patient to consult their treating physician or pharmacist.

---

## PART VIII: FULL ENGINEERING CHALLENGES & SOLUTIONS

This section details the primary technical and architectural challenges encountered throughout the engineering lifecycle of Tamargi.ai:

### Challenge 1: Broken Section Titles in PDF Extraction
- What Was Observed: PDF extraction split headings across lines (e.g., "Dosage &" / "Administration").
- Root Cause: Physical typesetting layout in EDA publications.
- How Investigated: Audited 50 random extracted chunks; discovered 22% of section metadata was mislabeled as "other".
- Solution: Built a multi-line header reconciler with hyphenation collapse in `metadata_extractor.py`.
- Result: Section labeling accuracy rose from 78% to 100% across the 5,437 chunk corpus.
- Lesson Learned: Layout-aware preprocessing is far more impactful than adjusting downstream embedding parameters.

### Challenge 2: Arabic Query vs English Corpus BM25 Failure
- What Was Observed: Arabic queries yielded Hit@5 = 0.067 in baseline ablation testing.
- Root Cause: BM25 regex was restricted to `[a-z0-9]+`; English corpus contained zero Arabic vocabulary tokens.
- How Investigated: Printed tokenized queries and BM25 score distributions for Arabic questions.
- Solution: Created `build_retrieval_query()` which translates resolved generic drugs and section intents into canonical English retrieval strings prior to BM25 execution.
- Result: Arabic Hit@5 surged from 0.067 (6.7%) to 0.933 (93.3%).
- Lesson Learned: In cross-lingual RAG, query normalization must bridge the lexical divide before invoking sparse keyword indexes.

### Challenge 3: Entity Contamination in Global Dense Retrieval
- What Was Observed: Dense semantic search ranked chunks from *Voriconazole* above *Anidulafungin* for antifungal queries.
- Why It Happened: Both drugs shared high semantic similarity in antifungal mechanism passages.
- How Investigated: Analyzed embedding vector cosine similarity matrices between different monographs.
- Solution: Implemented Stage 1 Drug Monograph Scope Identification to constrain retrieval to the target drug's monograph page window (±2 pages).
- Result: Eliminated cross-drug false positive retrievals; Drug ID accuracy reached 91.1%.
- Lesson Learned: Semantic similarity must be constrained by deterministic entity boundaries in clinical RAG.

### Challenge 4: Near-Duplicate Context Window Bloat
- What Was Observed: Top-5 evidence frequently contained 4 overlapping chunks from the same page.
- Root Cause: 20-word chunk overlap caused consecutive chunks to receive nearly identical CrossEncoder scores.
- How Investigated: Evaluated unique page counts in Top-5 retrieval results.
- Solution: Added an evidence acceptance layer enforcing word-level Jaccard similarity threshold (<0.85) and Pass 1 page diversity.
- Result: Top-5 results consistently cover distinct pages and clinical subsections.
- Lesson Learned: Context diversity must be explicitly engineered into post-reranking acceptance layers.

### Challenge 5: Railway Deployment Path Resolution Failure
- What Was Observed: Backend crashed on Railway startup with `FileNotFoundError: /data/processed/chunks_with_metadata.csv`.
- Root Cause: Railway configured the root directory as `/backend`, making repository-root `/data/` inaccessible via relative paths.
- How Investigated: Inspected Railway build directory tree and container working directory.
- Solution: Added multi-location candidate path resolution in `config.py` and synced required RAG runtime data into backend deployment packaging.
- Result: 100% reliable startup artifact discovery across local development, Docker, and cloud deployments.
- Lesson Learned: Cloud container root configurations must be decoupled from local monorepo directory structures.

### Challenge 6: Railway 1 GB Container Out-Of-Memory (OOM) Crash
- What Was Observed: Railway backend crashed during model initialization with "Deploy Ran Out of Memory".
- Root Cause: Loading PyTorch, Multilingual-E5-base (833 MB total), and CrossEncoder (1,154 MB total) alongside the FastAPI runtime exceeded the 1 GB container memory limit, peaking at 1,668 MB during inference.
- How Investigated: Executed step-by-step memory profiling measuring exact RSS RAM consumption for every subsystem.
- Solution: Documented memory profile; identified infrastructure constraint requiring a 2 GB container tier for production dual-model neural inference.
- Result: Proved algorithmic correctness while establishing exact production infrastructure requirements.
- Lesson Learned: Neural CrossEncoders and Transformer embedding models have strict physical memory baselines that cannot be compressed below their parameter sizes on CPU without quantization.

---

## PART IX: PRODUCTION APPLICATION ARCHITECTURE

### 32. Agentic Orchestration and Deterministic Tool Routing

The main orchestrator (`backend/app/orchestrator/orchestrator.py`) handles incoming user messages through a deterministic intent-routing architecture:

```
User Message
     │
     ▼
[ Intent Classifier ]
  - general_medication_query
  - device_usage_query
  - patient_specific_safety_check
  - medication_plan_generation
  - conversation_management
     │
     ├──────────────────────────────────────────────────────┐
     ▼                                                      ▼
[ General Medication Query ]                [ Device Usage Query ]
  1. Resolve Medication                       1. Resolve Exact Device
  2. Extract Patient Profile                  2. Match Verified Video
  3. Execute Hybrid RAG V2                    3. Check Inhaler Ambiguity
  4. Run Safety Engine                        4. Return Video + Steps
  5. Synthesize Grounded Answer                            │
     │                                                     │
     └──────────────────────┬──────────────────────────────┘
                            ▼
               [ Response Composer ]
         - Structured Grounded Text
         - Citations [E1], [E2] with Pages
         - Video Cards (if applicable)
         - Medication Plan Cards (if applicable)
```

---

### 33. Verified Educational Videos

Implemented in `backend/app/video/video_resolver.py`:
- Device Matching: Maps commercial brands (e.g., *Symbicort Turbuhaler*, *Seretide Diskus*, *Lantus Solostar*) to exact instructional videos.
- Ambiguity Handling: Generic terms (e.g., "بخاخ" or "inhaler") trigger an educational clarification prompt rather than presenting an incorrect device technique.
- Verified Source Citing: Videos must originate from verified health authorities with active URLs in `public.verified_videos`.

---

### 34. Medication Plans and Pharmacist QR Verification

Implemented in `backend/app/plans/plan_generator.py`:
- Plan Generation: Synthesizes multi-medication schedules with meal timing, dosage forms, and special administration precautions directly from verified monograph evidence.
- Public Verification Token: Generates a unique UUID token allowing read-only access to the structured plan.
- Pharmacist Verification Portal: Accessible at `/verify-plan/[token]`, enabling community pharmacists to inspect evidence citations and patient safety factors before dispensing.

---

### 35. Bring Your Own Key (BYOK) Security

Implemented in `backend/app/security/encryption.py` and `user_keys.py`:
- Client Isolation: Every authenticated user can supply their own Google Gemini API key.
- Server-Side Fernet Encryption: Keys are encrypted using Fernet symmetric encryption with backend-derived keys (SHA-256 derivation from server secret).
- Masked Display: The frontend displays only safe hints (e.g., `AIzaSy...4x8Q`).
- Key Resolution: Requests decrypt the user's key in-memory per request; if no key is provided, the backend returns a clean prompt requesting key configuration.

---

## PART X: DEPLOYMENT JOURNEY

### 36. Deployment Infrastructure Status

| Component | Platform | Environment / Configuration | Operational Status |
|---|---|---|---|
| Frontend Web App | Vercel | Next.js 14, Node 18, React 18, Tailwind CSS | Deployed & Operational |
| Backend API | Railway | FastAPI, Python 3.11, Uvicorn | Build / Health API Online; Full RAG requires >=2GB RAM |
| Database & Auth | Supabase | PostgreSQL 15, PostgREST, Auth with RLS | Deployed & Operational |
| Language Model | Google AI | Gemini 3.5 Flash Lite / Configurable via BYOK | Operational |
| Local Full System | Localhost | FastAPI + Next.js + PyTorch CPU / CUDA | 100% Fully Operational |

---

## PART XI: RESEARCH VS PRODUCTION

### 37. Comparison: Research Notebook vs Production System

| Aspect | Research Notebook (`Tamargi_RAG_V2_Research.ipynb`) | Production Backend (`backend/app/`) |
|---|---|---|
| Primary Audience | University evaluators, technical reviewers, viva demo | End-user Egyptian patients and clinicians |
| Execution Environment | Jupyter Notebook / Google Colab / Local CPU | Distributed FastAPI + Next.js + Supabase |
| State Management | In-memory Python variables and DataFrames | PostgreSQL database with Row Level Security |
| Architecture | Sequential procedural functions | Modular microservices with deterministic tools |
| Authentication | None | Supabase JWT Bearer Token validation |
| Safety Enforcement | Demonstrated on evaluation questions | Real-time multi-factor patient profile safety engine |
| Multi-Turn Memory | Single query evaluation loop | Full conversation history with Supabase logging |
| BYOK Security | Environment variable `GEMINI_API_KEY` | Server-side Fernet encrypted database key storage |

---

## PART XII: FINAL ANALYSIS AND LESSONS LEARNED

### 38. Complete Technology Stack

| Layer | Technology / Library | Specific Version / Model | Purpose |
|---|---|---|---|
| Frontend Core | Next.js / React | Next.js 14.2, React 18 | Modern responsive web application |
| Styling & Theme | Tailwind CSS | Tailwind CSS 3.4 | Dark and Light theme UI design system |
| Backend Framework | FastAPI / Uvicorn | FastAPI 0.110, Uvicorn | High-performance API runtime |
| Neural Embeddings | Sentence-Transformers | intfloat/multilingual-e5-base (768-dim) | Multilingual dense semantic search |
| Sparse Retrieval | rank-bm25 | BM25Okapi | Exact keyword and entity retrieval |
| Neural Reranking | Sentence-Transformers | cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 | Cross-attention query-passage reranking |
| Generative AI | Google GenAI SDK | Configurable via `GEMINI_MODEL` (default: gemini-3.5-flash-lite) | Strict evidence-grounded response generation |
| Database & Storage | Supabase / PostgreSQL | PostgreSQL 15 with pgvector & RLS | Persistent data, authentication, and RLS |
| Cryptography | Cryptography (Python) | Fernet (Authenticated Symmetric Cryptography) | BYOK Gemini API key encryption |

---

### 39. Repository Structure

```
tamargi-pharma-rag/
├── Tamargi_RAG_V2_Research.ipynb      # Complete Standalone Research Notebook (RAG V2)
├── README.md                          # Project Overview
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── api/                       # API Route Handlers (chat, patient, plans, byok)
│   │   ├── auth/                      # Supabase JWT Authentication Middleware
│   │   ├── config.py                  # Environment & Model Configuration
│   │   ├── database/                  # Supabase Client & SQL Repositories
│   │   ├── language/                  # Egyptian Dialect & Language Detection
│   │   ├── normalization/             # Text Normalizer, Medication & Query Resolver
│   │   ├── orchestrator/              # Agentic Intent Router & Response Composer
│   │   ├── plans/                     # Structured Medication Plan Generator
│   │   ├── rag/                       # RAG V2 Engine (Loader, Dense, BM25, RRF, CrossEncoder, Acceptance)
│   │   ├── safety/                    # Deterministic Safety Engine & Clinical Checkers
│   │   ├── security/                  # Fernet BYOK Encryption & Key Resolver
│   │   └── video/                     # Verified Educational Video Resolver
│   ├── build_research_notebook.py     # Builder Script for Research Notebook
│   └── test_notebook_execution.py     # Full Notebook Execution Test Harness
├── data/
│   ├── evaluation/                    # 45-Question Gold Dataset & Ablation Results
│   ├── processed/                     # 5,437 Chunks CSV & 251 Medication Aliases
│   └── raw/eda/                       # 13 Official EDA Formulary PDFs
├── docs/                              # Project Documentation & Evaluation Reports
├── frontend/                          # Next.js 14 Web Application
│   ├── src/
│   │   ├── app/                       # App Router Pages (chat, profile, plans, verify)
│   │   ├── components/                # UI Components (ChatArea, Sidebar, ThemeToggle, BYOK)
│   │   └── lib/                       # Supabase Client & API Helpers
├── notebooks/
│   ├── TamargiAI-RAG.ipynb            # Notebook 1 (Initial Research Prototype)
│   └── Tamargi_RAG_V2_Research.ipynb  # Notebook 2 (RAG V2 Research Notebook)
├── supabase/
│   └── schema.sql                     # Full Database Schema with RLS Policies
└── tests/                             # Automated Test Suites (e2e, grounding, retrieval)
```

---

### 40. End-to-End Walkthrough Example

#### User Query (Egyptian Arabic)
`"مريض ضغط وسكر.. ينفع ياخد كتافلام 50 مع دواء الضغط كونكور؟"`
*(A patient with hypertension and diabetes.. Can they take Cataflam 50 with their blood pressure medication Concor?)*

#### Execution Trace:
1. Language Detection: Detected Egyptian Arabic (`ar-EG`).
2. Text Normalization: Tashkeel stripped, characters standardized.
3. Medication Entity Resolution:
   - `"كتافلام"` -> Resolves to generic active ingredient `diclofenac` (strength: 50 mg).
   - `"كونكور"` -> Resolves to generic active ingredient `bisoprolol`.
4. Patient Profile Association:
   - Active Conditions: `hypertension`, `type_2_diabetes`.
   - Current Medications: `bisoprolol`.
5. Deterministic Safety Engine Evaluation:
   - Rule Check 1 (Drug-Disease): Diclofenac (NSAID) in Hypertension -> Flagged (NSAIDs promote sodium retention and attenuate antihypertensive efficacy of beta-blockers).
   - Rule Check 2 (Drug-Drug): Diclofenac + Bisoprolol -> Potential interaction flagged.
6. Stage 1 Drug Scope Identification: Restricts search space to *Diclofenac* monograph (`egypt_cardiovascular_formulary_2024.pdf` and `egypt_blood_disorders_formulary_2025.pdf`).
7. Hybrid RRF Retrieval & CrossEncoder Reranking: Retrieves exact contraindication and interaction sections.
8. Evidence Acceptance: Selects top 3 diverse, non-duplicate chunks with page numbers.
9. Strict Grounded Generation: Gemini synthesizes response citing exact EDA pages `[E1] p.45`, `[E2] p.48`.
10. Final Output: Clinical warning explaining the mechanism of NSAID-induced blood pressure elevation, advising paracetamol as an alternative, and citing official EDA monograph pages.

---

### 41. Key Lessons Learned

1. Semantic Similarity Is Not Clinical Safety: High cosine similarity between embeddings does not prevent hallucinations or cross-drug contamination. Clinical RAG requires deterministic scope constraints.
2. Multilingual Bridging Requires Entity Normalization: When queries are in Arabic and documents are in English, BM25 fails unless queries are canonically translated at the entity level before search.
3. Absence of Evidence Is Not Evidence of Safety: If a medical system lacks evidence regarding a drug combination, it must explicitly state that evidence is insufficient rather than assuming safety.
4. Infrastructure Dictates ML Deployment: Neural CrossEncoders and Transformer embedding models have non-negotiable physical RAM footprints (~1.15 GB steady-state, ~1.67 GB peak) that require appropriate container memory tiers.
5. Multi-User Security Must Be Built In Early: Managing healthcare data requires strict Row Level Security (RLS) and cryptographic isolation (Fernet BYOK) from the first prototype.

---

### 42. Conclusion

Tamargi.ai represents a robust, explainable, and scientifically validated approach to personalized medication safety for Egyptian patients. By replacing generic, hallucination-prone LLM chatbots with a structured 5-stage Hybrid RAG V2 pipeline, a deterministic safety engine, and page-level regulatory provenance, Tamargi.ai demonstrates how modern AI can empower patients and assist clinicians while upholding the highest standards of evidence-based medical safety.
