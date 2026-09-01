import re
from typing import Optional, List, Tuple

CANONICAL_SECTIONS = [
    "indications",
    "contraindications",
    "dosage",
    "dosage_adjustment",
    "administration",
    "warnings_precautions",
    "drug_interactions",
    "adverse_reactions",
    "monitoring",
    "pregnancy_lactation",
    "dosage_form_strength",
    "route",
    "pharmacologic_category",
    "high_alert",
    "do_not_crush",
    "other"
]

SECTION_PATTERNS: List[Tuple[str, List[str]]] = [
    ("contraindications", [
        r"contraindications?",
        r"contra-indications?",
        r"موانع الاستعمال",
        r"موانع الاستخدام",
        r"ممنوع"
    ]),
    ("indications", [
        r"indications?\b",
        r"therapeutic uses?",
        r"approved indications?",
        r"دواعي الاستعمال",
        r"دواعي الاستخدام",
        r"استخدامات"
    ]),
    ("dosage_adjustment", [
        r"dosage adjustment\b",
        r"dose adjustment\b",
        r"renal dosage adjustment",
        r"hepatic dosage adjustment",
        r"dosing: altered kidney function",
        r"dosing: hepatic impairment",
        r"جرعة مرضى الكلى",
        r"جرعة مرضى الكبد"
    ]),
    ("dosage", [
        r"dosage(?:\s+and\s+administration)?",
        r"dosing\b",
        r"dosage\s+regimen",
        r"doses?\b",
        r"adult dosing",
        r"pediatric dosing",
        r"الجرعة",
        r"جرعات"
    ]),
    ("administration", [
        r"administration\b",
        r"how to take",
        r"method of administration",
        r"طريقة الاستعمال",
        r"كيفية الاستخدام",
        r"طريقة أخذ"
    ]),
    ("warnings_precautions", [
        r"warnings(?:\s*/\s*|\s+and\s+)precautions",
        r"warnings?\b",
        r"precautions?\b",
        r"special warnings",
        r"black box warning",
        r"تحذيرات واحتياطات",
        r"تحذيرات",
        r"احتياطات"
    ]),
    ("drug_interactions", [
        r"drug interactions?",
        r"interactions?\b",
        r"تفاعلات دوائية",
        r"تداخلات دوائية",
        r"التعارضات"
    ]),
    ("adverse_reactions", [
        r"adverse reactions?",
        r"adverse effects?",
        r"side effects?",
        r"undesirable effects",
        r"الآثار الجانبية",
        r"الأعراض الجانبية",
        r"أعراض جانبية"
    ]),
    ("monitoring", [
        r"monitoring parameters?",
        r"monitoring\b",
        r"patient monitoring",
        r"المتابعة والتحاليل"
    ]),
    ("pregnancy_lactation", [
        r"pregnancy(?:\s+and\s+lactation)?",
        r"pregnancy\b",
        r"lactation\b",
        r"breastfeeding",
        r"الحمل والرضاعة",
        r"الحمل",
        r"الرضاعة"
    ]),
    ("dosage_form_strength", [
        r"dosage forms?(?:\s+and\s+strengths?)?",
        r"forms and strengths",
        r"available forms",
        r"strength\b",
        r"الأشكال الدوائية والتركيزات"
    ]),
    ("route", [
        r"route of administration",
        r"route\b"
    ]),
    ("pharmacologic_category", [
        r"pharmacologic category",
        r"drug class",
        r"mechanism of action",
        r"التصنيف الدوائي"
    ]),
    ("high_alert", [
        r"high alert\b",
        r"high-alert",
        r"أدوية عالية الخطورة",
        r"عالي الخطورة"
    ]),
    ("do_not_crush", [
        r"do not crush",
        r"oral dosage forms that should not be crushed",
        r"ممنوع كسرها",
        r"أدوية لا تطحن"
    ])
]

def normalize_section_heading(heading_text: str) -> str:
    """
    Normalizes raw section heading text into one of the canonical section strings.
    """
    clean = heading_text.strip().lower()
    clean = re.sub(r"[\r\n\t]+", " ", clean)
    clean = re.sub(r"[•\-\*:#_]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    for canonical, patterns in SECTION_PATTERNS:
        for pat in patterns:
            if re.search(pat, clean, re.IGNORECASE):
                return canonical

    return "other"

def detect_section_in_text(chunk_text: str) -> Optional[str]:
    """
    Scans the beginning lines of a chunk for recognizable section headings,
    supporting split lines like 'Dosage\nRegimen' or 'Warnings/\nPrecautions'.
    """
    # Look at the first 300 characters
    prefix = chunk_text[:300]
    lines = [l.strip() for l in prefix.split("\n") if l.strip()]

    # Check first 3 lines individually and pairs
    for i in range(min(len(lines), 3)):
        # Single line
        sec = normalize_section_heading(lines[i])
        if sec != "other":
            return sec
        # Joined line pair (split heading)
        if i + 1 < len(lines):
            pair = f"{lines[i]} {lines[i+1]}"
            sec_pair = normalize_section_heading(pair)
            if sec_pair != "other":
                return sec_pair

    # Scan for prominent inline section markers
    for canonical, patterns in SECTION_PATTERNS:
        for pat in patterns:
            # Check if pattern occurs as a heading (at line start or after newline/bullet)
            heading_regex = rf"(?:^|\n|•)\s*(?:{pat})\s*(?::|\n|-|$)"
            if re.search(heading_regex, chunk_text[:400], re.IGNORECASE):
                return canonical

    return None
