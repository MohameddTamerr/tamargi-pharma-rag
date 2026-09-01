from typing import Optional, List
from .models import SafetyCheckItem, SafetyStatus, EvidenceCitation
from .normalizer import normalize_medication_name
from .repository import get_verified_rules

def check_high_alert(medication: str) -> Optional[SafetyCheckItem]:
    """
    Checks if a medication is identified as High-Alert in verified EDA guidelines.
    """
    if not medication:
        return None

    gen_name, _ = normalize_medication_name(medication)

    # Query verified rules for high_alert category
    verified_rules = get_verified_rules(rule_type="high_alert", drug_a=gen_name)
    if not verified_rules:
        return None

    matched_rule = verified_rules[0]

    return SafetyCheckItem(
        type="high_alert",
        status=matched_rule.status,
        medication=medication,
        patient_factor=f"High-Alert Category: {matched_rule.dosage_form or matched_rule.condition_name or 'High-Alert Medication'}",
        reason=matched_rule.reason or "High-alert medication: requires independent double-checking and administration safeguards.",
        evidence_ids=[str(matched_rule.id)],
        evidence=[EvidenceCitation(
            rule_id=str(matched_rule.id),
            source=matched_rule.source_file,
            page=matched_rule.source_page,
            section=matched_rule.source_section,
            excerpt=matched_rule.evidence_excerpt
        )]
    )
