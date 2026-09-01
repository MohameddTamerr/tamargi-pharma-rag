"""
Arabic/Egyptian query expansion, intent detection, and drug entity extraction.

This module provides:
1. Drug entity extraction from Arabic/Egyptian queries (transliterated names)
2. Comparison intent detection ("what's the difference between X and Y")
3. Query decomposition for multi-drug comparisons
4. Expanded retrieval query construction

IMPORTANT: This module does NOT touch the embedding model, reranker, or BM25 index.
It only pre-processes the query string before it enters the existing pipeline.
"""
import re
from app.language.arabic import normalize_arabic

# ─────────────────────────────────────────────────────────────────────────────
# Drug name transliteration mappings
# Arabic transliterations → canonical English drug name (lowercase)
# ─────────────────────────────────────────────────────────────────────────────
ARABIC_DRUG_ALIASES: dict[str, str] = {
    # Paracetamol / Acetaminophen
    "باراسيتامول": "paracetamol",
    "باراسيتامو": "paracetamol",
    "بنادول": "paracetamol",
    "بندول": "paracetamol",
    "أسيتامينوفين": "acetaminophen",
    "اسيتامينوفين": "acetaminophen",
    "سيتامول": "paracetamol",
    "ادول": "paracetamol",
    "ادفيل": "ibuprofen",

    # Ibuprofen
    "إيبوبروفين": "ibuprofen",
    "ايبوبروفين": "ibuprofen",
    "ايبوبروفن": "ibuprofen",
    "إيبوبروفن": "ibuprofen",
    "ايبو": "ibuprofen",
    "نوروفين": "ibuprofen",
    "بروفين": "ibuprofen",

    # Amoxicillin
    "أموكسيسيلين": "amoxicillin",
    "اموكسيسيلين": "amoxicillin",
    "أموكسيل": "amoxicillin",
    "اموكسيل": "amoxicillin",

    # Metformin
    "ميتفورمين": "metformin",
    "جلوكوفاج": "metformin",
    "جلوكوفج": "metformin",

    # Omeprazole
    "أوميبرازول": "omeprazole",
    "اوميبرازول": "omeprazole",
    "لوسك": "omeprazole",

    # Aspirin
    "أسبرين": "aspirin",
    "اسبرين": "aspirin",

    # Atorvastatin
    "أتورفاستاتين": "atorvastatin",
    "اتورفاستاتين": "atorvastatin",
    "ليبيتور": "atorvastatin",

    # Amlodipine
    "أملوديبين": "amlodipine",
    "امولوديبين": "amlodipine",
    "نورفاسك": "amlodipine",

    # Losartan
    "لوسارتان": "losartan",
    "كوزار": "losartan",

    # Furosemide
    "فيوروسيميد": "furosemide",
    "فروسيميد": "furosemide",
    "لاسيكس": "furosemide",

    # Insulin
    "انسولين": "insulin",
    "أنسولين": "insulin",

    # Salbutamol / Albuterol
    "سالبيوتامول": "salbutamol",
    "البيوتيرول": "albuterol",
    "فنتولين": "salbutamol",

    # Codeine
    "كودين": "codeine",

    # Diclofenac
    "ديكلوفيناك": "diclofenac",

    # Tramadol
    "ترامادول": "tramadol",

    # Clindamycin
    "كليندامايسين": "clindamycin",

    # Dexamethasone
    "ديكساميثازون": "dexamethasone",
    "ديكساميثاسون": "dexamethasone",
    "دكساميثازون": "dexamethasone",

    # Ciprofloxacin
    "سيبروفلوكساسين": "ciprofloxacin",
    "سيبروفلوكساصين": "ciprofloxacin",

    # Azithromycin
    "أزيثرومايسين": "azithromycin",
    "ازيثرومايسين": "azithromycin",
    "زيثروماكس": "azithromycin",
}

