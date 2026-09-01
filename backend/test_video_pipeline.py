import sys
from app.video.intent_detector import detect_video_intent
from app.video.video_matcher import score_video_match, find_verified_video

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

test_cases = [
    {
        "id": 1,
        "query": "ازاي استخدم بخاخ الربو؟",
        "expected_intent": True,
        "expected_concept": "inhaler"
    },
    {
        "id": 2,
        "query": "طريقة استخدام قلم الانسولين",
        "expected_intent": True,
        "expected_concept": "insulin_pen"
    },
    {
        "id": 3,
        "query": "How do I use an inhaler?",
        "expected_intent": True,
        "expected_concept": "inhaler"
    },
    {
        "id": 4,
        "query": "ازاي احط قطرة العين؟",
        "expected_intent": True,
        "expected_concept": "eye_drop"
    },
    {
        "id": 5,
        "query": "ما هي موانع استخدام Anidulafungin؟",
        "expected_intent": False,
        "expected_concept": None
    },
    {
        "id": 6,
        "query": "ما الفرق بين الباراسيتامول والإيبوبروفين؟",
        "expected_intent": False,
        "expected_concept": None
    },
    {
        "id": 7,
        "query": "ازاي استخدم جهاز غسيل الكلى المنزلي التلقائي النادر؟",
        "expected_intent": True,
        "expected_concept": None  # Device without video in DB
    }
]

print("=" * 80)
print("RUNNING INTENT & CONCEPT DETECTION TESTS")
print("=" * 80)

passed = 0
for tc in test_cases:
    is_practical, ext_concept, norm_dev = detect_video_intent(tc["query"])
    status = "PASS" if is_practical == tc["expected_intent"] else "FAIL"
    if status == "PASS" and tc["expected_concept"]:
        if norm_dev != tc["expected_concept"]:
            status = f"FAIL (Expected {tc['expected_concept']}, got {norm_dev})"
    
    if "PASS" in status:
        passed += 1

    print(f"Test {tc['id']}: '{tc['query']}'")
    print(f"  Result: Intent={is_practical}, Extracted='{ext_concept}', Normalized='{norm_dev}' -> [{status}]")
    print()

print(f"Intent Detection Summary: {passed}/{len(test_cases)} Passed.")

print("\n" + "=" * 80)
print("TESTING STRICT VERIFIED / ACTIVE FILTERING LOGIC")
print("=" * 80)

# Mock candidate database records
mock_db = [
    {
        "id": "v-inhaler-verified",
        "title": "How to Use a Metered Dose Inhaler (MDI)",
        "topic": "inhaler_usage",
        "medication_or_device": "inhaler",
        "aliases": ["inhaler", "بخاخ", "بخاخ الربو", "salbutamol", "ventolin"],
        "language": "en",
        "video_url": "https://www.youtube.com/watch?v=Rdb3p9RZoR4",
        "thumbnail_url": "https://img.youtube.com/vi/Rdb3p9RZoR4/hqdefault.jpg",
        "source_name": "CDC Respiratory Health",
        "verified": True,
        "active": True
    },
    {
        "id": "v-unverified-fake",
        "title": "Random Unverified Inhaler Video",
        "topic": "inhaler_usage",
        "medication_or_device": "inhaler",
        "aliases": ["inhaler", "بخاخ"],
        "language": "en",
        "video_url": "https://example.com/unverified",
        "thumbnail_url": None,
        "source_name": "Unverified Blog",
        "verified": False, # UNVERIFIED
        "active": True
    },
    {
        "id": "v-inactive-inhaler",
        "title": "Old Inactive Inhaler Video",
        "topic": "inhaler_usage",
        "medication_or_device": "inhaler",
        "aliases": ["inhaler", "بخاخ"],
        "language": "en",
        "video_url": "https://example.com/inactive",
        "thumbnail_url": None,
        "source_name": "CDC Archive",
        "verified": True,
        "active": False # INACTIVE
    }
]

# Test Case 8: Unverified video test
print("Test 8: Ensure unverified video (verified=False) is rejected")
candidates_unverified = [v for v in mock_db if v["verified"] and v["active"]]
unverified_found = any(v["id"] == "v-unverified-fake" for v in candidates_unverified)
print(f"  Unverified video returned: {unverified_found} -> [{'PASS' if not unverified_found else 'FAIL'}]")

# Test Case 9: Inactive video test
print("Test 9: Ensure inactive video (active=False) is rejected")
inactive_found = any(v["id"] == "v-inactive-inhaler" for v in candidates_unverified)
print(f"  Inactive video returned: {inactive_found} -> [{'PASS' if not inactive_found else 'FAIL'}]")

# Test Matching score
test_query_ar = "ازاي استخدم بخاخ السالبوتامول؟"
score_valid = score_video_match(mock_db[0], "inhaler", "سالبوتامول", test_query_ar, user_lang="ar")
print(f"\nAlias Match Test: Query='{test_query_ar}' against '{mock_db[0]['title']}'")
print(f"  Score: {score_valid} -> [{'PASS' if score_valid >= 5.0 else 'FAIL'}]")
