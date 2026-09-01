from typing import List, Optional
from .models import SafetyCheckItem, SafetyStatus, EvidenceCitation, PatientAllergy
from .normalizer import normalize_medication_name, normalize_allergen_name, ALLERGEN_CLASS_MAP
from .repository import get_verified_rules

def check_allergy(
    medication: str,
    patient_allergies: List[PatientAllergy]
) -> List[SafetyCheckItem]:
    """
    Deterministic allergy checker verifying drug classes and cross-reactivities
    against verified safety rules in the knowledge store.
    """
    findings: List[SafetyCheckItem] = []
    if not medication or not patient_allergies:
        return findings

    gen_name, _ = normalize_medication_name(medication)

    # Fetch verified allergy rules for this medication
    verified_rules = get_verified_rules(rule_type="allergy", drug_a=gen_name)

    for allergy in patient_allergies:
        if not allergy.active:
            continue

        can_allergen, a_class = normalize_allergen_name(allergy.allergen)

        matched_rule = None
        for r in verified_rules:
            r_allg = (r.allergen_class or r.condition_name or "").lower()
            if (can_allergen and can_allergen.lower() in r_allg) or (a_class and a_class.lower() in r_allg) or (can_allergen.lower() == r.drug_a.lower()):
                matched_rule = r
                break

        if matched_rule:
            findings.append(SafetyCheckItem(
                type="allergy",
                status=matched_rule.status,
                medication=medication,
                patient_factor=f"Allergy to {allergy.allergen}",
                reason=matched_rule.reason or f"Patient has a documented hypersensitivity to {allergy.allergen}.",
                evidence_ids=[str(matched_rule.id)],
                evidence=[EvidenceCitation(
                    rule_id=str(matched_rule.id),
                    source=matched_rule.source_file,
                    page=matched_rule.source_page,
                    section=matched_rule.source_section,
                    excerpt=matched_rule.evidence_excerpt
                )]
            ))
            continue

        # 2. Direct ingredient exact string match (without fake page citation if unseeded)
        if can_allergen == gen_name or allergy.allergen.lower() == gen_name.lower():
            # If an exact ingredient match occurs, check if a verified rule exists
            direct_rules = [r for r in verified_rules if r.drug_a.lower() == gen_name.lower()]
            if direct_rules:
                dr = direct_rules[0]
                findings.append(SafetyCheckItem(
                    type="allergy",
                    status=dr.status,
                    medication=medication,
                    patient_factor=f"Direct Ingredient Allergy: {allergy.allergen}",
                    reason=dr.reason or f"Direct ingredient match for allergy: {allergy.allergen}.",
                    evidence_ids=[str(dr.id)],
                    evidence=[EvidenceCitation(
                        rule_id=str(dr.id),
                        source=dr.source_file,
                        page=dr.source_page,
                        section=dr.source_section,
                        excerpt=dr.evidence_excerpt
                    )]
                ))

    return findings
