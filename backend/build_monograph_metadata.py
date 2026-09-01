import os
import sys
import pandas as pd
from app.rag.metadata_extractor import extract_metadata_for_corpus

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def build_monograph_metadata():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_path = os.path.join(base_dir, 'data', 'processed', 'final_chunks.csv')
    out_path = os.path.join(base_dir, 'data', 'processed', 'chunks_with_metadata.csv')

    print(f"[METADATA] Loading raw chunks from: {in_path}")
    raw_df = pd.read_csv(in_path)
    print(f"[METADATA] Input chunks: {len(raw_df)}")

    enriched_df = extract_metadata_for_corpus(raw_df)

    print(f"[METADATA] Output chunks: {len(enriched_df)}")
    print(f"[METADATA] Chunks with canonical_drug: {(enriched_df['canonical_drug'] != '').sum()} / {len(enriched_df)}")
    print(f"[METADATA] Chunks with monograph_name: {(enriched_df['monograph_name'] != '').sum()} / {len(enriched_df)}")
    print(f"[METADATA] Unique canonical drugs: {enriched_df['canonical_drug'].nunique()}")
    print("\nSection distribution:")
    print(enriched_df['section'].value_counts())

    enriched_df.to_csv(out_path, index=False, encoding='utf-8')
    print(f"\n[METADATA] Saved enriched metadata corpus to: {out_path}")

    return enriched_df

if __name__ == '__main__':
    build_monograph_metadata()
