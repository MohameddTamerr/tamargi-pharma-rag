import re
from typing import Optional, Tuple, List, Dict, Any

# Practical usage intent patterns (Arabic & English)
PRACTICAL_INTENT_PATTERNS_AR = [
    r"ازاي\s+(?:استخدم|استعمل|اخد|آخد|احط|أحط|اقيس|أقيس|احقن|أحقن|اركب|أركب|اشغل|أشغل|اغسل|أغسل|اعمل|أعمل|اسوي|أسوي|اجهز|أجهز)",
    r"طريق[ةه]\s+(?:استخدام|استعمال|اخذ|أخذ|وضع|قياس|حقن|تشغيل|تطبيق|اعطاء|إعطاء|تناول|عمل|تجهيز)",
    r"كيفي[ةه]\s+(?:استخدام|استعمال|اخذ|أخذ|وضع|قياس|حقن|تطبيق|اعطاء|إعطاء|تناول|عمل|تجهيز)",
    r"كيف\s+(?:استخدم|استعمل|اخذ|أخذ|اضع|أضع|احقن|أحقن|اطبق|أطبق|اقيس|أقيس|اشغل|أشغل|اعمل|أعمل)",
    r"وريني\s+(?:ازاي|كيف|طريق[ةه]|فيديو)",
    r"علمني\s+(?:ازاي|كيف|طريق[ةه])",
    r"شرح\s+(?:استخدام|استعمال|طريق[ةه]|خطوات|طريقه)",
    r"خطوات\s+(?:استخدام|استعمال|أخذ|اخذ|حقن|قياس|عمل)",
    r"فيديو\s+(?:تعليمي|شرح|توضيحي|طريق[ةه]|استخدام|طريقه)",
    r"طريق[ةه]\s+(?:عمل|استعمال|تشغيل)\s+(?:جهاز|جلس[ةه]|حقن[ةه]|بخاخ)",
    r"عاوز\s+اعرف\s+ازاي\s+(?:استخدم|استعمل|احط|احقن|اشغل|اعمل)",
    r"عايز\s+اعرف\s+ازاي\s+(?:استخدم|استعمل|احط|احقن|اشغل|اعمل)",
    r"جلس[ةه]\s+(?:نيبولايزر|بخار|استنشاق)"
]

PRACTICAL_INTENT_PATTERNS_EN = [
    r"how\s+(?:do\s+i|should\s+i|can\s+i|to)\s+(?:use|take|apply|inject|administer|operate|insert|spray|inhale|measure|check|test|clean)",
    r"(?:instructions|directions|steps|guide|technique|demonstration|tutorial)\s+(?:for|to|on)\s+(?:using|taking|applying|injecting|administering|operating)",
    r"(?:proper|correct|right)\s+way\s+to\s+(?:use|take|apply|inject|administer)",
    r"show\s+me\s+how\s+to\s+(?:use|take|apply|inject|administer|operate)",
    r"demonstrate\s+how\s+to\s+(?:use|inject|apply)",
    r"how\s+is\s+.+\s+(?:used|administered|injected|applied|taken)"
]

# Negative / strictly clinical patterns that should NOT trigger instructional videos
NEGATIVE_CLINICAL_PATTERNS = [
    r"موانع\s+(?:استخدام|استعمال)",
    r"(?:أعراض|اعراض|اثار|آثار)\s+جانبي[ةه]",
    r"(?:تفاعلات|تداخلات)\s+دوائي[ةه]",
    r"(?:الفرق|ايه\s+الفرق|ما\s+الفرق)\s+بين",
    r"بديل",
    r"(?:هل|أهو)\s+(?:آمن|امن)\s+(?:للحامل|للمرضع|للاطفال|للأطفال|لكبار\s+السن)",
    r"دواعي\s+(?:الاستعمال|الاستخدام)",
    r"جرع[ةه]\s+(?:الاطفال|الأطفال|الكبار|مرضى|القصوى)",
    r"contraindication",
    r"side\s+effect",
    r"adverse\s+(?:reaction|event)",
    r"drug\s+interaction",
    r"difference\s+between",
    r"compare",
    r"mechanism\s+of\s+action",
    r"is\s+it\s+safe\s+(?:in|for|during)\s+pregnancy"
]

def normalize_text_for_matching(text: str) -> str:
    """
    Normalizes Arabic, Egyptian Arabic, and English text for robust token/entity matching.
    """
    if not text:
        return ""
    
    t = text.lower().strip()
    # Strip Arabic diacritics & tatweel
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", t)
    # Normalize Alef variations
    t = re.sub(r"[إأآا]", "ا", t)
    # Normalize Teh Marbuta
    t = re.sub(r"ة", "ه", t)
    # Normalize Yaa variations
    t = re.sub(r"ى", "ي", t)
    # Remove punctuation
    t = re.sub(r"[؟?!.,;:\"'()\\[\\]{}]", " ", t)
    # Collapse multiple whitespaces
    t = re.sub(r"\s+", " ", t).strip()
    return t

def detect_video_intent(query: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes user query to detect practical "how-to-use" medical device/medication intent.
    
    Returns:
        (is_practical_intent: bool, extracted_product_or_device: Optional[str])
    """
    if not query or not query.strip():
        return False, None

    q_clean = query.strip()

    # Step 1: Check if query contains negative clinical cues (e.g. side effects, contraindications)
    for neg_pat in NEGATIVE_CLINICAL_PATTERNS:
        if re.search(neg_pat, q_clean, re.IGNORECASE):
            return False, None

    # Step 2: Check for practical usage phrasing patterns
    is_practical = False
    for pat in PRACTICAL_INTENT_PATTERNS_AR + PRACTICAL_INTENT_PATTERNS_EN:
        if re.search(pat, q_clean, re.IGNORECASE):
            is_practical = True
            break

    if not is_practical:
        return False, None

    # Step 3: Extract the product / medication / device candidate segment after intent verb
    extracted_target = None

    # Arabic extraction
    ar_match = re.search(
        r"(?:استخدم|استعمل|اخد|آخد|احط|أحط|اقيس|أقيس|احقن|أحقن|اركب|أركب|تشغيل|تطبيق|طريقة|كيفية|كيف|شرح|خطوات|فيديو)\s+([a-zA-Z\u0600-\u06FF0-9\s\-+]+)",
        q_clean,
        re.IGNORECASE
    )
    if ar_match:
        cand = ar_match.group(1).strip()
        # Clean filler words
        cand = re.sub(r"^(?:استخدام|استعمال|وضع|حقن|قياس|تركيب|عمل|جهاز)\s+", "", cand).strip()
        if cand:
            extracted_target = cand

    # English extraction
    if not extracted_target:
        en_match = re.search(
            r"(?:use|take|apply|inject|administer|operate|insert|spray|inhale|measure|check|test|instructions for|guide for)\s+([a-zA-Z\u0600-\u06FF0-9\s\-+]+)",
            q_clean,
            re.IGNORECASE
        )
        if en_match:
            extracted_target = en_match.group(1).strip()

    # Fallback to whole query if extraction didn't isolate target
    if not extracted_target:
        extracted_target = q_clean

    return True, extracted_target
