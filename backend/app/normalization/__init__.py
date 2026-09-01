"""
Arabic and Egyptian Medication Resolution Package for Tamargi.ai
"""

from .text_normalizer import normalize_arabic_text, normalize_medical_query, levenshtein_distance
from .medication_resolver import (
    MedicationResolutionResult,
    resolve_medication,
    extract_all_medications,
    extract_strength,
    extract_dosage_form
)
from .condition_normalizer import normalize_condition_name, CONDITION_ALIASES
from .symptom_normalizer import extract_symptoms, SYMPTOM_ALIASES
from .device_normalizer import resolve_device, is_ambiguous_device, DEVICE_ALIASES
from .query_translator import build_canonical_retrieval_query
