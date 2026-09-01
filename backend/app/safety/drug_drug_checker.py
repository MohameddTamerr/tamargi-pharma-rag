from typing import List, Optional, Dict, Any
from .models import SafetyCheckItem, SafetyStatus, EvidenceCitation, PatientMedication
from .normalizer import normalize_medication_name
from .repository import get_verified_rules

def check_drug_drug(
    medication: str,
    patient_medications: List[PatientMedication]
) -> List[SafetyCheckItem]:
    """
    Deterministic drug-drug interaction checker querying verified safety rules
    from the structured knowledge store.
    """
    findings: List[SafetyCheckItem] = []
    if not medication or not patient_medications:
        return findings

    req_gen, _ = normalize_medication_name(medication)

    # Fetch verified DDI rules for the requested drug
    verified_rules = get_verified_rules(rule_type="drug_drug", drug_a=req_gen)
    if not verified_rules:
        return findings

    for p_med in patient_medications:
        if not p_med.active:
            continue

        p_gen, _ = normalize_medication_name(p_med.generic_name)

        for rule in verified_rules:
            r_a = normalize_medication_name(rule.drug_a)[0]
            r_b = normalize_medication_name(rule.drug_b or "")[0] if rule.drug_b else ""

            match_pair = (
                (r_a == req_gen and r_b == p_gen) or
                (r_a == p_gen and r_b == req_gen)
            )

            if match_pair:
                findings.append(SafetyCheckItem(
                    type="drug_drug",
                    status=rule.status,
                    medication=medication,
                    patient_factor=f"Concurrent Medication: {p_med.generic_name.capitalize()}",
                    reason=rule.reason or f"Documented drug-drug interaction between {medication} and {p_med.generic_name}.",
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

def get_relevant_medications_for_interaction(medication: str) -> List[str]:
    """Returns list of drug names that have verified interaction rules with requested drug."""
    req_gen, _ = normalize_medication_name(medication)
    verified_rules = get_verified_rules(rule_type="drug_drug", drug_a=req_gen)
    relevant: List[str] = []
    for rule in verified_rules:
        r_a = normalize_medication_name(rule.drug_a)[0]
        r_b = normalize_medication_name(rule.drug_b or "")[0] if rule.drug_b else ""
        if r_a and r_a != req_gen:
            relevant.append(r_a)
        if r_b and r_b != req_gen:
            relevant.append(r_b)
    return list(set(relevant))
