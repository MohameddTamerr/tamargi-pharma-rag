import os
import sys
import hashlib
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.rag.loader import rag_loader
from app.rag.dense_search import dense_search
from app.rag.bm25_search import bm25_search
from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank_results
from app.rag.retrieval import retrieve, get_candidate_scope_indices
from app.rag.acceptance import filter_and_accept_evidence
from app.normalization.medication_resolver import extract_all_medications
from app.normalization.query_translator import build_canonical_retrieval_query, detect_query_section
from app.normalization.text_normalizer import normalize_arabic_text

def check_hit(results, exp_file, exp_page):
    ranks = []
    for r_idx, res in enumerate(results[:5], start=1):
        f_match = (str(res.get("file", res.get("source_file", ""))).lower() == str(exp_file).lower())
        p_match = (abs(int(res.get("page", -999)) - int(exp_page)) <= 1)
        if f_match and p_match:
            ranks.append(r_idx)
    return ranks[0] if ranks else None

def compute_metrics(hits1, hits3, hits5, mrrs):
    return {
        "Hit@1": float(np.mean(hits1)),
        "Hit@3": float(np.mean(hits3)),
        "Hit@5": float(np.mean(hits5)),
        "MRR": float(np.mean(mrrs))
    }

def run_ablation_study():
    print("=" * 95)
    print("TAMARGI.AI — RAG RETRIEVAL V2 ACADEMIC ABLATION STUDY (7 STAGES)")
    print("=" * 95)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_path = os.path.join(base_dir, 'data', 'evaluation', 'rag_gold_dataset.csv')
    out_csv_path = os.path.join(base_dir, 'data', 'evaluation', 'rag_v2_ablation_results.csv')

    with open(gold_path, 'rb') as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"Gold Dataset: {gold_path}")
    print(f"Verified Frozen SHA-256: {sha256}")

    if not rag_loader.is_loaded:
        rag_loader.load()

    df_gold = pd.read_csv(gold_path)
    total_q = len(df_gold)
    print(f"Evaluating {total_q} questions ({len(df_gold[df_gold['language']=='en'])} English, {len(df_gold[df_gold['language']=='ar'])} Arabic)\n")

    stages = [
        "A: Baseline (No metadata, standard RRF+CrossEncoder)",
        "B: + Monograph Metadata (Enriched BM25 index)",
        "C: + Section-Aware Query Decomposition",
        "D: + Hierarchical Scoped Candidate Pool",
        "E: + Contextual CrossEncoder Reranking",
        "F: + Controlled Neighbor Expansion",
        "G: Final Full Pipeline (+ Acceptance & Deduplication)"
    ]

    ablation_results = []

    for stage_idx, stage_name in enumerate(stages, start=1):
        print(f"--- Running Stage {stage_idx}/7: {stage_name} ---")

        hits1, hits3, hits5, mrrs = [], [], [], []
        hits1_en, hits3_en, hits5_en, mrrs_en = [], [], [], []
        hits1_ar, hits3_ar, hits5_ar, mrrs_ar = [], [], [], []
        drug_correct = 0
        section_correct = 0

        for _, row in df_gold.iterrows():
            qid = row['question_id']
            query = row['question']
            exp_file = row['expected_file']
            exp_page = row['expected_page']
            exp_drug = str(row['expected_drug']).strip() if pd.notna(row['expected_drug']) else ""
            exp_sec = str(row['expected_section']).strip() if pd.notna(row['expected_section']) else ""
            lang = row['language']

            # Entity and section extraction
            med_objs = extract_all_medications(query)
            target_meds = [m.canonical_generic for m in med_objs if m.canonical_generic]
            detected_sec = detect_query_section(query)

            # Accuracy tracking
            if exp_drug:
                if any(exp_drug.lower() in tm.lower() or tm.lower() in exp_drug.lower() for tm in target_meds):
                    drug_correct += 1
            else:
                drug_correct += 1

            if exp_sec:
                if detected_sec.lower() == exp_sec.lower() or exp_sec.lower() in detected_sec.lower():
                    section_correct += 1
            else:
                section_correct += 1

            # Build query according to stage
            if stage_idx == 1:
                # Stage A: Raw baseline query
                q_proc = query
                candidates = hybrid_search(q_proc, dense_k=10, bm25_k=10, final_k=10, candidate_indices=None)
                # Raw text pairs only
                pairs = [[q_proc, c["text"]] for c in candidates]
                raw_scores = rag_loader.embedding_model.encode(["query: " + q_proc], normalize_embeddings=True)[0]
                results = sorted(candidates, key=lambda x: x.get("rrf_score", 0), reverse=True)[:5]

            elif stage_idx == 2:
                # Stage B: Enriched BM25 + standard search
                q_proc = query
                candidates = hybrid_search(q_proc, dense_k=20, bm25_k=20, final_k=20, candidate_indices=None)
                results = rerank_results(q_proc, candidates, top_k=5, target_medications=None, target_section=None)

            elif stage_idx == 3:
                # Stage C: Section-aware query
                if lang == "ar":
                    q_norm = normalize_arabic_text(query)
                    q_proc = build_canonical_retrieval_query(q_norm, "general", med_objs)
                else:
                    q_proc = build_canonical_retrieval_query(query, "general", med_objs)
                candidates = hybrid_search(q_proc, dense_k=30, bm25_k=30, final_k=30, candidate_indices=None)
                results = rerank_results(q_proc, candidates, top_k=5, target_medications=None, target_section=None)

            elif stage_idx == 4:
                # Stage D: Hierarchical Scoped candidates
                if lang == "ar":
                    q_norm = normalize_arabic_text(query)
                    q_proc = build_canonical_retrieval_query(q_norm, "general", med_objs)
                else:
                    q_proc = build_canonical_retrieval_query(query, "general", med_objs)
                scope_idx = get_candidate_scope_indices(target_meds, detected_sec, query.lower())
                if scope_idx and len(scope_idx) >= 10:
                    candidates = hybrid_search(q_proc, dense_k=len(scope_idx), bm25_k=len(scope_idx), final_k=40, candidate_indices=scope_idx)
                else:
                    candidates = hybrid_search(q_proc, dense_k=40, bm25_k=40, final_k=40, candidate_indices=None)
                results = rerank_results(q_proc, candidates, top_k=5, target_medications=target_meds, target_section=detected_sec)

            elif stage_idx == 5:
                # Stage E: Contextual CrossEncoder Reranking
                if lang == "ar":
                    q_norm = normalize_arabic_text(query)
                    q_proc = build_canonical_retrieval_query(q_norm, "general", med_objs)
                else:
                    q_proc = build_canonical_retrieval_query(query, "general", med_objs)
                scope_idx = get_candidate_scope_indices(target_meds, detected_sec, query.lower())
                if scope_idx and len(scope_idx) >= 10:
                    candidates = hybrid_search(q_proc, dense_k=len(scope_idx), bm25_k=len(scope_idx), final_k=40, candidate_indices=scope_idx)
                else:
                    candidates = hybrid_search(q_proc, dense_k=40, bm25_k=40, final_k=40, candidate_indices=None)
                results = rerank_results(q_proc, candidates, top_k=5, target_medications=target_meds, target_section=detected_sec)

            elif stage_idx == 6:
                # Stage F: Controlled Neighbor Expansion
                if lang == "ar":
                    q_norm = normalize_arabic_text(query)
                    q_proc = build_canonical_retrieval_query(q_norm, "general", med_objs)
                else:
                    q_proc = build_canonical_retrieval_query(query, "general", med_objs)
                scope_idx = get_candidate_scope_indices(target_meds, detected_sec, query.lower())
                if scope_idx and len(scope_idx) >= 10:
                    candidates = hybrid_search(q_proc, dense_k=len(scope_idx), bm25_k=len(scope_idx), final_k=40, candidate_indices=scope_idx)
                else:
                    candidates = hybrid_search(q_proc, dense_k=40, bm25_k=40, final_k=40, candidate_indices=None)
                reranked = rerank_results(q_proc, candidates, top_k=40, target_medications=target_meds, target_section=detected_sec)
                # Expand top hit
                if reranked:
                    top_idx = reranked[0].get("index")
                    seen = {c["chunk_id"] for c in reranked}
                    for off in [1, -1, 2]:
                        n_i = top_idx + off
                        if 0 <= n_i < len(rag_loader.chunks_df):
                            nr = rag_loader.chunks_df.iloc[n_i]
                            if str(nr["file"]).lower() == reranked[0]["file"].lower() and int(nr["chunk_id"]) not in seen:
                                reranked.append({
                                    "index": int(n_i), "file": str(nr["file"]), "page": int(nr["page"]),
                                    "chunk_id": int(nr["chunk_id"]), "canonical_drug": str(nr.get("canonical_drug", "")),
                                    "section": str(nr.get("section", "")), "text": str(nr["text"]),
                                    "reranker_score": reranked[0].get("reranker_score", 0) - 0.05 * abs(off)
                                })
                results = sorted(reranked, key=lambda x: x.get("reranker_score", 0), reverse=True)[:5]

            elif stage_idx == 7:
                # Stage G: Final Full Pipeline
                if lang == "ar":
                    q_norm = normalize_arabic_text(query)
                    q_proc = build_canonical_retrieval_query(q_norm, "general", med_objs)
                else:
                    q_proc = build_canonical_retrieval_query(query, "general", med_objs)
                results = retrieve(q_proc, target_medications=target_meds, target_section=detected_sec)[:5]

            rank = check_hit(results, exp_file, exp_page)
            h1 = 1 if rank == 1 else 0
            h3 = 1 if rank and rank <= 3 else 0
            h5 = 1 if rank and rank <= 5 else 0
            mrr = (1.0 / rank) if rank else 0.0

            hits1.append(h1)
            hits3.append(h3)
            hits5.append(h5)
            mrrs.append(mrr)

            if lang == "en":
                hits1_en.append(h1)
                hits3_en.append(h3)
                hits5_en.append(h5)
                mrrs_en.append(mrr)
            else:
                hits1_ar.append(h1)
                hits3_ar.append(h3)
                hits5_ar.append(h5)
                mrrs_ar.append(mrr)

        m_all = compute_metrics(hits1, hits3, hits5, mrrs)
        m_en = compute_metrics(hits1_en, hits3_en, hits5_en, mrrs_en)
        m_ar = compute_metrics(hits1_ar, hits3_ar, hits5_ar, mrrs_ar)
        drug_acc = drug_correct / total_q
        sec_acc = section_correct / total_q

        print(f"  Overall: Hit@1={m_all['Hit@1']:.3f} | Hit@3={m_all['Hit@3']:.3f} | Hit@5={m_all['Hit@5']:.3f} ({int(sum(hits5))}/{total_q}) | MRR={m_all['MRR']:.3f}")
        print(f"  English Hit@5: {m_en['Hit@5']:.3f} ({int(sum(hits5_en))}/30) | Arabic Hit@5: {m_ar['Hit@5']:.3f} ({int(sum(hits5_ar))}/15)")
        print(f"  Drug Identification Acc: {drug_acc*100:.1f}% | Section Identification Acc: {sec_acc*100:.1f}%\n")

        ablation_results.append({
            "stage": stage_name,
            "hit_at_1": m_all['Hit@1'],
            "hit_at_3": m_all['Hit@3'],
            "hit_at_5": m_all['Hit@5'],
            "hit_at_5_count": f"{int(sum(hits5))}/{total_q}",
            "mrr": m_all['MRR'],
            "en_hit_at_5": m_en['Hit@5'],
            "ar_hit_at_5": m_ar['Hit@5'],
            "drug_id_acc": drug_acc,
            "section_id_acc": sec_acc
        })

    ab_df = pd.DataFrame(ablation_results)
    ab_df.to_csv(out_csv_path, index=False, encoding='utf-8')
    print(f"\n[ABLATION] Saved ablation results to: {out_csv_path}")

    # Print clean Markdown summary table
    print("\n" + "=" * 95)
    print("FINAL ABLATION SUMMARY TABLE")
    print("=" * 95)
    print(f"{'Stage':<52} | {'Hit@1':<7} | {'Hit@3':<7} | {'Hit@5':<7} | {'MRR':<7} | {'En Hit@5':<8} | {'Ar Hit@5':<8}")
    print("-" * 110)
    for r in ablation_results:
        print(f"{r['stage'][:52]:<52} | {r['hit_at_1']:<7.3f} | {r['hit_at_3']:<7.3f} | {r['hit_at_5']:<7.3f} | {r['mrr']:<7.3f} | {r['en_hit_at_5']:<8.3f} | {r['ar_hit_at_5']:<8.3f}")

    return ab_df

if __name__ == '__main__':
    run_ablation_study()
