import sys
from app.video.video_matcher import get_verified_video

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_all_tests():
    print("=" * 90)
    print("TAMARGI.AI — FINAL VERIFIED INSTRUCTIONAL VIDEO FEATURE SAFETY TEST SUITE")
    print("=" * 90)

    test_results = []

    # -------------------------------------------------------------
    # TEST 1: Generic 'ازاي استخدم البخاخ؟' -> Exact Device Unknown (Safety Correction)
    # -------------------------------------------------------------
    t1 = get_verified_video(query_text="ازاي استخدم البخاخ؟")
    p1 = t1.get("found") is False and t1.get("reason") == "exact_device_unknown"
    test_results.append(("1. Generic 'بخاخ' -> Exact Device Unknown (NOT pMDI)", p1, t1))
    print("Test 1: 'ازاي استخدم البخاخ؟' (Generic Inhaler Safety Check)")
    print(f"  -> Found: {t1.get('found')} | Reason: {t1.get('reason')} [{'PASS' if p1 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 2: Exact Turbohaler Match
    # -------------------------------------------------------------
    t2 = get_verified_video(query_text="ازاي استخدم التربوهيلر؟")
    p2 = t2.get("found") is True and t2.get("usage_topic") == "turbohaler_usage" and t2.get("device_name") == "Turbohaler"
    test_results.append(("2. Exact Turbohaler Match", p2, t2))
    print("Test 2: 'ازاي استخدم التربوهيلر؟' (Exact Turbohaler Match)")
    print(f"  -> Found: {t2.get('found')} | Topic: {t2.get('usage_topic')} | Device: {t2.get('device_name')} [{'PASS' if p2 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 3: Exact Ellipta Match
    # -------------------------------------------------------------
    t3 = get_verified_video(query_text="ازاي استخدم الإليبتا؟")
    p3 = t3.get("found") is True and t3.get("usage_topic") == "ellipta_usage" and t3.get("device_name") == "Ellipta"
    test_results.append(("3. Exact Ellipta Match", p3, t3))
    print("Test 3: 'ازاي استخدم الإليبتا؟' (Exact Ellipta Match)")
    print(f"  -> Found: {t3.get('found')} | Topic: {t3.get('usage_topic')} | Device: {t3.get('device_name')} [{'PASS' if p3 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 4: Exact HandiHaler Match
    # -------------------------------------------------------------
    t4 = get_verified_video(query_text="طريقة استخدام جهاز HandiHaler")
    p4 = t4.get("found") is True and t4.get("usage_topic") == "handihaler_usage" and t4.get("device_name") == "HandiHaler"
    test_results.append(("4. Exact HandiHaler Match", p4, t4))
    print("Test 4: 'طريقة استخدام جهاز HandiHaler' (Exact HandiHaler Match)")
    print(f"  -> Found: {t4.get('found')} | Topic: {t4.get('usage_topic')} | Device: {t4.get('device_name')} [{'PASS' if p4 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 5: Explicit pMDI Match
    # -------------------------------------------------------------
    t5 = get_verified_video(query_text="طريقة استخدام pMDI")
    p5 = t5.get("found") is True and t5.get("usage_topic") == "pmdi_usage" and t5.get("device_name") == "pMDI"
    test_results.append(("5. Explicit pMDI Match", p5, t5))
    print("Test 5: 'طريقة استخدام pMDI' (Explicit pMDI Match)")
    print(f"  -> Found: {t5.get('found')} | Topic: {t5.get('usage_topic')} | Device: {t5.get('device_name')} [{'PASS' if p5 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 6: Explicit PARI BOY Match
    # -------------------------------------------------------------
    t6 = get_verified_video(query_text="طريقة استخدام PARI BOY")
    p6 = t6.get("found") is True and t6.get("usage_topic") == "pari_boy_nebulizer_usage" and t6.get("device_name") == "PARI BOY"
    test_results.append(("6. Explicit PARI BOY Match", p6, t6))
    print("Test 6: 'طريقة استخدام PARI BOY' (Explicit PARI BOY Match)")
    print(f"  -> Found: {t6.get('found')} | Topic: {t6.get('usage_topic')} | Device: {t6.get('device_name')} [{'PASS' if p6 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 7: Generic Nebulizer Query -> Must NOT Return PARI BOY
    # -------------------------------------------------------------
    t7 = get_verified_video(query_text="ازاي أعمل جلسة nebulizer؟")
    p7 = t7.get("found") is False and t7.get("reason") == "no_verified_video"
    test_results.append(("7. Generic Nebulizer -> No PARI BOY Fallback", p7, t7))
    print("Test 7: 'ازاي أعمل جلسة nebulizer؟' (Generic Nebulizer Query)")
    print(f"  -> Found: {t7.get('found')} | Reason: {t7.get('reason')} [{'PASS' if p7 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 8: Verified Arabic Insulin Pen (Saudi MOH)
    # -------------------------------------------------------------
    t8 = get_verified_video(query_text="طريقة استخدام قلم الأنسولين")
    p8 = t8.get("found") is True and t8.get("usage_topic") == "insulin_pen_usage" and "وزارة الصحة" in str(t8.get("source_name"))
    test_results.append(("8. Verified Arabic Insulin Pen", p8, t8))
    print("Test 8: 'طريقة استخدام قلم الأنسولين' (Verified Saudi MOH Video)")
    print(f"  -> Found: {t8.get('found')} | Source: {t8.get('source_name')} | URL: {t8.get('video_url')} [{'PASS' if p8 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 9: Topical Aerosol -> Unsupported Technique
    # -------------------------------------------------------------
    t9 = get_verified_video(query_text="ازاي استخدم بخاخ الليدوكايين الموضعي؟")
    p9 = t9.get("found") is False and t9.get("reason") == "unsupported_technique"
    test_results.append(("9. Topical Aerosol -> Unsupported", p9, t9))
    print("Test 9: 'ازاي استخدم بخاخ الليدوكايين الموضعي؟' (Topical Spray Rejection)")
    print(f"  -> Found: {t9.get('found')} | Reason: {t9.get('reason')} [{'PASS' if p9 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 10: Clinical Contraindication Question -> Not Usage Question
    # -------------------------------------------------------------
    t10 = get_verified_video(query_text="ما هي موانع استخدام دواء باراسيتامول؟")
    p10 = t10.get("found") is False and t10.get("reason") == "not_usage_question"
    test_results.append(("10. Contraindication Question -> Suppressed", p10, t10))
    print("Test 10: 'ما هي موانع استخدام دواء باراسيتامول؟' (Clinical Question Suppression)")
    print(f"  -> Found: {t10.get('found')} | Reason: {t10.get('reason')} [{'PASS' if p10 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 11: Multi-Brand DPI Medication -> Exact Device Unknown
    # -------------------------------------------------------------
    t11 = get_verified_video(query_text="طريقة استخدام دواء فورموتيرول بودرة")
    p11 = t11.get("found") is False and t11.get("reason") == "exact_device_unknown"
    test_results.append(("11. Multi-Brand DPI -> Exact Device Unknown", p11, t11))
    print("Test 11: 'طريقة استخدام دواء فورموتيرول بودرة' (Unresolved DPI Product)")
    print(f"  -> Found: {t11.get('found')} | Reason: {t11.get('reason')} [{'PASS' if p11 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # TEST 12: Inactive Video -> Not Returned
    # -------------------------------------------------------------
    t12 = get_verified_video(usage_topic="inactive_sample_usage")
    p12 = t12.get("found") is False and t12.get("reason") == "inactive_video"
    test_results.append(("12. Inactive Video -> Rejected", p12, t12))
    print("Test 12: Inactive Video Check")
    print(f"  -> Found: {t12.get('found')} | Reason: {t12.get('reason')} [{'PASS' if p12 else 'FAIL'}]\n")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    all_passed = all(r[1] for r in test_results)
    print("=" * 90)
    print(f"FINAL RESULT: {'ALL 12 SAFETY TESTS PASSED (100%)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 90)

    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
