import os
import re
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set, Any
from pydantic import BaseModel, Field

from .text_normalizer import normalize_arabic_text, levenshtein_distance

class MedicationResolutionResult(BaseModel):
    canonical_generic: str
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    is_ambiguous: bool = False
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    confidence: float = 1.0
    raw_term: str

from app.config import PROCESSED_DIR, ALIASES_FILE, BASE_DIR

# In-Memory Cache for verified aliases
ALIAS_TABLE: List[Dict[str, Any]] = []

def load_alias_dataset():
    """Loads the verified medication aliases dataset."""
    global ALIAS_TABLE
    candidate_paths = [
        ALIASES_FILE,
        PROCESSED_DIR / "medication_aliases.csv",
        BASE_DIR / "data" / "processed" / "medication_aliases.csv",
        BASE_DIR.parent / "data" / "processed" / "medication_aliases.csv",
    ]
    csv_path = None
    for p in candidate_paths:
        if p and Path(p).exists():
            csv_path = Path(p).resolve()
            break

    if csv_path and csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            ALIAS_TABLE = df[df["active"] == True].to_dict(orient="records")
            print(f"[MedicationResolver] Loaded {len(ALIAS_TABLE)} active aliases from {csv_path.name}")
        except Exception as e:
            print(f"[MedicationResolver Warning] Could not load aliases CSV: {e}")
            ALIAS_TABLE = []
    else:
        print("[MedicationResolver Warning] medication_aliases.csv not found.")
        ALIAS_TABLE = []

# Known Dosage Forms Map
DOSAGE_FORMS: Dict[str, str] = {
    "قرص": "tablet",
    "اقراص": "tablet",
    "أقراص": "tablet",
    "حبوب": "tablet",
    "حبة": "tablet",
    "كبسول": "capsule",
    "كبسولة": "capsule",
    "كبسولات": "capsule",
    "شراب": "syrup",
    "محلول": "solution",
    "نقط": "drops",
    "قطرة": "drops",
    "قطره": "drops",
    "حقنة": "injection",
    "حقن": "injection",
    "امبول": "ampoule",
    "أمبول": "ampoule",
    "فيال": "vial",
    "مرهم": "ointment",
    "كريم": "cream",
    "جل": "gel",
    "لبوس": "suppository",
    "تحاميل": "suppository",
    "فوار": "effervescent",
    "بودرة": "powder",
    "بخاخ": "inhaler/spray",
    "بخاخة": "inhaler/spray",
    "tablet": "tablet",
    "tablets": "tablet",
    "capsule": "capsule",
    "capsules": "capsule",
    "syrup": "syrup",
    "solution": "solution",
    "drops": "drops",
    "injection": "injection",
    "ampoule": "ampoule",
    "vial": "vial",
    "ointment": "ointment",
    "cream": "cream",
    "gel": "gel",
    "suppository": "suppository",
    "spray": "spray",
    "inhaler": "inhaler"
}

