import re
from typing import Tuple, List, Optional, Dict, Any

def extract_strength_and_form(raw_line: str) -> Tuple[str, str, Optional[str]]:
    """
    Separates a raw dosage form line into:
    (form_text, cleaned_raw_line, extracted_strength)
    
    Example:
    "Oral syrup: 10 mg/5mL" -> ("Oral syrup", "Oral syrup: 10 mg/5mL", "10 mg/5mL")
    "Tablets: 10 mg, 20 mg" -> ("Tablets", "Tablets: 10 mg, 20 mg", "10 mg, 20 mg")
    """
    clean_line = raw_line.strip().rstrip(".,; ")
    
    # Check if there is a colon ':' or dash '-' separating form from strength
    if ":" in clean_line:
        parts = clean_line.split(":", 1)
        form_part = parts[0].strip()
        strength_part = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        return form_part, clean_line, strength_part
    
    # Look for common strength patterns (e.g. 50mg, 10 mg/5ml, 2 gm/100g, 0.5%)
    strength_match = re.search(r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|gm|ml|mL|IU|units|%|mmol)(?:[/\s\d\w.,%-]*))", clean_line, re.IGNORECASE)
    if strength_match and strength_match.start() > 3:
        form_part = clean_line[:strength_match.start()].strip().rstrip(":, -")
        strength_part = clean_line[strength_match.start():].strip()
        return form_part, clean_line, strength_part

    return clean_line, clean_line, None

