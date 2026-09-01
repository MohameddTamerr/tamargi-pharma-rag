import re
from typing import Optional, List
from .models import SafetyCheckItem, SafetyStatus, EvidenceCitation
from .normalizer import normalize_medication_name, normalize_text
from .repository import get_verified_rules

CRUSHING_INTENT_PATTERNS = [
    r"(?:اطحن|طحن|اكسر|كسر|افتح\s+الكبسولة|امضغ|مضغ|ينفع\s+اطحن|ينفع\s+اكسر|ينفع\s+امضغ)",
    r"(?:crush|split|break|chew|open\s+capsule|can\s+i\s+crush|crushing)"
]

def check_do_not_crush(query: str, medication: str) -> Optional[SafetyCheckItem]:
    """
    Checks if a medication has a verified do-not-crush rule when crushing intent is detected.
    """
    if not query or not medication:
        return None

    query_norm = normalize_text(query)
    has_crush_intent = any(re.search(pat, query_norm, re.IGNORECASE) for pat in CRUSHING_INTENT_PATTERNS)

    if not has_crush_intent:
        return None

    gen_name, brand_name = normalize_medication_name(medication)

    # Query verified rules for do_not_crush category
    verified_rules = get_verified_rules(rule_type="do_not_crush", drug_a=gen_name)
    if not verified_rules and brand_name:
        verified_rules = get_verified_rules(rule_type="do_not_crush", drug_a=brand_name)

    if not verified_rules:
        return None

    matched_rule = verified_rules[0]

    return SafetyCheckItem(
        type="do_not_crush",
        status=matched_rule.status,
        medication=medication,
        patient_factor=f"Dosage Form Property: {matched_rule.dosage_form or 'Do Not Crush'}",
        reason=matched_rule.reason or "Do not crush, chew, or open this solid dosage form.",
        evidence_ids=[str(matched_rule.id)],
        evidence=[EvidenceCitation(
            rule_id=str(matched_rule.id),
            source=matched_rule.source_file,
            page=matched_rule.source_page,
            section=matched_rule.source_section,
            excerpt=matched_rule.evidence_excerpt
        )]
    )
