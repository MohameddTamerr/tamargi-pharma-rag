import os
import sys
import hashlib
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def audit_gold_dataset():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_path = os.path.join(base_dir, 'data', 'evaluation', 'rag_gold_dataset.csv')
    chunks_path = os.path.join(base_dir, 'data', 'processed', 'final_chunks.csv')
    out_path = os.path.join(base_dir, 'data', 'evaluation', 'gold_dataset_audit.csv')

    # 1. Compute SHA-256 of gold dataset
    with open(gold_path, 'rb') as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"[AUDIT] Gold Dataset Path: {gold_path}")
    print(f"[AUDIT] Initial SHA-256: {sha256}")

    gold_df = pd.read_csv(gold_path)
    chunks_df = pd.read_csv(chunks_path)

    print(f"[AUDIT] Loaded {len(gold_df)} gold questions.")
    print(f"[AUDIT] Loaded {len(chunks_df)} chunks from {chunks_df['file'].nunique()} PDF files.")

    audit_rows = []
    status_counts = {"VALID": 0, "VALID_BUT_CONTINUES_NEXT_PAGE": 0, "QUESTION_HAS_MULTIPLE_VALID_PAGES": 0, "POSSIBLE_GOLD_ISSUE": 0}

    for idx, r in gold_df.iterrows():
        qid = r['question_id']
        q = r['question']
        drug = str(r['expected_drug']).strip() if pd.notna(r['expected_drug']) else ""
        efile = str(r['expected_file']).strip()
        epage = int(r['expected_page'])
        esection = str(r['expected_section']).strip() if pd.notna(r['expected_section']) else ""

        # Find chunks on exact expected page
        exact_chunks = chunks_df[(chunks_df['file'] == efile) & (chunks_df['page'] == epage)]
        exact_text = " ".join(exact_chunks['text'].astype(str).tolist())

        # Find chunks on adjacent pages
        prev_chunks = chunks_df[(chunks_df['file'] == efile) & (chunks_df['page'] == epage - 1)]
        next_chunks = chunks_df[(chunks_df['file'] == efile) & (chunks_df['page'] == epage + 1)]
        nearby_text = " ".join(pd.concat([prev_chunks, exact_chunks, next_chunks])['text'].astype(str).tolist())

        # Determine evidence presence
        evidence_found = len(exact_chunks) > 0 and len(exact_text.strip()) > 30

        # Check drug and section mentions
        drug_in_exact = (drug.lower() in exact_text.lower()) if drug else True
        drug_in_nearby = (drug.lower() in nearby_text.lower()) if drug else True

        # Status determination
        if not evidence_found:
            status = "POSSIBLE_GOLD_ISSUE"
            notes = f"No chunks found for file '{efile}' on page {epage}."
            excerpt = "N/A"
        elif drug and not drug_in_exact and drug_in_nearby:
            status = "VALID_BUT_CONTINUES_NEXT_PAGE"
            notes = f"Monograph begins on adjacent page, continues onto page {epage}."
            excerpt = exact_text[:200].replace('\n', ' ')
        else:
            status = "VALID"
            notes = f"Evidence confirmed on page {epage} ({len(exact_chunks)} chunks)."
            excerpt = exact_text[:200].replace('\n', ' ')

        status_counts[status] += 1

        audit_rows.append({
            "question_id": qid,
            "expected_drug": drug if drug else "N/A",
            "expected_file": efile,
            "expected_page": epage,
            "evidence_found_on_expected_page": evidence_found,
            "evidence_excerpt": excerpt,
            "audit_status": status,
            "notes": notes
        })

    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(out_path, index=False, encoding='utf-8')
    print(f"\n[AUDIT] Saved gold audit report to: {out_path}")
    print(f"[AUDIT] Summary: {status_counts}")
    return audit_df, sha256

if __name__ == '__main__':
    audit_gold_dataset()
