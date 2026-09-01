import sys
from app.video.intent_detector import detect_video_intent, normalize_text_for_matching
from app.video.video_matcher import (
    match_query_to_device_mapping,
    is_generic_inhaler_query_without_device,
    DEFAULT_TAXONOMY_MAPPINGS
)

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Curated mock verified videos representing approved Supabase records
MOCK_SUPABASE_VIDEOS = [
    {
        "id": "v-turbohaler-01",
        "title": "How to Use Symbicort Turbohaler (DPI)",
        "topic": "turbohaler_usage",
        "medication_or_device": "Turbohaler",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Turbohaler",
        "usage_topic": "turbohaler_usage",
        "aliases": ["turbohaler", "symbicort", "تربوهيلر"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=sample_turbohaler",
        "thumbnail_url": "https://example.com/turbo.jpg",
        "source_name": "Asthma & Lung UK",
        "verified": True,
        "active": True
    },
    {
        "id": "v-ellipta-01",
        "title": "How to Use an Ellipta Dry Powder Inhaler",
        "topic": "ellipta_usage",
        "medication_or_device": "Ellipta",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Ellipta",
        "usage_topic": "ellipta_usage",
        "aliases": ["ellipta", "relvar", "اليبيتا"],
        "language": "en",
        "video_url": "https://www.youtube.com/watch?v=sample_ellipta",
        "thumbnail_url": "https://example.com/ellipta.jpg",
        "source_name": "National Health Service (NHS)",
        "verified": True,
        "active": True
    },
    {
        "id": "v-pmdi-01",
        "title": "طريقة استخدام بخاخ الربو المضغوط (pMDI / Evohaler)",
        "topic": "pmdi_usage",
        "medication_or_device": "Evohaler",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "pMDI",
        "device_name": "Evohaler",
        "usage_topic": "pmdi_usage",
        "aliases": ["evohaler", "ventolin", "فنتولين", "ايفوهيلر"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=sample_evohaler",
        "thumbnail_url": "https://example.com/evohaler.jpg",
        "source_name": "Egyptian Respiratory Society",
        "verified": True,
        "active": True
    },
    {
        "id": "v-accuhaler-01",
        "title": "How to Use Seretide Accuhaler / Diskus",
        "topic": "accuhaler_usage",
        "medication_or_device": "Accuhaler",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Accuhaler",
        "usage_topic": "accuhaler_usage",
        "aliases": ["accuhaler", "diskus", "أكيوهيلر", "سيريتيد"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=sample_accuhaler",
        "thumbnail_url": "https://example.com/accuhaler.jpg",
        "source_name": "NHS Inform",
        "verified": True,
        "active": True
    },
    {
        "id": "v-insulin-pen-01",
        "title": "How to Use an Insulin Pen Correctly",
        "topic": "insulin_pen_usage",
        "medication_or_device": "insulin_pen",
        "category": "insulin_injection",
        "dosage_form": "subcutaneous_injection",
        "device_type": "pen_injector",
        "device_name": "insulin_pen",
        "usage_topic": "insulin_pen_usage",
        "aliases": ["insulin pen", "قلم انسولين", "قلم الانسولين"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=sample_insulin",
        "thumbnail_url": "https://example.com/insulin.jpg",
        "source_name": "American Diabetes Association",
        "verified": True,
        "active": True
    },
    {
        "id": "v-cgm-freestyle-01",
        "title": "FreeStyle Libre Sensor Application & Usage",
        "topic": "cgm_freestyle_libre_usage",
        "medication_or_device": "FreeStyle Libre",
        "category": "glucose_monitoring",
        "dosage_form": "sensor",
        "device_type": "cgm",
        "device_name": "FreeStyle Libre",
        "usage_topic": "cgm_freestyle_libre_usage",
        "aliases": ["freestyle libre", "فري ستايل ليبري", "حساس السكر"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=sample_freestyle",
        "thumbnail_url": "https://example.com/freestyle.jpg",
        "source_name": "Abbott Diabetes Care Verified Guide",
        "verified": True,
        "active": True
    },
    {
        "id": "v-unverified-turbohaler",
        "title": "Unverified Random Turbohaler Video",
        "topic": "turbohaler_usage",
        "medication_or_device": "Turbohaler",
        "category": "inhaler",
        "device_type": "DPI",
        "device_name": "Turbohaler",
        "usage_topic": "turbohaler_usage",
        "video_url": "https://example.com/fake_unverified",
        "source_name": "Unknown Blog",
        "verified": False, # UNVERIFIED
        "active": True
    },
    {
        "id": "v-inactive-ellipta",
        "title": "Inactive Ellipta Video",
        "topic": "ellipta_usage",
        "medication_or_device": "Ellipta",
        "category": "inhaler",
        "device_type": "DPI",
        "device_name": "Ellipta",
        "usage_topic": "ellipta_usage",
        "video_url": "https://example.com/fake_inactive",
        "source_name": "Archived NHS",
        "verified": True,
        "active": False # INACTIVE
    }
]

def simulate_video_matcher(query: str, available_videos: list = MOCK_SUPABASE_VIDEOS) -> dict | None:
    is_practical, extracted_target = detect_video_intent(query)
    if not is_practical:
        return None

    query_norm = normalize_text_for_matching(query)
    target_norm = normalize_text_for_matching(extracted_target or "")

    is_generic_inhaler = is_generic_inhaler_query_without_device(query_norm)

    matched_mapping, is_exact = match_query_to_device_mapping(query_norm, target_norm, DEFAULT_TAXONOMY_MAPPINGS)
    if is_generic_inhaler:
        matched_mapping = None

    target_usage_topic = matched_mapping.get("usage_topic") if matched_mapping else None
    target_device_name = matched_mapping.get("device_name") if matched_mapping else None

    # Matching with strict priority
    for vid in available_videos:
        if not vid.get("verified", False) or not vid.get("active", True):
            continue

        vid_topic = vid.get("usage_topic") or vid.get("topic") or ""
        vid_dev = vid.get("device_name") or vid.get("medication_or_device") or ""

        # Priority 1: Exact device match
        if target_usage_topic and (vid_topic.lower() == target_usage_topic.lower() or vid_dev.lower() == target_device_name.lower()):
            return vid

        if is_generic_inhaler:
            if vid_topic in ("general_inhaler_usage", "generic_inhaler_usage"):
                return vid

    return None

print("=" * 85)
print("EXACT DEVICE / DELIVERY-SYSTEM MATCHING TEST SUITE (11 CASES)")
print("=" * 85)

# Test 1: Symbicort Turbohaler
t1 = simulate_video_matcher("ازاي استخدم Symbicort Turbohaler؟")
res1 = "PASS" if t1 and t1["device_name"] == "Turbohaler" else "FAIL"
print(f"Test 1: 'ازاي استخدم Symbicort Turbohaler؟'")
print(f"  -> Matched Device: {t1.get('device_name') if t1 else None} | Video: {t1.get('title') if t1 else None} [{res1}]")

# Test 2: Ellipta Inhaler
t2 = simulate_video_matcher("How do I use an Ellipta inhaler?")
res2 = "PASS" if t2 and t2["device_name"] == "Ellipta" else "FAIL"
print(f"\nTest 2: 'How do I use an Ellipta inhaler?'")
print(f"  -> Matched Device: {t2.get('device_name') if t2 else None} | Video: {t2.get('title') if t2 else None} [{res2}]")

# Test 3: Ventolin Evohaler
t3 = simulate_video_matcher("طريقة استخدام Ventolin Evohaler")
res3 = "PASS" if t3 and t3["device_name"] == "Evohaler" else "FAIL"
print(f"\nTest 3: 'طريقة استخدام Ventolin Evohaler'")
print(f"  -> Matched Device: {t3.get('device_name') if t3 else None} | Video: {t3.get('title') if t3 else None} [{res3}]")

# Test 4: Seretide Accuhaler
t4 = simulate_video_matcher("ازاي استخدم Seretide Accuhaler؟")
res4 = "PASS" if t4 and t4["device_name"] == "Accuhaler" else "FAIL"
print(f"\nTest 4: 'ازاي استخدم Seretide Accuhaler؟'")
print(f"  -> Matched Device: {t4.get('device_name') if t4 else None} | Video: {t4.get('title') if t4 else None} [{res4}]")

# Test 5: Generic Inhaler (Must NOT guess Turbohaler or Accuhaler randomly)
t5 = simulate_video_matcher("ازاي استخدم بخاخ الربو؟")
res5 = "PASS" if t5 is None else "FAIL (Guessed a specific device without specification!)"
print(f"\nTest 5: 'ازاي استخدم بخاخ الربو؟' (Generic Inhaler)")
print(f"  -> Result: {t5} (Strict No-Guessing Rule Verified) [{res5}]")

# Test 6: Generic Insulin Pen
t6 = simulate_video_matcher("ازاي استخدم قلم الانسولين؟")
res6 = "PASS" if t6 and t6["device_name"] == "insulin_pen" else "FAIL"
print(f"\nTest 6: 'ازاي استخدم قلم الانسولين؟'")
print(f"  -> Matched Device: {t6.get('device_name') if t6 else None} | Video: {t6.get('title') if t6 else None} [{res6}]")

# Test 7: FreeStyle Libre CGM
t7 = simulate_video_matcher("ازاي استخدم FreeStyle Libre؟")
res7 = "PASS" if t7 and t7["device_name"] == "FreeStyle Libre" else "FAIL"
print(f"\nTest 7: 'ازاي استخدم FreeStyle Libre؟'")
print(f"  -> Matched Device: {t7.get('device_name') if t7 else None} | Video: {t7.get('title') if t7 else None} [{res7}]")

# Test 8: Clinical question on Symbicort (Side effects)
t8 = simulate_video_matcher("What are the side effects of Symbicort?")
res8 = "PASS" if t8 is None else "FAIL (Clinical question triggered video!)"
print(f"\nTest 8: 'What are the side effects of Symbicort?' (Clinical Question)")
print(f"  -> Result: {t8} (Intent Suppressed) [{res8}]")

# Test 9: Drug comparison (Clinical comparison)
t9 = simulate_video_matcher("ما الفرق بين الباراسيتامول والإيبوبروفين؟")
res9 = "PASS" if t9 is None else "FAIL (Comparison triggered video!)"
print(f"\nTest 9: 'ما الفرق بين الباراسيتامول والإيبوبروفين؟' (Clinical Comparison)")
print(f"  -> Result: {t9} (Intent Suppressed) [{res9}]")

# Test 10: Unverified exact-device video
unverified_db = [v for v in MOCK_SUPABASE_VIDEOS if v["id"] == "v-unverified-turbohaler"]
t10 = simulate_video_matcher("ازاي استخدم Symbicort Turbohaler؟", available_videos=unverified_db)
res10 = "PASS" if t10 is None else "FAIL (Unverified video returned!)"
print(f"\nTest 10: Unverified Video Safety Check")
print(f"  -> Result: {t10} (Strictly Rejected) [{res10}]")

# Test 11: Inactive exact-device video
inactive_db = [v for v in MOCK_SUPABASE_VIDEOS if v["id"] == "v-inactive-ellipta"]
t11 = simulate_video_matcher("How do I use an Ellipta inhaler?", available_videos=inactive_db)
res11 = "PASS" if t11 is None else "FAIL (Inactive video returned!)"
print(f"\nTest 11: Inactive Video Safety Check")
print(f"  -> Result: {t11} (Strictly Rejected) [{res11}]")

print("\n" + "=" * 85)
all_passed = all("PASS" in r for r in [res1, res2, res3, res4, res5, res6, res7, res8, res9, res10, res11])
print(f"FINAL RESULT: {'ALL 11 TESTS PASSED SUCCESSFULLY (100%)' if all_passed else 'SOME TESTS FAILED'}")
print("=" * 85)
