import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.supabase import get_supabase_client
from .models import VerifiedSafetyRule, SafetyStatus
from .normalizer import normalize_text, normalize_medication_name, normalize_condition_name

# In-memory store for verified safety rules (unit test & offline execution)
IN_MEMORY_VERIFIED_RULES: List[Dict[str, Any]] = []

def clear_test_rules():
    """Clears all in-memory safety rules for clean test execution."""
    IN_MEMORY_VERIFIED_RULES.clear()

def is_valid_verified_rule(rule: Dict[str, Any]) -> bool:
    """
    Strict evidence validation requirement:
    Every active verified safety rule MUST have:
    - active == True
    - verified == True
    - non-empty source_file
    - valid integer source_page > 0
    - non-empty evidence_excerpt
    """
    if not rule.get("active", True) or not rule.get("verified", False):
        return False

    source_file = rule.get("source_file")
    if not source_file or not str(source_file).strip():
        return False

    source_page = rule.get("source_page")
    if source_page is None:
        return False
    try:
        page_num = int(source_page)
        if page_num <= 0:
            return False
    except (ValueError, TypeError):
        return False

    excerpt = rule.get("evidence_excerpt")
    if not excerpt or not str(excerpt).strip():
        return False

    return True

def seed_verified_rule(rule_data: Dict[str, Any]) -> VerifiedSafetyRule:
    """
    Seeds a verified clinical safety rule into the repository.
    Generates UUID if not provided.
    """
    r_dict = dict(rule_data)
    if "id" not in r_dict or not r_dict["id"]:
        r_dict["id"] = str(uuid.uuid4())
    if "created_at" not in r_dict or not r_dict["created_at"]:
        r_dict["created_at"] = datetime.now()
    if "updated_at" not in r_dict or not r_dict["updated_at"]:
        r_dict["updated_at"] = datetime.now()
    if "source_authority" not in r_dict or not r_dict["source_authority"]:
        r_dict["source_authority"] = "Egyptian Drug Authority"

    # Normalize lookup terms for deterministic indexing
    if r_dict.get("drug_a"):
        gen_a, _ = normalize_medication_name(r_dict["drug_a"])
        r_dict["drug_a_norm"] = gen_a
    if r_dict.get("drug_b"):
        gen_b, _ = normalize_medication_name(r_dict["drug_b"])
        r_dict["drug_b_norm"] = gen_b
    if r_dict.get("condition_name"):
        r_dict["condition_norm"] = normalize_condition_name(r_dict["condition_name"])

    # Push to Supabase if connected
    client = get_supabase_client()
    if client:
        try:
            client.table("verified_safety_rules").insert(r_dict).execute()
        except Exception:
            pass

    IN_MEMORY_VERIFIED_RULES.append(r_dict)
    return VerifiedSafetyRule(**r_dict)

def get_verified_rules(
    rule_type: Optional[str] = None,
    drug_a: Optional[str] = None,
    drug_b: Optional[str] = None,
    condition_name: Optional[str] = None,
    allergen_class: Optional[str] = None
) -> List[VerifiedSafetyRule]:
    """
    Retrieves verified safety rules from Supabase (or in-memory store).
    Strictly filters out unverified, inactive, or evidence-incomplete rules.
    """
    norm_drug_a = normalize_medication_name(drug_a)[0] if drug_a else None
    norm_drug_b = normalize_medication_name(drug_b)[0] if drug_b else None
    norm_cond = normalize_condition_name(condition_name) if condition_name else None
    norm_allg = normalize_text(allergen_class) if allergen_class else None

    client = get_supabase_client()
    raw_rules = []

    if client:
        try:
            q = client.table("verified_safety_rules").select("*").eq("active", True).eq("verified", True)
            if rule_type:
                q = q.eq("rule_type", rule_type)
            res = q.execute()
            if res.data and len(res.data) > 0:
                raw_rules = res.data
        except Exception:
            pass

    if not raw_rules:
        raw_rules = IN_MEMORY_VERIFIED_RULES

    valid_matches: List[VerifiedSafetyRule] = []

    for r in raw_rules:
        if not is_valid_verified_rule(r):
            continue

        if rule_type and r.get("rule_type") != rule_type:
            continue

        r_drug_a = normalize_medication_name(r.get("drug_a", ""))[0]
        r_drug_b = normalize_medication_name(r.get("drug_b", ""))[0] if r.get("drug_b") else None
        r_cond = normalize_condition_name(r.get("condition_name", "")) if r.get("condition_name") else None
        r_allg = normalize_text(r.get("allergen_class", "")) if r.get("allergen_class") else None

        # Filter by drug_a
        if norm_drug_a:
            drug_match = (
                r_drug_a == norm_drug_a or
                norm_drug_a in r_drug_a or
                r_drug_a in norm_drug_a
            )
            # Check symmetrical drug-drug rule
            if not drug_match and r_drug_b:
                drug_match = (
                    r_drug_b == norm_drug_a or
                    norm_drug_a in r_drug_b or
                    r_drug_b in norm_drug_a
                )
            if not drug_match:
                continue

        # Filter by drug_b
        if norm_drug_b:
            dd_match = (
                (r_drug_a == norm_drug_a and r_drug_b == norm_drug_b) or
                (r_drug_a == norm_drug_b and r_drug_b == norm_drug_a) or
                (r_drug_b and (norm_drug_b in r_drug_b or r_drug_b in norm_drug_b))
            )
            if not dd_match:
                continue

        # Filter by condition
        if norm_cond:
            if r_cond and r_cond != norm_cond and norm_cond not in r_cond and r_cond not in norm_cond:
                continue

        # Filter by allergen_class
        if norm_allg:
            if r_allg and r_allg != norm_allg and norm_allg not in r_allg:
                continue

        valid_matches.append(VerifiedSafetyRule(**r))

    return valid_matches
