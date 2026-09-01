import re
from typing import Dict, List, Optional, Tuple, Set

# Comprehensive brand-to-generic pharmaceutical dictionary in Egyptian healthcare
BRAND_TO_GENERIC: Dict[str, str] = {
    "brufen": "ibuprofen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "panadol": "paracetamol",
    "abimol": "paracetamol",
    "paramol": "paracetamol",
    "tylenol": "paracetamol",
    "cetamol": "paracetamol",
    "adwiflam": "diclofenac",
    "cataflam": "diclofenac",
    "voltaren": "diclofenac",
    "diclac": "diclofenac",
    "olfen": "diclofenac",
    "augmentin": "amoxicillin",
    "amoxil": "amoxicillin",
    "hibiotic": "amoxicillin",
    "curam": "amoxicillin",
    "klacid": "clarithromycin",
    "zithrokan": "azithromycin",
    "zithromax": "azithromycin",
    "ciprofar": "ciprofloxacin",
    "cipro": "ciprofloxacin",
    "tavanic": "levofloxacin",
    "glucophage": "metformin",
    "cidophage": "metformin",
    "amaryl": "glimepiride",
    "januvia": "sitagliptin",
    "forxiga": "dapagliflozin",
    "jardiance": "empagliflozin",
    "lantus": "insulin glargine",
    "toujeo": "insulin glargine",
    "novorapid": "insulin aspart",
    "humalog": "insulin lispro",
    "concor": "bisoprolol",
    "bisocard": "bisoprolol",
    "capoten": "captopril",
    "zestril": "lisinopril",
    "cozaar": "losartan",
    "diovan": "valsartan",
    "norvasc": "amlodipine",
    "lipitor": "atorvastatin",
    "atormac": "atorvastatin",
    "crestor": "rosuvastatin",
    "plavix": "clopidogrel",
    "clexane": "enoxaparin",
    "aspirin": "acetylsalicylic acid",
    "aspocid": "acetylsalicylic acid",
    "aggrex": "acetylsalicylic acid",
    "ventolin": "salbutamol",
    "symbicort": "budesonide/formoterol",
    "relvar": "fluticasone/vilanterol",
    "seretide": "salmeterol/fluticasone",
    "spiriva": "tiotropium",
    "controloc": "pantoprazole",
    "nexium": "esomeprazole",
    "antodine": "famotidine",
    "gastrazole": "omeprazole",
    "lasix": "furosemide",
    "aldactone": "spironolactone"
}

# Arabic brand/generic transliterations
ARABIC_MED_ALIASES: Dict[str, str] = {
    "بروفين": "ibuprofen",
    "ادفل": "ibuprofen",
    "بنادول": "paracetamol",
    "ابيمول": "paracetamol",
    "بارامول": "paracetamol",
    "باراسيتامول": "paracetamol",
    "كتفلام": "diclofenac",
    "فولتارين": "diclofenac",
    "ديكلاك": "diclofenac",
    "اوجمنتين": "amoxicillin",
    "أوجمنتين": "amoxicillin",
    "اموكسيل": "amoxicillin",
    "اموكسيسيلين": "amoxicillin",
    "أموكسيسيلين": "amoxicillin",
    "جلوكوفاج": "metformin",
    "سيدوفاج": "metformin",
    "ميتفورمين": "metformin",
    "كونكور": "bisoprolol",
    "اسبرين": "acetylsalicylic acid",
    "أسبرين": "acetylsalicylic acid",
    "اسبوسيد": "acetylsalicylic acid",
    "فنتولين": "salbutamol",
    "سيمبيكورت": "budesonide/formoterol",
    "سيريتيد": "salmeterol/fluticasone",
    "سبيريفا": "tiotropium",
    "كونترولوك": "pantoprazole",
    "نكسيوم": "esomeprazole",
    "لازيكس": "furosemide",
    "وارفارين": "warfarin",
    "ماريفان": "warfarin",
    "مارفان": "warfarin",
    "ميثوتريكسات": "methotrexate",
    "ميثوتركسات": "methotrexate",
    "ديكساميثازون": "dexamethasone",
    "ديكساميزون": "dexamethasone",
    "بروبرانولول": "propranolol",
    "اندرال": "propranolol",
    "إندرال": "propranolol",
    "سيلدينافيل": "sildenafil",
    "فياجرا": "sildenafil",
    "فياغرا": "sildenafil",
    "كلوبيدوجريل": "clopidogrel",
    "بلافيكس": "clopidogrel",
    "اوميبرازول": "omeprazole",
    "أوميبرازول": "omeprazole",
    "كابتوبريل": "captopril",
    "كابوتين": "captopril",
    "سبيرونولاكتون": "spironolactone",
    "الداكتون": "spironolactone",
    "إنوكسبارين": "enoxaparin",
    "انوكسبارين": "enoxaparin",
    "كليكسان": "enoxaparin",
    "أنسولين": "insulin",
    "انسولين": "insulin",
    "سيفالكسين": "cephalexin",
    "سيفاليكسين": "cephalexin"
}

