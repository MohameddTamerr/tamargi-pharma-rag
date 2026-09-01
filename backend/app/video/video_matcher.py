import os
import re
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings
from app.database.supabase import get_supabase_client
from app.video.intent_detector import detect_video_intent, normalize_text_for_matching

# Approved instructional topics taxonomy
APPROVED_USAGE_TOPICS = [
    "pmdi_usage",
    "aerochamber_usage",
    "vortex_spacer_usage",
    "autohaler_usage",
    "breezhaler_usage",
    "diskus_usage",
    "ellipta_usage",
    "forspiro_usage",
    "genuair_usage",
    "handihaler_usage",
    "nexthaler_usage",
    "novolizer_usage",
    "respimat_usage",
    "turbohaler_usage",
    "spiromax_usage",
    "pari_boy_nebulizer_usage",
    "nasal_spray_usage",
    "nebulizer_usage",
    "eye_drop_usage",
    "eye_ointment_usage",
    "ear_drop_usage",
    "nasal_drop_usage",
    "rectal_suppository_usage",
    "vaginal_pessary_usage",
    "transdermal_patch_usage",
    "subcutaneous_self_injection_usage",
    "insulin_pen_usage"
]

# Verified Arabic instructional video database (Deutsche Atemwegsliga, MSD Manual, Saudi MOH)
DEFAULT_VERIFIED_VIDEOS: List[Dict[str, Any]] = [
    {
        "id": "v-aerochamber-atemwegsliga",
        "title": "طريقة استخدام جهاز حجرة الاستنشاق (AeroChamber)",
        "usage_topic": "aerochamber_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "spacer",
        "device_name": "AeroChamber",
        "aliases": ["aerochamber", "ايروشمبر", "حجرة الاستنشاق", "سبيسر ايروشمبر"],
        "language": "ar",
        "video_url": "https://youtu.be/wtSw3U9cz0M",
        "thumbnail_url": "https://img.youtube.com/vi/wtSw3U9cz0M/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-autohaler-atemwegsliga",
        "title": "طريقة استخدام بخاخ الأوتوهيلر (Autohaler)",
        "usage_topic": "autohaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "breath_actuated_MDI",
        "device_name": "Autohaler",
        "aliases": ["autohaler", "اوتوهيلر", "اوتوهيلار"],
        "language": "ar",
        "video_url": "https://youtu.be/6SxnAJWAJBg",
        "thumbnail_url": "https://img.youtube.com/vi/6SxnAJWAJBg/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-breezhaler-mono-atemwegsliga",
        "title": "طريقة استخدام بخاخ البريزهيلر أحادي المادة (Breezhaler)",
        "usage_topic": "breezhaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Breezhaler",
        "aliases": ["breezhaler", "بريزهيلر", "اونبريز"],
        "language": "ar",
        "video_url": "https://youtu.be/P16vS8_4HqE",
        "thumbnail_url": "https://img.youtube.com/vi/P16vS8_4HqE/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-breezhaler-combo-atemwegsliga",
        "title": "طريقة استخدام بخاخ البريزهيلر المركب (Breezhaler Combination)",
        "usage_topic": "breezhaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Breezhaler",
        "aliases": ["breezhaler combination", "بريزهيلر مركب", "التيريز"],
        "language": "ar",
        "video_url": "https://youtu.be/K_l5-9bsASc",
        "thumbnail_url": "https://img.youtube.com/vi/K_l5-9bsASc/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-diskus-atemwegsliga",
        "title": "طريقة استخدام بخاخ الديسكوس / أكيوهيلر (Diskus / Accuhaler)",
        "usage_topic": "diskus_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Diskus",
        "aliases": ["diskus", "accuhaler", "ديسكوس", "اكيوهيلر", "أكيوهيلر", "سيريتيد"],
        "language": "ar",
        "video_url": "https://youtu.be/gPanzwWilYg",
        "thumbnail_url": "https://img.youtube.com/vi/gPanzwWilYg/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-pmdi-atemwegsliga",
        "title": "طريقة استخدام بخاخ الجرعات المقننة المضغوط (pMDI / Metered Dose Inhaler)",
        "usage_topic": "pmdi_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "pMDI",
        "device_name": "pMDI",
        "aliases": ["pmdi", "metered dose inhaler", "evohaler", "بخاخ الربو المضغوط", "بخاخ مضغوط", "جرعات مقننة", "ايفوهيلر", "فنتولين بخاخ"],
        "language": "ar",
        "video_url": "https://youtu.be/y4KmmNuaBFo",
        "thumbnail_url": "https://img.youtube.com/vi/y4KmmNuaBFo/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-pmdi-msd",
        "title": "طريقة استعمال أجهزة الاستنشاق بالجرعات المقننة",
        "usage_topic": "pmdi_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "pMDI",
        "device_name": "pMDI",
        "aliases": ["pmdi msd", "استنشاق جرعات مقننة msd"],
        "language": "ar",
        "video_url": "https://www.msdmanuals.com/ar/home/multimedia/video/طريقة-استعمال-أجهزة-الاستنشاق-بالجرعات-المقننة",
        "thumbnail_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "source_name": "MSD Manual Arabic",
        "source_url": "https://www.msdmanuals.com/ar",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-ellipta-atemwegsliga",
        "title": "طريقة استخدام بخاخ الإليبيتا (Ellipta)",
        "usage_topic": "ellipta_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Ellipta",
        "aliases": ["ellipta", "اليبيتا", "إليبتَا", "ريلفار إليبيتا", "تريليجي"],
        "language": "ar",
        "video_url": "https://youtu.be/F7YWhnNFdnQ",
        "thumbnail_url": "https://img.youtube.com/vi/F7YWhnNFdnQ/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-forspiro-atemwegsliga",
        "title": "طريقة استخدام بخاخ فورسبييرو (Forspiro)",
        "usage_topic": "forspiro_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Forspiro",
        "aliases": ["forspiro", "فورسبييرو", "فورسبيرو"],
        "language": "ar",
        "video_url": "https://youtu.be/y94Gi8XxQQU",
        "thumbnail_url": "https://img.youtube.com/vi/y94Gi8XxQQU/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-genuair-atemwegsliga",
        "title": "طريقة استخدام بخاخ جينواير (Genuair)",
        "usage_topic": "genuair_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Genuair",
        "aliases": ["genuair", "جينواير"],
        "language": "ar",
        "video_url": "https://youtu.be/xMD9HpAmEgk",
        "thumbnail_url": "https://img.youtube.com/vi/xMD9HpAmEgk/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-handihaler-atemwegsliga",
        "title": "طريقة استخدام بخاخ الهاندي هيلر (HandiHaler)",
        "usage_topic": "handihaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "HandiHaler",
        "aliases": ["handihaler", "هاندي هيلر", "هانديهيلر", "سبيريفا كبسول"],
        "language": "ar",
        "video_url": "https://youtu.be/ptO0aIGLSRY",
        "thumbnail_url": "https://img.youtube.com/vi/ptO0aIGLSRY/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-nexthaler-atemwegsliga",
        "title": "طريقة استخدام بخاخ نكست هيلر (NEXThaler)",
        "usage_topic": "nexthaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "NEXThaler",
        "aliases": ["nexthaler", "نكست هيلر", "نكستهيلر"],
        "language": "ar",
        "video_url": "https://youtu.be/Ur_grKNKuNQ",
        "thumbnail_url": "https://img.youtube.com/vi/Ur_grKNKuNQ/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-novolizer-atemwegsliga",
        "title": "طريقة استخدام بخاخ نوفولايزر (Novolizer)",
        "usage_topic": "novolizer_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Novolizer",
        "aliases": ["novolizer", "نوفولايزر", "نوفوليزر"],
        "language": "ar",
        "video_url": "https://youtu.be/wHu8o5fiOqA",
        "thumbnail_url": "https://img.youtube.com/vi/wHu8o5fiOqA/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-respimat-atemwegsliga",
        "title": "طريقة استخدام بخاخ الريسبيمات (Respimat)",
        "usage_topic": "respimat_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "SMI",
        "device_name": "Respimat",
        "aliases": ["respimat", "ريسبيمات", "سبيريفا ريسبيمات"],
        "language": "ar",
        "video_url": "https://youtu.be/6wNDQfeZEX4",
        "thumbnail_url": "https://img.youtube.com/vi/6wNDQfeZEX4/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-turbohaler-atemwegsliga",
        "title": "طريقة استخدام بخاخ التربوهيلر (Turbohaler)",
        "usage_topic": "turbohaler_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Turbohaler",
        "aliases": ["turbohaler", "turbuhaler", "تربوهيلر", "تيربوهيلر", "سيمبيكورت تربوهيلر"],
        "language": "ar",
        "video_url": "https://youtu.be/Xnk8oYQPbaw",
        "thumbnail_url": "https://img.youtube.com/vi/Xnk8oYQPbaw/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-spiromax-atemwegsliga",
        "title": "طريقة استخدام بخاخ سبايروماكس (Spiromax)",
        "usage_topic": "spiromax_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "Spiromax",
        "aliases": ["spiromax", "سبايروماكس", "سبيروماكس"],
        "language": "ar",
        "video_url": "https://youtu.be/ebestHd2r08",
        "thumbnail_url": "https://img.youtube.com/vi/ebestHd2r08/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-vortex-atemwegsliga",
        "title": "طريقة استخدام حجرة الاستنشاق فورتكس (Vortex Spacer)",
        "usage_topic": "vortex_spacer_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "spacer",
        "device_name": "Vortex",
        "aliases": ["vortex", "فورتكس", "فورتكس سبيسر"],
        "language": "ar",
        "video_url": "https://youtu.be/6a-IO2THEaA",
        "thumbnail_url": "https://img.youtube.com/vi/6a-IO2THEaA/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-pari-boy-atemwegsliga",
        "title": "طريقة استخدام جهاز نيبولايزر باري بوي (PARI BOY Nebulizer)",
        "usage_topic": "pari_boy_nebulizer_usage",
        "category": "nebulizer",
        "dosage_form": "inhalation",
        "device_type": "nebulizer",
        "device_name": "PARI BOY",
        "aliases": ["pari boy", "باري بوي", "باري بوي نيبولايزر", "pari boy nebulizer"],
        "language": "ar",
        "video_url": "https://youtu.be/sGg9Xkv4rnI",
        "thumbnail_url": "https://img.youtube.com/vi/sGg9Xkv4rnI/hqdefault.jpg",
        "source_name": "Deutsche Atemwegsliga e.V.",
        "source_url": "https://www.atemwegsliga.de/richtig-inhalieren/zu-den-videos-international/arabisch.html",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": True
    },
    {
        "id": "v-insulin-pen-saudi-moh",
        "title": "طريقة استخدام قلم الأنسولين",
        "usage_topic": "insulin_pen_usage",
        "category": "insulin_injection",
        "dosage_form": "subcutaneous_injection",
        "device_type": "pen_injector",
        "device_name": "Generic Insulin Pen",
        "aliases": ["insulin pen", "قلم انسولين", "قلم الانسولين", "حقن الانسولين بالقلم"],
        "language": "ar",
        "video_url": "https://www.youtube.com/watch?v=7SLD3YQtNoE",
        "thumbnail_url": "https://img.youtube.com/vi/7SLD3YQtNoE/hqdefault.jpg",
        "source_name": "وزارة الصحة السعودية",
        "source_url": "https://www.moh.gov.sa",
        "source_tier": "B_government_health_authority",
        "verified": True,
        "active": True
    },
    {
        "id": "v-inactive-sample",
        "title": "فيديو تجريبي غير مفعل (Inactive)",
        "usage_topic": "inactive_sample_usage",
        "category": "inhaler",
        "dosage_form": "inhalation",
        "device_type": "DPI",
        "device_name": "inactive_device",
        "aliases": ["inactive_sample"],
        "language": "ar",
        "video_url": "https://example.com/inactive.mp4",
        "source_name": "Test Source",
        "source_tier": "B_recognized_medical_organization",
        "verified": True,
        "active": False
    }
]