# ─────────────────────────────────────────────────────────────────────────────
# Symptom-to-OTC indications mapping (Arabic/Egyptian)
# Maps common patient symptoms to approved Egyptian OTC formulary terms
# ─────────────────────────────────────────────────────────────────────────────
SYMPTOM_TO_OTC_TERMS: dict[str, str] = {
    # Cold / Flu / Fever / Respiratory
    "برد": "symptoms common colds and flu fever Brufen Cetafen Paracetamol Ibuprofen Panadol Cold Flu Stopadol OTC",
    "انفلونزا": "symptoms common colds and flu fever Paracetamol Ibuprofen Panadol Cold Flu OTC",
    "إنفلونزا": "symptoms common colds and flu fever Paracetamol Ibuprofen Panadol Cold Flu OTC",
    "زكام": "symptoms common colds and flu congestion fever Panadol Sinus Relief Stopadol OTC",
    "رشح": "symptoms common colds and flu Panadol Cold Flu Stopadol OTC",
    "سخونية": "fever antipyretic mild to moderate pain feverishness Brufen Paracetamol Ibuprofen Arkadolow Cetafen OTC",
    "حرارة": "fever antipyretic mild to moderate pain Brufen Paracetamol Ibuprofen Arkadolow OTC",

    # Pain / Headache / Dental / Musculoskeletal
    "صداع": "symptomatic relief of headache including migraine headache dental pain mild to moderate pain Brufen Flamotal Spididol Panadol Stopadol Extra Ibuprofen Paracetamol OTC",
    "وجع سنان": "toothache dental pain dental procedures mild to moderate pain Brufen Spididol Ibuprofen Paracetamol OTC",
    "الم اسنان": "toothache dental pain mild to moderate pain Brufen Spididol Ibuprofen Paracetamol OTC",
    "ألم أسنان": "toothache dental pain mild to moderate pain Brufen Spididol Ibuprofen Paracetamol OTC",
    "وجع ضهر": "backache muscular pain mild to moderate muscular pain Brufen Spididol Ibuprofen OTC",
    "الم عضلات": "muscular pain mild to moderate muscular pain Brufen Spididol Ibuprofen OTC",
    "الم الدورة": "dysmenorrhea primary dysmenorrhea menstrual pain Brufen Flamotal Spididol Ibuprofen Paracetamol OTC",
    "مغص الدورة": "dysmenorrhea primary dysmenorrhea menstrual pain Brufen Flamotal Spididol Ibuprofen OTC",

    # Heartburn / Acidity / Reflux / GERD
    "حموضة": "heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Healsec Controloc Pepzole Omez Gastrazole Protofix OTC",
    "حرقان في المعدة": "heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Healsec Controloc Pepzole Omez OTC",
    "حرقان بالمعدة": "heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Healsec Controloc Pepzole Omez OTC",
    "ارتجاع": "reflux symptoms heartburn acid regurgitation gastro-oesophageal reflux disease Omeprazole Pantoprazole Controloc Healsec OTC",
    "ارتجاع المريء": "gastro-oesophageal reflux disease heartburn acid regurgitation Omeprazole Pantoprazole Controloc Healsec Pepzole Omez OTC",
}

# ─────────────────────────────────────────────────────────────────────────────
# Comparison intent patterns (Arabic/Egyptian)
# ─────────────────────────────────────────────────────────────────────────────
COMPARISON_PATTERNS = [
    r"الفرق بين",
    r"الفرق ما بين",
    r"فرق بين",
    r"مقارنة بين",
    r"compare",
    r"difference[s]? between",
    r"differ[s]? from",
    r"vs\.?",
    r"versus",
    r"ايه الفرق",
    r"إيه الفرق",
    r"ايه الاختلاف",
    r"الاختلاف بين",
    r"افضل من",
    r"أفضل من",
    r"احسن من",
    r"أحسن من",
    r"بيختلف عن",
    r"يختلف عن",
]


def detect_comparison_intent(query: str) -> bool:
    """Returns True if the query is asking to compare two or more drugs."""
    q_lower = query.lower()
    for pattern in COMPARISON_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return True
    return False