# Drug allergy classes and cross-reactivity mapping
ALLERGEN_CLASS_MAP: Dict[str, Set[str]] = {
    "penicillins": {
        "penicillin", "amoxicillin", "ampicillin", "augmentin", "amoxil", "hibiotic",
        "curam", "piperacillin", "flucloxacillin", "amoxicillin/clavulanate", "بنسلين", "بنسيلين", "اموكسيسيلين"
    },
    "cephalosporins": {
        "cephalexin", "cefuroxime", "ceftriaxone", "cefotaxime", "cefepime", "cefixime", "سيفالوسبورين"
    },
    "sulfonamides": {
        "sulfamethoxazole", "bactrim", "septrin", "sulfasalazine", "sulfadiazine", "sulfa", "سلفا"
    },
    "nsaids": {
        "ibuprofen", "diclofenac", "ketoprofen", "naproxen", "aspirin", "acetylsalicylic acid",
        "celecoxib", "meloxicam", "piroxicam", "indomethacin", "cataflam", "voltaren", "brufen",
        "advil", "aspocid", "مسكنات", "مضادات الالتهاب اللاستيرويدية"
    }
}

# Chronic conditions normalization
CONDITION_NORMALIZATION: Dict[str, str] = {
    "diabetes": "diabetes_mellitus",
    "diabetes mellitus": "diabetes_mellitus",
    "type 2 diabetes": "diabetes_mellitus",
    "type 1 diabetes": "diabetes_mellitus",
    "سكر": "diabetes_mellitus",
    "مرض السكر": "diabetes_mellitus",
    "السكري": "diabetes_mellitus",
    "hypertension": "hypertension",
    "high blood pressure": "hypertension",
    "ضغط": "hypertension",
    "ضغط عالي": "hypertension",
    "ارتفاع ضغط الدم": "hypertension",
    "chronic kidney disease": "chronic_kidney_disease",
    "ckd": "chronic_kidney_disease",
    "renal impairment": "chronic_kidney_disease",
    "renal failure": "chronic_kidney_disease",
    "kidney failure": "chronic_kidney_disease",
    "فشل كلوي": "chronic_kidney_disease",
    "كلى": "chronic_kidney_disease",
    "قصور كلوي": "chronic_kidney_disease",
    "asthma": "asthma",
    "bronchial asthma": "asthma",
    "ربو": "asthma",
    "حساسية صدر": "asthma",
    "حساسية على الصدر": "asthma",
    "peptic ulcer": "peptic_ulcer_disease",
    "peptic ulcer disease": "peptic_ulcer_disease",
    "stomach ulcer": "peptic_ulcer_disease",
    "gastric ulcer": "peptic_ulcer_disease",
    "قرحة معدة": "peptic_ulcer_disease",
    "قرحة في المعدة": "peptic_ulcer_disease",
    "قرحة": "peptic_ulcer_disease",
    "hepatic impairment": "hepatic_impairment",
    "liver cirrhosis": "hepatic_impairment",
    "liver failure": "hepatic_impairment",
    "كبد": "hepatic_impairment",
    "تليف كبد": "hepatic_impairment",
    "قصور كبدي": "hepatic_impairment",
    "heart failure": "heart_failure",
    "chf": "heart_failure",
    "فشل عضلة القلب": "heart_failure",
    "ضعف عضلة القلب": "heart_failure",
    "bleeding disorder": "bleeding_disorder",
    "hemophilia": "bleeding_disorder",
    "سيولة": "bleeding_disorder",
    "سيولة في الدم": "bleeding_disorder"
}

