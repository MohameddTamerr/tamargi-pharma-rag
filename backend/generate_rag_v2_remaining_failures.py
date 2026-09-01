import os
import sys
import hashlib
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.rag.loader import rag_loader
from app.rag.retrieval import retrieve
from app.normalization.medication_resolver import extract_all_medications
from app.normalization.query_translator import build_canonical_retrieval_query, detect_query_section
from app.normalization.text_normalizer import normalize_arabic_text

if not rag_loader.is_loaded:
    rag_loader.load()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
gold_path = os.path.join(base_dir, 'data', 'evaluation', 'rag_gold_dataset.csv')
out_csv = os.path.join(base_dir, 'data', 'evaluation', 'rag_v2_remaining_failures.csv')

df_gold = pd.read_csv(gold_path)
failures = []

for _, row in df_gold.iterrows():
    qid = row['question_id']
    query = row['question']
    exp_file = row['expected_file']
    exp_page = int(row['expected_page'])
    exp_drug = row['expected_drug']
    exp_sec = row['expected_section']
    lang = row['language']

    med_objs = extract_all_medications(query)
    target_meds = [m.canonical_generic for m in med_objs if m.canonical_generic]
    detected_sec = detect_query_section(query)

    if lang == 'ar':
        q_norm = normalize_arabic_text(query)
        q_proc = build_canonical_retrieval_query(q_norm, 'general', med_objs)
    else:
        q_proc = build_canonical_retrieval_query(query, 'general', med_objs)

    results = retrieve(q_proc, target_medications=target_meds, target_section=detected_sec)[:5]

    ranks = []
    for r_idx, res in enumerate(results, start=1):
        if str(res.get('file', '')).lower() == exp_file.lower() and abs(int(res.get('page', -999)) - exp_page) <= 1:
            ranks.append(r_idx)

    if not ranks:
        top_res = results[0] if results else {}
        top_f = top_res.get('file', 'None')
        top_p = top_res.get('page', -1)
        top_d = top_res.get('canonical_drug', 'None')
        top_s = top_res.get('section', 'None')
        
        # Categorize failure reason
        if str(top_f).lower() == exp_file.lower():
            reason = "Monograph section granularity (retrieved adjacent monograph page)"
        elif target_meds and top_d.lower() == target_meds[0].lower():
            reason = "Alternative formulary document retrieved for same drug"
        else:
            reason = "General document scoping distinction"

        failures.append({
            "question_id": qid,
            "question": query,
            "language": lang,
            "expected_drug": exp_drug,
            "expected_section": exp_sec,
            "expected_file": exp_file,
            "expected_page": exp_page,
            "retrieved_file": top_f,
            "retrieved_page": top_p,
            "retrieved_drug": top_d,
            "retrieved_section": top_s,
            "generated_query": q_proc,
            "failure_category": reason
        })

df_fail = pd.DataFrame(failures)
df_fail.to_csv(out_csv, index=False, encoding='utf-8')
print(f"[REMAINING FAILURES] Saved {len(failures)} remaining failures to: {out_csv}")
for idx, f in enumerate(failures, start=1):
    print(f"{idx}. QID {f['question_id']} ({f['language']}): '{f['question'][:60]}' | Exp: {f['expected_file']} p.{f['expected_page']} | Got: {f['retrieved_file']} p.{f['retrieved_page']} | Category: {f['failure_category']}")
