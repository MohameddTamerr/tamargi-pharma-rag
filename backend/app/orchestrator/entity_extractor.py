from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from app.normalization.text_normalizer import normalize_arabic_text
from app.normalization.medication_resolver import extract_all_medications, extract_strength, extract_dosage_form
from app.normalization.condition_normalizer import extract_conditions
from app.normalization.symptom_normalizer import extract_symptoms
from app.normalization.device_normalizer import resolve_device
from app.safety.normalizer import normalize_allergen_name

class ExtractedEntities(BaseModel):
    medications: List[str] = Field(default_factory=list) # Normalized generic names
    raw_medication_terms: List[str] = Field(default_factory=list) # User verbatim terms
    dosage_forms: List[str] = Field(default_factory=list)
    devices: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)

def extract_entities(query_text: str) -> ExtractedEntities:
    """
    Extracts structured healthcare entities from user query without fabricating diagnoses.
    """
    clean_q = normalize_arabic_text(query_text)
    
    # 1. Medications & Brands
    med_res = extract_all_medications(query_text)
    extracted_meds = [m.canonical_generic for m in med_res if m.canonical_generic]
    raw_terms = [m.raw_term for m in med_res if m.raw_term]

    # 2. Symptoms (Strictly preserved as symptoms, never inferred as chronic conditions)
    extracted_symptoms = extract_symptoms(query_text)

    # 3. Conditions
    extracted_conditions = extract_conditions(query_text)

    # 4. Allergies
    extracted_allergies: List[str] = []
    for alg_term in ["penicillin", "بنسلين", "بنسيلين", "sulfa", "سلفا", "nsaids", "مسكنات", "cephalosporin", "سيفالوسبورين"]:
        if normalize_arabic_text(alg_term) in clean_q:
            norm_alg, _ = normalize_allergen_name(alg_term)
            if norm_alg and norm_alg not in extracted_allergies:
                extracted_allergies.append(norm_alg)

    # 5. Delivery Devices
    extracted_devices: List[str] = []
    dev_res = resolve_device(query_text)
    if dev_res:
        extracted_devices.append(dev_res[0])

    # 6. Dosage Forms
    extracted_forms: List[str] = []
    form = extract_dosage_form(query_text)
    if form:
        extracted_forms.append(form)

    # 7. Strengths
    extracted_strengths: List[str] = []
    strength = extract_strength(query_text)
    if strength:
        extracted_strengths.append(strength)

    return ExtractedEntities(
        medications=extracted_meds,
        raw_medication_terms=raw_terms,
        dosage_forms=extracted_forms,
        devices=extracted_devices,
        symptoms=extracted_symptoms,
        conditions=extracted_conditions,
        allergies=extracted_allergies,
        strengths=extracted_strengths
    )