def extract_drug_entities(query: str) -> list[str]:
    """
    Extracts drug names from Arabic/Egyptian queries.
    
    Tries Arabic alias map first, then extracts embedded English drug names.
    Returns a list of canonical English drug names found in the query.
    """
    found: list[str] = []
    
    # Normalize Arabic for alias matching
    q_normalized = normalize_arabic(query)
    
    # 1. Check Arabic alias map (case-insensitive, after Arabic normalization)
    for arabic_name, english_name in ARABIC_DRUG_ALIASES.items():
        alias_norm = normalize_arabic(arabic_name)
        if alias_norm in q_normalized:
            if english_name not in found:
                found.append(english_name)

    # 2. Extract any embedded English drug names (already in query)
    english_words = re.findall(r'[A-Za-z][a-zA-Z0-9\-]{2,}', query)
    for word in english_words:
        word_lower = word.lower()
        if word_lower not in found:
            found.append(word_lower)
    
    return found


def build_expansion_query(
    original_query: str,
    drug_entities: list[str],
    is_comparison: bool
) -> str:
    """
    Constructs an expanded, retrieval-optimized query string.
    
    For comparison queries with 2+ drugs, the expansion includes:
    - The original (Arabic) query for dense retrieval context
    - Each drug name individually (for BM25 term matching)
    - Key medical comparison terms
    
    This does NOT decompose into separate sub-queries. It enriches the
    single retrieval query with extra terms the model can match against.
    """
    parts = [original_query]
    
    if drug_entities:
        # Add individual drug names so BM25 can match their passages
        parts.extend(drug_entities)
    
    if is_comparison and len(drug_entities) >= 2:
        # Only add comparison terms if not already present (avoid duplication
        # when the Egyptian normalizer has already added them)
        already_has_comparison = (
            "comparison" in original_query.lower() or
            "difference" in original_query.lower() or
            "مقارنة" in original_query
        )
        if not already_has_comparison:
            parts.append("comparison difference mechanism action indications side effects")
            parts.append("مقارنة الفرق آلية العمل الأعراض الجانبية الاستخدامات")
    
    return " ".join(parts).strip()


def extract_symptom_terms(query: str) -> list[str]:
    """
    Extracts OTC indication search terms for patient symptoms mentioned in the query.
    """
    q_norm = normalize_arabic(query)
    found_terms: list[str] = []
    for symptom, terms in SYMPTOM_TO_OTC_TERMS.items():
        symptom_norm = normalize_arabic(symptom)
        if symptom_norm in q_norm:
            found_terms.append(terms)
    return found_terms


def expand_arabic_query(original_query: str) -> str:
    """
    Main entry point. Takes any Arabic/Egyptian query and returns
    an enriched retrieval query string.
    
    Expands:
    1. Arabic drug aliases (brand / generic transliterations)
    2. Comparison intents (differences between drugs)
    3. Patient symptom queries -> Egyptian OTC indications
    """
    drug_entities = extract_drug_entities(original_query)
    is_comparison = detect_comparison_intent(original_query)
    symptom_terms = extract_symptom_terms(original_query)
    
    if not drug_entities and not is_comparison and not symptom_terms:
        # Nothing to expand — pass through unchanged
        return original_query
    
    parts = [original_query]
    if drug_entities:
        parts.extend(drug_entities)
    if symptom_terms:
        parts.extend(symptom_terms)
        parts.append("OTC approved indication dosage form")
    if is_comparison and len(drug_entities) >= 2:
        already_has_comparison = (
            "comparison" in original_query.lower() or
            "difference" in original_query.lower() or
            "مقارنة" in original_query
        )
        if not already_has_comparison:
            parts.append("comparison difference mechanism action indications side effects")
            parts.append("مقارنة الفرق آلية العمل الأعراض الجانبية الاستخدامات")
            
    return " ".join(parts).strip()