def normalize_text(text: str) -> str:
    """Cleans punctuation, Arabic diacritics, and normalizes letters."""
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", t)
    t = re.sub(r"[إأآا]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"ى", "ي", t)
    t = re.sub(r"[؟?!.,;:\"'()\\[\\]{}]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

KNOWN_GENERIC_NAMES = [
    "metformin", "amoxicillin", "ampicillin", "ibuprofen", "paracetamol", "diclofenac",
    "salbutamol", "budesonide", "fluticasone", "tiotropium", "warfarin", "methotrexate",
    "aspirin", "acetylsalicylic acid", "sildenafil", "clopidogrel", "atorvastatin",
    "simvastatin", "rosuvastatin", "propranolol", "pseudoephedrine", "omeprazole",
    "pantoprazole", "esomeprazole", "enoxaparin", "captopril", "lisinopril", "losartan",
    "valsartan", "bisoprolol", "dexamethasone", "prednisolone", "hydrocortisone",
    "ciprofloxacin", "levofloxacin", "azithromycin", "clarithromycin", "insulin"
]

def normalize_medication_name(med: str) -> Tuple[str, Optional[str]]:
    """
    Resolves medication name to canonical generic name and brand name if detected.
    Returns: (canonical_generic, detected_brand)
    """
    if not med:
        return ("", None)

    norm = normalize_text(med)

    # Clean common frequency & formulation noise
    noise_patterns = [
        r"\b(?:يوميا|يومياً|كل\s+يوم|مرتين|ثلاث\s+مرات|قرص|كبسولة|شريط|حقنة|امبول|daily|once\s+daily|twice\s+daily|tablet|capsule|ampoule)\b"
    ]
    for np in noise_patterns:
        norm = re.sub(np, "", norm).strip()

    # Check Arabic aliases
    for ar_k, gen_v in ARABIC_MED_ALIASES.items():
        if normalize_text(ar_k) in norm:
            return (gen_v, ar_k)

    # Check English brands
    for brand_k, gen_v in BRAND_TO_GENERIC.items():
        if brand_k in norm:
            return (gen_v, brand_k.capitalize())

    # Check known generic names
    for gen in KNOWN_GENERIC_NAMES:
        if gen in norm:
            return (gen, None)

    # Fallback to cleaned normalized input text
    return (norm, None)

def normalize_condition_name(cond: str) -> str:
    """Normalizes medical condition string to standard clinical term."""
    if not cond:
        return ""
    norm = normalize_text(cond)
    for k, v in CONDITION_NORMALIZATION.items():
        if normalize_text(k) in norm or norm in normalize_text(k):
            return v
    return norm.replace(" ", "_")

def normalize_allergen_name(allergen: str) -> Tuple[str, str]:
    """
    Normalizes allergen text and identifies if it belongs to a known allergen class.
    Returns: (canonical_allergen, allergen_class)
    """
    if not allergen:
        return ("", "")
    norm = normalize_text(allergen)

    # Check if matches penicillin
    if any(p in norm for p in ["penicillin", "بنسلين", "بنسيلين"]):
        return ("penicillin", "penicillins")
    if any(p in norm for p in ["sulfa", "سلفا"]):
        return ("sulfonamides", "sulfonamides")
    if any(p in norm for p in ["nsaid", "مسكنات", "بروفين", "فولتارين", "اسبرين"]):
        return ("nsaids", "nsaids")
    if any(p in norm for p in ["cephalosporin", "سيفالوسبورين"]):
        return ("cephalosporins", "cephalosporins")

    return (norm, norm)