def normalize_dosage_form(raw_form_text: str) -> str:
    """
    Normalizes raw dosage form text into a canonical standard taxonomy token.
    """
    t = raw_form_text.lower().strip()
    t = re.sub(r"[.,:;()\\[\\]{}]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # Specific tablet forms
    if "chewable" in t:
        return "chewable_tablet"
    if "oro-dispersible" in t or "orodispersible" in t or "dispersible" in t or "sublingual" in t or "mouth dissolving" in t:
        return "orodispersible_tablet"
    if "effervescent" in t:
        return "effervescent_granules" if "granule" in t or "sachet" in t else "effervescent_tablet"
    if "film-coated" in t or "sugar-coated" in t or "coated tablet" in t:
        return "tablet"
    if "extended-release tablet" in t or "sustained-release tablet" in t or "modified-release tablet" in t:
        return "extended_release_tablet"
    if "tablet" in t or "tab" in t:
        return "tablet"

    # Capsules
    if "soft gelatin" in t or "soft capsule" in t or "softgel" in t:
        return "soft_capsule"
    if "capsule" in t or "cap" in t:
        return "capsule"

    # Oral liquids
    if "suspension" in t:
        return "oral_suspension"
    if "syrup" in t:
        return "oral_syrup"
    if "drop" in t and ("oral" in t or "pediatric" in t or "infant" in t):
        return "oral_drops"
    if "emulsion" in t:
        return "oral_emulsion"
    if "oral solution" in t or "elixir" in t:
        return "oral_solution"

    # Inhalation
    if "inhalation powder" in t or "dry powder" in t or "powder for inhalation" in t or "dpi" in t:
        return "inhalation_powder"
    if "metered-dose" in t or "metered dose" in t or "aerosol" in t or "pmdi" in t or "inhalation aerosol" in t:
        return "inhalation_aerosol"
    if "nebul" in t or "solution for inhalation" in t or "inhalation solution" in t:
        return "nebulizer_solution"
    if "inhal" in t:
        return "inhalation"

    # Injectables & Infusions
    if "iv infusion" in t or "infusion" in t:
        return "iv_infusion"
    if "injection" in t or "inj" in t or "vial" in t or "ampoule" in t or "powder for injection" in t:
        return "injection"

    # Ophthalmic & Otic
    if "eye drop" in t or "ophthalmic drop" in t or "ophthalmic solution" in t:
        return "eye_drops"
    if "eye ointment" in t or "ophthalmic ointment" in t:
        return "eye_ointment"
    if "ear drop" in t or "otic drop" in t or "otic solution" in t:
        return "ear_drops"

    # Nasal
    if "nasal spray" in t or "nasal pump" in t:
        return "nasal_spray"
    if "nasal drop" in t:
        return "nasal_drops"

    # Topical & Transdermal
    if "patch" in t or "transdermal" in t:
        return "transdermal_patch"
    if "topical spray" in t or "spray" in t:
        return "topical_spray"
    if "cream" in t:
        return "cream"
    if "ointment" in t:
        return "ointment"
    if "gel" in t:
        return "gel"
    if "lotion" in t:
        return "lotion"

    # Rectal & Vaginal
    if "suppository" in t or "suppositories" in t:
        return "suppository"
    if "pessary" in t or "vaginal" in t:
        return "vaginal_suppository"

    # Powders & Granules
    if "granule" in t:
        return "granules"
    if "powder" in t:
        return "powder"

    # Fallback clean token
    cleaned = re.sub(r"[^\w\d]+", "_", t).strip("_")
    return cleaned if cleaned else "unspecified"

def normalize_route(raw_route: str) -> Tuple[str, List[str]]:
    """
    Extracts and standardizes routes of administration.
    Returns: (cleaned_raw_string, list_of_normalized_routes)
    """
    if not raw_route:
        return "Unspecified", []

    raw_clean = raw_route.strip().rstrip(".,; ")
    routes_found = []

    route_map = [
        ("Oral", [r"\boral\b", r"\bpo\b", r"\bby mouth\b"]),
        ("IV", [r"\biv\b", r"\bintravenous\b"]),
        ("IM", [r"\bim\b", r"\bintramuscular\b"]),
        ("SC", [r"\bsc\b", r"\bsubcutaneous\b", r"\bsubcut\b"]),
        ("Topical", [r"\btopical\b", r"\bcutaneous\b", r"\bdermal\b", r"\bskin\b"]),
        ("Inhalation", [r"\binhalation\b", r"\binhale\b", r"\brespiratory\b"]),
        ("Ophthalmic", [r"\bophthalmic\b", r"\beye\b", r"\bocular\b"]),
        ("Otic", [r"\botic\b", r"\bear\b", r"\baural\b"]),
        ("Nasal", [r"\bnasal\b", r"\bnose\b"]),
        ("Rectal", [r"\brectal\b", r"\brectum\b", r"\bper rectum\b"]),
        ("Vaginal", [r"\bvaginal\b", r"\bvagina\b"]),
        ("Intrathecal", [r"\bintrathecal\b"]),
        ("Epidural", [r"\bepidural\b"]),
        ("Intra-articular", [r"\bintra-articular\b", r"\bintraarticular\b"])
    ]

    r_lower = raw_clean.lower()
    for standard_name, patterns in route_map:
        for p in patterns:
            if re.search(p, r_lower):
                if standard_name not in routes_found:
                    routes_found.append(standard_name)
                break

    # If no regex matched, split by comma/slash
    if not routes_found:
        chunks = re.split(r"[,/;\s]+", raw_clean)
        for c in chunks:
            if c.strip() and len(c.strip()) > 1:
                routes_found.append(c.strip().capitalize())

    return raw_clean, routes_found

def classify_video_relevance(norm_form: str, norm_routes: List[str], generic_name: str = "") -> Tuple[str, Optional[str]]:
    """
    Determines whether a dosage form is likely to benefit from an instructional video
    and derives the broad device category without guessing specific commercial models.
    
    Returns:
        (video_relevant: "true" | "false" | "needs_review", device_category: Optional[str])
    """
    g_lower = generic_name.lower()

    # 1. Nebulizers (Distinct from Inhalers!)
    if "nebul" in norm_form:
        return "needs_review", "nebulizer"

    # 2. Inhalers & Respiratory Delivery
    if "inhal" in norm_form or "Inhalation" in norm_routes:
        return "needs_review", "inhaler"

    # 3. Insulin / Diabetes Injections
    if "insulin" in g_lower:
        return "needs_review", "insulin_injection"

    # 4. Glucose Monitoring Sensors / CGMs
    if "sensor" in norm_form or "cgm" in norm_form or "glucose" in g_lower:
        return "needs_review", "glucose_monitoring"

    # 5. Ophthalmic Medications
    if "eye" in norm_form or "ophthalmic" in norm_form or "Ophthalmic" in norm_routes:
        return "needs_review", "ophthalmic"

    # 6. Otic / Ear Drops
    if "ear" in norm_form or "otic" in norm_form or "Otic" in norm_routes:
        return "needs_review", "otic"

    # 7. Nasal Sprays & Drops
    if "nasal" in norm_form or "Nasal" in norm_routes:
        return "needs_review", "nasal"

    # 8. Transdermal Patches
    if "patch" in norm_form or "transdermal" in norm_form:
        return "needs_review", "transdermal"

    # 9. Rectal / Suppositories
    if "suppository" in norm_form or "Rectal" in norm_routes or "Vaginal" in norm_routes:
        return "needs_review", "rectal"

    # 10. Oral Liquids / Drops / Suspensions
    if norm_form in ("oral_drops", "oral_suspension", "oral_syrup", "oral_emulsion"):
        return "needs_review", "oral_liquid"

    # 11. Injections (General IV / IM / SC)
    if "injection" in norm_form or "iv_infusion" in norm_form or any(r in ("IV", "IM", "SC") for r in norm_routes):
        return "needs_review", "injection"

    # 12. Standard Solid Oral Forms
    if norm_form in ("tablet", "capsule", "soft_capsule", "chewable_tablet", "orodispersible_tablet", "effervescent_tablet", "effervescent_granules", "powder", "granules"):
        return "false", "solid_oral"

    # Default fallback
    return "false", "other"

def classify_patient_self_use(
    norm_form: str,
    norm_routes: List[str],
    generic_name: str = "",
    admin_instructions: Optional[str] = None,
    raw_dosage_form: str = ""
) -> Dict[str, Any]:
    """
    Patient Self-Use Video Relevance Filtering.
    
    Evaluates whether a dosage form / route involves a practical technique that
    genuinely benefits from patient visual instructional videos.
    """
    g_lower = generic_name.lower().strip()
    raw_lower = raw_dosage_form.lower().strip()
    admin_lower = (admin_instructions or "").lower().strip()

    # -------------------------------------------------------------
    # 1. NEBULIZERS (Strictly Separate from Inhalers)
    # -------------------------------------------------------------
    if "nebul" in norm_form or "nebul" in raw_lower or "nebul" in admin_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "nebulizer",
            "device_category": "nebulizer",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Medical nebulizer chamber & compressor setup technique"
        }

    # -------------------------------------------------------------
    # 2. INHALATION DEVICES - SPECIFIC FORMS (DPI, pMDI)
    # -------------------------------------------------------------
    if norm_form == "inhalation_powder" or "dpi" in raw_lower or "dry powder" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "dpi_inhaler",
            "device_category": "inhaler",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "DPI breath-actuated inhalation device technique"
        }

    if norm_form == "inhalation_aerosol" or "metered-dose" in raw_lower or "metered dose" in raw_lower or "pmdi" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "pmdi_inhaler",
            "device_category": "inhaler",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "Pressurized metered-dose inhaler actuation & coordination technique"
        }

    # -------------------------------------------------------------
    # 3. OPHTHALMIC (Eye Drops & Eye Ointment)
    # -------------------------------------------------------------
    if norm_form == "eye_drops" or "eye drop" in raw_lower or "ophthalmic drop" in raw_lower or "ophthalmic solution" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "eye_drops",
            "device_category": "ophthalmic",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Eye drop instillation, conjunctival sac pouching, and tear-duct occlusion"
        }

    if norm_form == "eye_ointment" or "eye ointment" in raw_lower or "ophthalmic ointment" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "eye_ointment",
            "device_category": "ophthalmic",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Eye ointment ribbon application along the lower eyelid"
        }

    # -------------------------------------------------------------
    # 4. OTIC (Ear Drops)
    # -------------------------------------------------------------
    if norm_form in ("ear_drops", "ears_drops", "otic_drops") or "ear drop" in raw_lower or "otic drop" in raw_lower or "otic solution" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "ear_drops",
            "device_category": "otic",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Ear drop administration, ear canal positioning, and head-tilt hold"
        }

    # -------------------------------------------------------------
    # 5. NASAL (Nasal Sprays & Drops)
    # -------------------------------------------------------------
    if norm_form == "nasal_spray" or "nasal spray" in raw_lower or "nasal pump" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "nasal_spray",
            "device_category": "nasal",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Nasal spray pump priming, head tilt, and ipsilateral/contralateral spraying technique"
        }

    if norm_form == "nasal_drops" or "nasal drop" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "nasal_drops",
            "device_category": "nasal",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Nasal drops instillation posture (Mygind / Mecca position)"
        }

    # -------------------------------------------------------------
    # 6. RECTAL & VAGINAL (Suppositories)
    # -------------------------------------------------------------
    if norm_form in ("suppository", "vaginal_suppository") or "suppository" in raw_lower or "suppositories" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "suppository",
            "device_category": "rectal",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Suppository insertion, unwrapping, position, and retention"
        }

    # -------------------------------------------------------------
    # 7. TRANSDERMAL PATCHES
    # -------------------------------------------------------------
    if norm_form == "transdermal_patch" or "patch" in raw_lower or "transdermal" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "transdermal_patch",
            "device_category": "transdermal",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Transdermal patch skin preparation, adhesion, and rotation"
        }

    # -------------------------------------------------------------
    # 8. INSULIN & DIABETES SELF-INJECTION
    # -------------------------------------------------------------
    if "insulin" in g_lower or "insulin" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "insulin_pen",
            "device_category": "insulin_injection",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "Insulin injection pen dial, priming, and subcutaneous technique"
        }

    # -------------------------------------------------------------
    # 9. AUTO-INJECTORS & PATIENT SELF-INJECTION PENS
    # -------------------------------------------------------------
    if "epipen" in g_lower or "auto-injector" in raw_lower or "autoinjector" in raw_lower or "prefilled pen" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "self_injection",
            "device_category": "self_injection",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "Emergency or daily patient self-administered auto-injector device"
        }

    # -------------------------------------------------------------
    # 10. GLUCOSE MONITORING & SENSORS
    # -------------------------------------------------------------
    if "cgm" in norm_form or "sensor" in norm_form or "freestyle" in g_lower or "dexcom" in g_lower or "sensor" in raw_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "cgm",
            "device_category": "glucose_monitoring",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "Continuous glucose monitoring sensor application & scanner pairing"
        }

    if "glucometer" in norm_form or "glucose meter" in raw_lower or "blood glucose" in g_lower:
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "glucometer",
            "device_category": "glucose_monitoring",
            "device_specificity": "generic_technique",
            "exact_device_review_required": False,
            "classification_reason": "Blood glucometer lancing and test strip sampling technique"
        }

    # -------------------------------------------------------------
    # 11. INHALATION DEVICES - UNSPECIFIED
    # -------------------------------------------------------------
    if norm_form == "inhalation" or ("Inhalation" in norm_routes and norm_form not in ("tablet", "capsule", "soft_capsule", "cream", "ointment", "gel", "injection", "iv_infusion", "oral_syrup", "oral_suspension", "oral_solution")):
        return {
            "self_use_video_relevance": "yes",
            "technique_category": "inhaler_unspecified",
            "device_category": "inhaler",
            "device_specificity": "exact_device_required",
            "exact_device_review_required": True,
            "classification_reason": "Inhalation delivery system requiring exact device mapping"
        }

    # -------------------------------------------------------------
    # 12. INJECTIONS (Parenteral Filtering)
    # -------------------------------------------------------------
    if "injection" in norm_form or "iv_infusion" in norm_form or any(r in ("IV", "IM", "SC") for r in norm_routes) or "vial" in raw_lower or "ampoule" in raw_lower:
        if any(w in admin_lower or w in raw_lower for w in ["self-inject", "self inject", "prefilled pen", "auto-injector", "autoinjector", "subcutaneous pen"]):
            return {
                "self_use_video_relevance": "yes",
                "technique_category": "self_injection",
                "device_category": "self_injection",
                "device_specificity": "exact_device_required",
                "exact_device_review_required": True,
                "classification_reason": "Documented patient self-administered subcutaneous injection"
            }

        if "SC" in norm_routes and not any(r in ("IV", "IM") for r in norm_routes) and norm_form not in ("tablet", "capsule", "cream"):
            return {
                "self_use_video_relevance": "needs_review",
                "technique_category": "self_injection",
                "device_category": "self_injection",
                "device_specificity": "needs_review",
                "exact_device_review_required": False,
                "classification_reason": "Subcutaneous route requires clinical check for outpatient self-use"
            }

        return {
            "self_use_video_relevance": "no",
            "technique_category": "hospital_parenteral",
            "device_category": "hospital_parenteral",
            "device_specificity": "not_applicable",
            "exact_device_review_required": False,
            "classification_reason": "Hospital / healthcare professional parenteral administration (IV/IM)"
        }

    # -------------------------------------------------------------
    # 13. ORAL LIQUIDS (Syrups, Drops, Suspensions)
    # -------------------------------------------------------------
    if norm_form in ("oral_drops", "oral_suspension", "oral_syrup", "oral_solution", "oral_emulsion") or "syrup" in raw_lower or "suspension" in raw_lower:
        if any(w in admin_lower or w in raw_lower for w in ["dropper", "oral syringe", "measuring syringe", "reconstitut"]):
            return {
                "self_use_video_relevance": "needs_review",
                "technique_category": "oral_syringe",
                "device_category": "oral_liquid",
                "device_specificity": "needs_review",
                "exact_device_review_required": False,
                "classification_reason": "Oral liquid with special dosing syringe, dropper, or reconstitution"
            }

        return {
            "self_use_video_relevance": "no",
            "technique_category": "oral_suspension" if norm_form == "oral_suspension" else "none",
            "device_category": "oral_liquid",
            "device_specificity": "not_applicable",
            "exact_device_review_required": False,
            "classification_reason": "Standard swallowed oral liquid with routine dosing"
        }

    # -------------------------------------------------------------
    # 14. SOLID ORAL FORMS (Tablets, Capsules, Powders)
    # -------------------------------------------------------------
    if norm_form in ("tablet", "capsule", "soft_capsule", "chewable_tablet", "orodispersible_tablet", "effervescent_tablet", "effervescent_granules", "powder", "granules"):
        return {
            "self_use_video_relevance": "no",
            "technique_category": "solid_oral",
            "device_category": "solid_oral",
            "device_specificity": "not_applicable",
            "exact_device_review_required": False,
            "classification_reason": "Standard swallowed solid oral dosage form"
        }

    # -------------------------------------------------------------
    # 15. TOPICAL DERMATOLOGIC (Creams, Ointments, Gels, Sprays)
    # -------------------------------------------------------------
    if norm_form in ("cream", "ointment", "gel", "lotion", "topical_spray") or "topical" in raw_lower:
        return {
            "self_use_video_relevance": "no",
            "technique_category": "topical_application",
            "device_category": "other",
            "device_specificity": "not_applicable",
            "exact_device_review_required": False,
            "classification_reason": "Standard topical skin application"
        }

    # Default fallback
    return {
        "self_use_video_relevance": "no",
        "technique_category": "none",
        "device_category": "other",
        "device_specificity": "not_applicable",
        "exact_device_review_required": False,
        "classification_reason": "No specialized patient device or administration technique"
    }

