import sys
import requests
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = "http://127.0.0.1:8000/api/chat"

test_queries = [
    # 1. Paracetamol overdose treatment (explicitly in formulary)
    "ما هو علاج الجرعة الزائدة من الباراسيتامول؟",
    # 2. Egyptian dialect query
    "هو الاسيتيل سيستئين بيستخدم في ايه لجرعة الباراسيتامول الزايدة؟",
    # 3. English query
    "What is the treatment for paracetamol overdose?",
]

for q in test_queries:
    print("=" * 70)
    print(f"Testing Query: {q}")
    payload = {"query": q}
    try:
        res = requests.post(url, json=payload, timeout=60)
        if res.status_code == 200:
            data = res.json()
            print(f"Language Detected: {data.get('language_detected')}")
            print(f"Normalized Query: {data.get('normalized_query')}")
            print(f"\nAnswer:\n{data.get('answer')}")
            print(f"\nTop Sources ({len(data.get('sources', []))}):")
            for s in data.get('sources', []):
                print(f" - [{s.get('evidenceId')}] {s.get('fileName')} (Page {s.get('pageNumber')}, Rank {s.get('rank')}, Score: {s.get('score'):.4f})")
                print(f"   Excerpt: {s.get('excerpt')[:120]}...")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    print()
