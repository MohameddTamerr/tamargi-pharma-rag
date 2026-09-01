from typing import List, Optional, Dict, Any
from .models import SafetyCheckItem, SafetyStatus, EvidenceCitation, PatientCondition
from .normalizer import normalize_medication_name, normalize_condition_name
from .repository import get_verified_rules

def check_drug_disease(
    medication: str,
    patient_conditions: List[PatientCondition]
) -> List[SafetyCheckItem]:
    """
    Deterministic drug-disease safety checker verifying active patient conditions
    against verified safety rules in the knowledge repository.
    """
    findings: List[SafetyCheckItem] = []
    if not medication or not patient_conditions:
        return findings

    gen_name, _ = normalize_medication_name(medication)

    # Fetch verified drug-disease rules for this medication
    verified_rules = get_verified_rules(rule_type="drug_disease", drug_a=gen_name)
    if not verified_rules:
        return findings

    for cond in patient_conditions:
        if not cond.active:
            continue

        norm_c = cond.normalized_condition or normalize_condition_name(cond.condition_name)

        for rule in verified_rules:
            rule_c = normalize_condition_name(rule.condition_name or "")
            if rule_c == norm_c or norm_c in rule_c or rule_c in norm_c:
                findings.append(SafetyCheckItem(
                    type="drug_disease",
                    status=rule.status,
                    medication=medication,
                    patient_factor=cond.condition_name,
                    reason=rule.reason or f"Contraindication/warning with {cond.condition_name}.",
                    evidence_ids=[str(rule.id)],
                    evidence=[EvidenceCitation(
                        rule_id=str(rule.id),
                        source=rule.source_file,
                        page=rule.source_page,
                        section=rule.source_section,
                        excerpt=rule.evidence_excerpt
                    )]
                ))

    return findings

def get_relevant_conditions_for_medication(medication: str) -> List[str]:
    """Returns condition names that have verified safety rules for the given medication."""
    gen_name, _ = normalize_medication_name(medication)
    verified_rules = get_verified_rules(rule_type="drug_disease", drug_a=gen_name)
    relevant: List[str] = []
    for rule in verified_rules:
        if rule.condition_name:
            norm_c = normalize_condition_name(rule.condition_name)
            if norm_c not in relevant:
                relevant.append(norm_c)
    return relevant