# Medication-to-Device Mappings taxonomy
DEFAULT_MEDICATION_DEVICE_MAPPINGS: List[Dict[str, Any]] = [
    {
        "generic_name": "budesonide/formoterol",
        "brand_name": "Symbicort Turbohaler",
        "aliases": ["symbicort", "turbohaler", "turbuhaler", "تربوهيلر", "تيربوهيلر", "سيمبيكورت", "سيمبيكورت تربوهيلر"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "DPI",
        "device_name": "Turbohaler",
        "usage_topic": "turbohaler_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "fluticasone/vilanterol",
        "brand_name": "Relvar Ellipta",
        "aliases": ["ellipta", "relvar", "trelegy", "ريلفار", "تريليجي", "اليبيتا", "إليبتَا", "اليبتا"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "DPI",
        "device_name": "Ellipta",
        "usage_topic": "ellipta_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "salmeterol/fluticasone",
        "brand_name": "Seretide Accuhaler",
        "aliases": ["seretide", "accuhaler", "diskus", "أكيوهيلر", "اكيوهيلر", "ديسكوس", "سيريتيد"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "DPI",
        "device_name": "Accuhaler",
        "usage_topic": "diskus_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "tiotropium",
        "brand_name": "Spiriva Respimat",
        "aliases": ["respimat", "spiriva respimat", "ريسبيمات", "سبيريفا ريسبيمات"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "SMI",
        "device_name": "Respimat",
        "usage_topic": "respimat_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "tiotropium",
        "brand_name": "Spiriva HandiHaler",
        "aliases": ["handihaler", "spiriva handihaler", "هاندي هيلر", "هانديهيلر", "سبيريفا كبسول"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "DPI",
        "device_name": "HandiHaler",
        "usage_topic": "handihaler_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "salbutamol",
        "brand_name": "Ventolin Evohaler",
        "aliases": ["ventolin", "evohaler", "فنتولين", "فينتولين", "ايفوهيلر", "بخاخ فنتولين"],
        "dosage_form": "inhalation",
        "device_category": "inhaler",
        "device_type": "pMDI",
        "device_name": "Evohaler",
        "usage_topic": "pmdi_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "insulin glargine / detemir / degludec",
        "brand_name": "Insulin Pen",
        "aliases": ["insulin pen", "قلم انسولين", "قلم الانسولين", "حقن الانسولين بالقلم"],
        "dosage_form": "injection",
        "device_category": "insulin_injection",
        "device_type": "pen_injector",
        "device_name": "insulin_pen",
        "usage_topic": "insulin_pen_usage",
        "exact_device_verified": True,
        "active": True
    },
    {
        "generic_name": "glucose sensor",
        "brand_name": "FreeStyle Libre",
        "aliases": ["freestyle libre", "freestyle", "فري ستايل ليبري", "فري ستايل"],
        "dosage_form": "sensor",
        "device_category": "glucose_monitoring",
        "device_type": "CGM",
        "device_name": "FreeStyle Libre",
        "usage_topic": "cgm_usage",
        "exact_device_verified": True,
        "active": True
    }
]

# Non-inhaler topical aerosol products (Must NOT return respiratory inhaler videos)
TOPICAL_NON_INHALER_TERMS = [
    "lidocaine", "terbinafine", "clotrimazole", "betamethasone foam",
    "topical spray", "topical aerosol", "بخاخ موضعي", "بخاخ جلد", "ليدوكايين", "كلوتريمازول", "تيربينافين"
]

def fetch_db_videos() -> List[Dict[str, Any]]:
    """Fetches verified videos from Supabase, falls back to built-in verified registry."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("verified_videos")\
                .select("id, title, usage_topic, category, dosage_form, device_type, device_name, aliases, language, video_url, thumbnail_url, source_name, source_url, source_tier, verified, active, verification_notes")\
                .execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception:
            pass
    return DEFAULT_VERIFIED_VIDEOS

def fetch_db_mappings() -> List[Dict[str, Any]]:
    """Fetches medication device mappings from Supabase."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("medication_device_mappings")\
                .select("id, generic_name, brand_name, aliases, dosage_form, device_category, device_type, device_name, usage_topic, exact_device_verified, active")\
                .execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception:
            pass
    return DEFAULT_MEDICATION_DEVICE_MAPPINGS

def log_video_match(
    query_text: Optional[str],
    detected_medication: Optional[str],
    detected_brand: Optional[str],
    detected_usage_intent: bool,
    resolved_usage_topic: Optional[str],
    resolved_device: Optional[str],
    video_id: Optional[str],
    match_status: str
):
    """Audits video matching decisions in public.video_match_logs."""
    client = get_supabase_client()
    if client:
        try:
            client.table("video_match_logs").insert({
                "query_text": query_text,
                "detected_medication": detected_medication,
                "detected_brand": detected_brand,
                "detected_usage_intent": detected_usage_intent,
                "resolved_usage_topic": resolved_usage_topic,
                "resolved_device": resolved_device,
                "video_id": video_id,
                "match_status": match_status
            }).execute()
        except Exception:
            pass

def is_topical_non_inhaler(text_norm: str) -> bool:
    """Detects topical aerosols/sprays that must not be treated as respiratory inhalers."""
    return any(term in text_norm for term in TOPICAL_NON_INHALER_TERMS)

def is_unresolved_inhaler_device(text_norm: str) -> bool:
    """
    CRITICAL SAFETY CHECK:
    Detects if the query asks about an inhaler ("بخاخ", "البخاخ", "بخاخة", "inhaler", "بودرة")
    without specifying the exact physical device or explicit pMDI / metered-dose formulation.
    """
    # 1. Terms indicating an inhaler/delivery inquiry
    generic_inhaler_terms = [
        "بخاخ", "البخاخ", "بخاخه", "البخاخه", "بخاخ الربو", "بخاخ الصدر", "inhaler",
        "بخاخ بودرة", "بودرة استنشاق", "بودرة", "بودره", "inhalation powder", "dpi", "dry powder",
        "formoterol", "فورموتيرول", "tiotropium", "تيوتروبيوم", "سيمبيكورت من غير جهاز",
        "كبسول استنشاق", "كبسولات استنشاق"
    ]
    
    # 2. Terms proving exact physical device or delivery model
    exact_device_or_brand_terms = [
        "turbohaler", "turbuhaler", "تربوهيلر", "تيربوهيلر", "تربوهيلار",
        "ellipta", "اليبيتا", "إليبتَا", "اليبتا", "إليبتا", "ريلفار", "تريليجي",
        "accuhaler", "diskus", "أكيوهيلر", "اكيوهيلر", "ديسكوس", "سيريتيد",
        "respimat", "ريسبيمات",
        "handihaler", "هاندي هيلر", "هانديهيلر",
        "breezhaler", "بريزهيلر", "اونبريز",
        "genuair", "جينواير",
        "forspiro", "فورسبييرو", "فورسبيرو",
        "novolizer", "نوفولايزر", "نوفوليزر",
        "nexthaler", "نكست هيلر", "نكستهيلر",
        "spiromax", "سبايروماكس", "سبيروماكس",
        "autohaler", "اوتوهيلر", "اوتوهيلار",
        "aerochamber", "ايروشمبر", "سبيسر", "spacer", "حجرة الاستنشاق",
        "vortex", "فورتكس",
        # Explicit pMDI indicators
        "pmdi", "metered dose", "جرعات مقننة", "جرعات مقننه", "بخاخ مضغوط", "بخاخه مضغوطه", "evohaler", "ايفوهيلر", "فنتولين"
    ]

    norm_inhaler = [normalize_text_for_matching(t) for t in generic_inhaler_terms]
    norm_exact = [normalize_text_for_matching(t) for t in exact_device_or_brand_terms]

    has_inhaler = any(ind in text_norm for ind in norm_inhaler)
    has_exact = any(dev in text_norm for dev in norm_exact)

    return has_inhaler and not has_exact

def get_verified_video(
    generic_name: Optional[str] = None,
    brand_name: Optional[str] = None,
    dosage_form: Optional[str] = None,
    device_name: Optional[str] = None,
    usage_topic: Optional[str] = None,
    query_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Core backend service for Verified Instructional Medical Videos.
    
    Matching Hierarchy:
    1. Practical usage intent detection (suppresses contraindications / clinical queries).
    2. Topical aerosol vs respiratory inhaler discrimination.
    3. Strict safety check: Generic 'بخاخ' alone does NOT default to pMDI.
    4. Rectal suppository vs vaginal pessary discrimination.
    5. Nebulizer vs PARI BOY separation (PARI BOY requires explicit PARI BOY resolution).
    6. 4-tier matching priority:
       - Tier 1: Exact brand + exact device match
       - Tier 2: Exact verified device match
       - Tier 3: Approved generic technique match (when explicit form/technique is resolved)
       - Tier 4: No video (exact_device_unknown, brand_required, unsupported_technique)
    7. Safety verification (verified = true AND active = true).
    """
    full_text = f"{query_text or ''} {generic_name or ''} {brand_name or ''} {device_name or ''} {dosage_form or ''}".strip()
    text_norm = normalize_text_for_matching(full_text)

    # 1. Detect practical usage intent
    if query_text:
        is_practical, extracted_cand = detect_video_intent(query_text)
        if not is_practical:
            log_video_match(query_text, generic_name, brand_name, False, None, None, None, "not_usage_question")
            return {"found": False, "reason": "not_usage_question"}
        if not text_norm and extracted_cand:
            text_norm = normalize_text_for_matching(extracted_cand)

    # 2. Check for Topical Aerosols (Must NOT return inhaler videos)
    if is_topical_non_inhaler(text_norm):
        log_video_match(query_text, generic_name, brand_name, True, None, None, None, "unsupported_technique")
        return {"found": False, "reason": "unsupported_technique"}

    # 3. SAFETY CHECK: Generic 'بخاخ' / 'inhaler' without exact device or explicit pMDI formulation
    if is_unresolved_inhaler_device(text_norm):
        log_video_match(query_text, generic_name, brand_name, True, None, None, None, "exact_device_unknown")
        return {"found": False, "reason": "exact_device_unknown"}

    # Load databases
    videos = fetch_db_videos()
    mappings = fetch_db_mappings()

    matched_topic: Optional[str] = usage_topic
    matched_device: Optional[str] = device_name
    match_tier: int = 99

    # Check for Explicit PARI BOY first (Strict separation from generic nebulizer)
    if any(w in text_norm for w in ["pari boy", "باري بوي"]):
        matched_topic = "pari_boy_nebulizer_usage"
        matched_device = "PARI BOY"
        match_tier = 2

    # Tier 1 & 2: Exact Brand & Device Mapping Resolution
    if not matched_topic:
        for m in mappings:
            if not m.get("active", True):
                continue
            m_brand = normalize_text_for_matching(m.get("brand_name", ""))
            m_dev = normalize_text_for_matching(m.get("device_name", ""))
            m_aliases = [normalize_text_for_matching(a) for a in (m.get("aliases") or [])]

            if m_brand and m_brand in text_norm:
                matched_topic = m.get("usage_topic")
                matched_device = m.get("device_name")
                match_tier = 1
                break

            if m_dev and m_dev in text_norm and len(m_dev) > 3:
                matched_topic = m.get("usage_topic")
                matched_device = m.get("device_name")
                match_tier = 2
                break

            for a in m_aliases:
                if a and a in text_norm and len(a) > 2 and a not in ("بخاخ", "بخاخ الربو", "inhaler"):
                    matched_topic = m.get("usage_topic")
                    matched_device = m.get("device_name")
                    match_tier = 2
                    break
            if match_tier in (1, 2):
                break

    # Direct search on video device names and specific aliases
    if not matched_topic:
        for v in videos:
            v_topic = v.get("usage_topic", "")
            v_dev = normalize_text_for_matching(v.get("device_name", ""))
            v_aliases = [normalize_text_for_matching(a) for a in (v.get("aliases") or [])]

            # Prevent generic nebulizer from matching PARI BOY
            if v_topic == "pari_boy_nebulizer_usage" and not any(w in text_norm for w in ["pari boy", "باري بوي"]):
                continue

            if v_dev and v_dev in text_norm and len(v_dev) > 3:
                matched_topic = v.get("usage_topic")
                matched_device = v.get("device_name")
                match_tier = 2
                break

            for a in v_aliases:
                if a and a in text_norm and len(a) > 3 and a not in ("بخاخ", "بخاخ الربو", "inhaler", "nebulizer", "نيبولايزر"):
                    matched_topic = v.get("usage_topic")
                    matched_device = v.get("device_name")
                    match_tier = 2
                    break
            if match_tier == 2:
                break

    # Tier 3: Approved Generic Technique Resolution
    if not matched_topic:
        # Explicit pMDI phrasing
        if any(w in text_norm for w in ["pmdi", "metered dose", "جرعات مقننة", "جرعات مقننه", "بخاخ مضغوط", "بخاخه مضغوطه", "evohaler", "ايفوهيلر"]):
            matched_topic = "pmdi_usage"
            matched_device = "pMDI"
            match_tier = 3
        # Generic Nebulizer (Does NOT return PARI BOY)
        elif any(w in text_norm for w in ["nebulizer", "نيبولايزر", "جلسه بخار", "جلسة بخار", "استنشاق بخار"]):
            matched_topic = "nebulizer_usage"
            matched_device = "Nebulizer"
            match_tier = 3
        # Insulin pen
        elif any(w in text_norm for w in ["insulin pen", "قلم انسولين", "قلم الانسولين", "حقن الانسولين بالقلم"]):
            matched_topic = "insulin_pen_usage"
            matched_device = "Generic Insulin Pen"
            match_tier = 3
        # Eye drops
        elif any(w in text_norm for w in ["eye drop", "eye drops", "قطره عين", "قطرة عين", "قطرات العين"]):
            matched_topic = "eye_drop_usage"
            matched_device = "eye_drop"
            match_tier = 3
        # Eye ointment
        elif any(w in text_norm for w in ["eye ointment", "مرهم عين", "مرهم العين"]):
            matched_topic = "eye_ointment_usage"
            matched_device = "eye_ointment"
            match_tier = 3
        # Ear drops
        elif any(w in text_norm for w in ["ear drop", "ear drops", "قطره اذن", "قطرة اذن", "قطرة الأذن"]):
            matched_topic = "ear_drop_usage"
            matched_device = "ear_drop"
            match_tier = 3
        # Nasal spray
        elif any(w in text_norm for w in ["nasal spray", "بخاخ انف", "بخاخ الانف", "بخاخ الأنف"]):
            matched_topic = "nasal_spray_usage"
            matched_device = "nasal_spray"
            match_tier = 3
        # Nasal drops
        elif any(w in text_norm for w in ["nasal drop", "nasal drops", "قطره انف", "قطرة انف"]):
            matched_topic = "nasal_drop_usage"
            matched_device = "nasal_drops"
            match_tier = 3
        # Vaginal pessary (Strictly separate from rectal)
        elif any(w in text_norm for w in ["vaginal suppository", "pessary", "لبوس مهبلي", "تحاميل مهبلية"]):
            matched_topic = "vaginal_pessary_usage"
            matched_device = "vaginal_pessary"
            match_tier = 3
        # Rectal suppository
        elif any(w in text_norm for w in ["suppository", "suppositories", "لبوس شرجي", "تحاميل شرجية"]):
            matched_topic = "rectal_suppository_usage"
            matched_device = "rectal_suppository"
            match_tier = 3
        # Transdermal patch
        elif any(w in text_norm for w in ["transdermal patch", "patch", "لاصقه طبيه", "لاصقة طبية", "لصقه"]):
            matched_topic = "transdermal_patch_usage"
            matched_device = "transdermal_patch"
            match_tier = 3

    if not matched_topic:
        log_video_match(query_text, generic_name, brand_name, True, None, None, None, "unsupported_technique")
        return {"found": False, "reason": "unsupported_technique"}

    # Find the corresponding video in the verified videos repository
    candidate_video = None
    for v in videos:
        v_topic = v.get("usage_topic", "")
        v_dev = v.get("device_name", "")

        # Strict safety check: Never return PARI BOY for generic nebulizer_usage
        if matched_topic == "nebulizer_usage" and v_topic == "pari_boy_nebulizer_usage":
            continue

        if v_topic.lower() == matched_topic.lower():
            candidate_video = v
            break

    if not candidate_video or not candidate_video.get("video_url"):
        log_video_match(query_text, generic_name, brand_name, True, matched_topic, matched_device, None, "no_verified_video")
        return {"found": False, "reason": "no_verified_video"}

    # Strict status checks
    if not candidate_video.get("active", True):
        log_video_match(query_text, generic_name, brand_name, True, matched_topic, matched_device, candidate_video.get("id"), "inactive_video")
        return {"found": False, "reason": "inactive_video"}

    if not candidate_video.get("verified", True):
        log_video_match(query_text, generic_name, brand_name, True, matched_topic, matched_device, candidate_video.get("id"), "unverified_video")
        return {"found": False, "reason": "no_verified_video"}

    log_video_match(query_text, generic_name, brand_name, True, matched_topic, matched_device, candidate_video.get("id"), "matched")

    return {
        "found": True,
        "id": str(candidate_video.get("id")),
        "title": candidate_video.get("title"),
        "video_url": candidate_video.get("video_url"),
        "thumbnail_url": candidate_video.get("thumbnail_url"),
        "source_name": candidate_video.get("source_name", "Deutsche Atemwegsliga e.V."),
        "source_url": candidate_video.get("source_url"),
        "source_tier": candidate_video.get("source_tier", "B_recognized_medical_organization"),
        "usage_topic": candidate_video.get("usage_topic"),
        "device_name": candidate_video.get("device_name"),
        "category": candidate_video.get("category"),
        "dosage_form": candidate_video.get("dosage_form"),
        "device_type": candidate_video.get("device_type"),
        "language": candidate_video.get("language", "ar")
    }

# Backward compatibility aliases
DEFAULT_TAXONOMY_MAPPINGS = DEFAULT_MEDICATION_DEVICE_MAPPINGS

def match_query_to_device_mapping(query: str, target: Optional[str] = None, mappings=None) -> Tuple[Optional[Dict[str, Any]], bool]:
    target_mappings = mappings if mappings is not None else fetch_db_mappings()
    text_norm = normalize_text_for_matching(f"{query} {target or ''}")
    for m in target_mappings:
        m_brand = normalize_text_for_matching(m.get("brand_name", ""))
        m_dev = normalize_text_for_matching(m.get("device_name", ""))
        m_aliases = [normalize_text_for_matching(a) for a in (m.get("aliases") or [])]
        if m_brand and m_brand in text_norm:
            return m, True
        if m_dev and m_dev in text_norm:
            return m, True
        for a in m_aliases:
            if a and a in text_norm and len(a) > 2 and a not in ("بخاخ", "بخاخ الربو", "inhaler"):
                return m, True
    return None, False

def is_generic_inhaler_query_without_device(query: str) -> bool:
    text_norm = normalize_text_for_matching(query)
    return is_unresolved_inhaler_device(text_norm)

def find_verified_video(query: str, user_lang: str = "ar") -> Optional[Dict[str, Any]]:
    """Helper preserving compatibility with existing Chat pipeline."""
    res = get_verified_video(query_text=query)
    if res.get("found"):
        return res
    return None