def extract_strength(text: str) -> Optional[str]:
    """Extracts pharmaceutical strength from text (e.g. 400 mg, 500 ملجم, or 400)."""
    if not text:
        return None
    # 1. Check for explicit units first (e.g., 400 mg, 500 ملجم, 1 جم, 100 مل)
    pattern_with_unit = r"(\b\d+(?:\.\d+)?\s*(?:mg|gm|mcg|ml|iu|ملجم|مجم|جم|مل|وحدة|وحده)\b|\b\d+(?:\.\d+)?\s*(?=%))"
    match = re.search(pattern_with_unit, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 2. Check for standalone pharmaceutical dosage numbers (e.g., "Brufen 400", "Panadol 500", "Concor 5")
    pattern_num = r"\b(?:[a-zA-Z\u0600-\u06FF]+)\s+(\d+(?:\.\d+)?)\b"
    match_num = re.search(pattern_num, text)
    if match_num:
        val = match_num.group(1).strip()
        # Avoid treating years or small query words as strength
        if len(val) <= 4:
            return val
            
    return None

def extract_dosage_form(text: str) -> Optional[str]:
    """Extracts pharmaceutical dosage form from text."""
    if not text:
        return None
    clean = normalize_arabic_text(text)
    words = clean.split()
    for w in words:
        if w in DOSAGE_FORMS:
            return DOSAGE_FORMS[w]
    return None

def resolve_medication(term: str) -> Optional[MedicationResolutionResult]:
    """
    Resolves a single medication or brand name to its canonical generic active ingredient.
    Employs exact matching first, followed by conservative typo tolerance.
    """
    if not term:
        return None

    if not ALIAS_TABLE:
        load_alias_dataset()

    clean_term = normalize_arabic_text(term)
    strength = extract_strength(term)
    form = extract_dosage_form(term)

    # 1. Exact / Normalized Alias Match
    for row in ALIAS_TABLE:
        alias_norm = normalize_arabic_text(str(row.get("alias", "")))
        if alias_norm == clean_term:
            return MedicationResolutionResult(
                canonical_generic=row["canonical_generic_name"],
                brand_name=row.get("brand_name") if pd.notna(row.get("brand_name")) else None,
                strength=strength,
                dosage_form=form,
                confidence=1.0,
                raw_term=term
            )

    # 2. Substring / Word Match against verified alias table
    for row in ALIAS_TABLE:
        alias_norm = normalize_arabic_text(str(row.get("alias", "")))
        if len(alias_norm) >= 3 and alias_norm in clean_term:
            return MedicationResolutionResult(
                canonical_generic=row["canonical_generic_name"],
                brand_name=row.get("brand_name") if pd.notna(row.get("brand_name")) else None,
                strength=strength,
                dosage_form=form,
                confidence=0.95,
                raw_term=term
            )

    # 3. Conservative Typo Tolerance (Levenshtein distance <= 1 on long words >= 5)
    clean_words = clean_term.split()
    for w in clean_words:
        if len(w) >= 5:
            for row in ALIAS_TABLE:
                alias_norm = normalize_arabic_text(str(row.get("alias", "")))
                if len(alias_norm) >= 5:
                    dist = levenshtein_distance(w, alias_norm)
                    if dist <= 1:
                        return MedicationResolutionResult(
                            canonical_generic=row["canonical_generic_name"],
                            brand_name=row.get("brand_name") if pd.notna(row.get("brand_name")) else None,
                            strength=strength,
                            dosage_form=form,
                            confidence=0.85,
                            raw_term=term
                        )

    return None

def extract_all_medications(query_text: str) -> List[MedicationResolutionResult]:
    """
    Extracts all distinct verified medication entities from a user query text.
    Preserves original mentions, strengths, and dosage forms.
    """
    if not ALIAS_TABLE:
        load_alias_dataset()

    clean_query = normalize_arabic_text(query_text)
    strength = extract_strength(query_text)
    form = extract_dosage_form(query_text)

    found_generics: Set[str] = set()
    results: List[MedicationResolutionResult] = []

    # Sort aliases by length descending to match specific multi-word brands first
    sorted_aliases = sorted(
        ALIAS_TABLE,
        key=lambda r: len(normalize_arabic_text(str(r.get("alias", "")))),
        reverse=True
    )

    for row in sorted_aliases:
        alias_norm = normalize_arabic_text(str(row.get("alias", "")))
        gen = row["canonical_generic_name"]
        
        if len(alias_norm) >= 3 and alias_norm in clean_query:
            if gen not in found_generics:
                found_generics.add(gen)
                results.append(MedicationResolutionResult(
                    canonical_generic=gen,
                    brand_name=row.get("brand_name") if pd.notna(row.get("brand_name")) else None,
                    strength=strength,
                    dosage_form=form,
                    confidence=1.0,
                    raw_term=alias_norm
                ))

    return results

# Initialize alias dataset on module load
load_alias_dataset()
