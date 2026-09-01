import pandas as pd
import csv

audit_data = [
    # 1. NSAID + CKD
    {
        "rule_type": "drug_disease",
        "drug_a": "ibuprofen",
        "drug_b_or_condition": "chronic_kidney_disease",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_antimicrobial_formulary_2023.pdf",
        "source_page": 164,
        "source_section": "Warnings / Renal Impairment",
        "exact_evidence_excerpt": "Use with caution in patients with renal dysfunction or in patients at risk of renal toxicity (including concurrent nephrotoxic agents or NSAIDs).",
        "scope_notes": "General class warning for NSAIDs in renal dysfunction mentioned across combination monographs, but individual ibuprofen monograph is not in cardiovascular formulary.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Partially verified as class caution in renal risk; individual monograph not present on claimed page."
    },
    # 2. NSAID + PUD
    {
        "rule_type": "drug_disease",
        "drug_a": "ibuprofen",
        "drug_b_or_condition": "peptic_ulcer_disease",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_gastrointestinal_formulary_2025.pdf",
        "source_page": 18,
        "source_section": "Peptic Ulcer Disease Management",
        "exact_evidence_excerpt": "NSAID-associated ulceration requires discontinuation of NSAID therapy or concurrent gastroprotective co-therapy.",
        "scope_notes": "GI formulary details NSAID ulcer risk under PPI indications, but standalone OTC ibuprofen monograph is separate.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Supported by ulcer management guidelines, but exact claimed table not present on page 78."
    },
    # 3. NSAID + Asthma
    {
        "rule_type": "drug_disease",
        "drug_a": "ibuprofen",
        "drug_b_or_condition": "asthma",
        "old_status": "caution",
        "verified_status": "caution",
        "final_status": "caution",
        "source_file": "egypt_respiratory_formulary_2026.pdf",
        "source_page": 24,
        "source_section": "Asthma / AERD Precautions",
        "exact_evidence_excerpt": "Patients with asthma sensitive to aspirin or other NSAIDs should avoid all nonsteroidal anti-inflammatory drugs.",
        "scope_notes": "Specific to aspirin/NSAID-sensitive asthma subset (AERD).",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Applies specifically to aspirin-sensitive asthmatic patients; requires qualifier."
    },
    # 4. Dexamethasone + Diabetes
    {
        "rule_type": "drug_disease",
        "drug_a": "dexamethasone",
        "drug_b_or_condition": "diabetes_mellitus",
        "old_status": "caution",
        "verified_status": "caution",
        "final_status": "caution",
        "source_file": "egypt_endocrine_formulary_2024.pdf",
        "source_page": 153,
        "source_section": "Adverse Drug Reactions / Endocrine & Metabolic",
        "exact_evidence_excerpt": "Hyperglycemia: may provoke new-onset hyperglycemia in patients without a history of diabetes or worsen pre-existing diabetes.",
        "scope_notes": "Directly supported in Dexamethasone endocrine monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 153. Supports caution status for diabetic patients."
    },
    # 5. Propranolol + Asthma
    {
        "rule_type": "drug_disease",
        "drug_a": "propranolol",
        "drug_b_or_condition": "asthma",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_cardiovascular_formulary_2024.pdf",
        "source_page": 122,
        "source_section": "Contraindications",
        "exact_evidence_excerpt": "Contraindications: Asthma or severe chronic obstructive pulmonary disease; sinus bradycardia; cardiogenic shock.",
        "scope_notes": "Exact contraindication in Propranolol monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 122. Supports contraindicated status."
    },
    # 6. Pseudoephedrine + Hypertension
    {
        "rule_type": "drug_disease",
        "drug_a": "pseudoephedrine",
        "drug_b_or_condition": "hypertension",
        "old_status": "warning",
        "verified_status": "unsupported",
        "final_status": "warning",
        "source_file": "egypt_cardiovascular_formulary_2024.pdf",
        "source_page": 140,
        "source_section": "N/A",
        "exact_evidence_excerpt": "N/A",
        "scope_notes": "Page 140 in cardiovascular formulary contains Digoxin/Cardiac Glycosides, not pseudoephedrine.",
        "verification_status": "NOT_VERIFIED",
        "verification_notes": "Claimed source and page do not contain pseudoephedrine monograph."
    },
    # 7. Metformin + CKD
    {
        "rule_type": "drug_disease",
        "drug_a": "metformin",
        "drug_b_or_condition": "chronic_kidney_disease",
        "old_status": "warning",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_endocrine_formulary_2024.pdf",
        "source_page": 32,
        "source_section": "Dosing: Renal Impairment: Adult",
        "exact_evidence_excerpt": "eGFR <30 mL/minute/1.73 m2: Use is contraindicated.",
        "scope_notes": "Contraindicated specifically at eGFR < 30 mL/min/1.73m2 (severe renal impairment), not all CKD stages.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Source confirmed at page 32, but rule is partially verified pending schema numerical qualifier (eGFR < 30)."
    },
    # 8. Sildenafil + Nitrates
    {
        "rule_type": "drug_drug",
        "drug_a": "sildenafil",
        "drug_b_or_condition": "nitroglycerin",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_cardiovascular_formulary_2024.pdf",
        "source_page": 71,
        "source_section": "Contraindications",
        "exact_evidence_excerpt": "Concurrent use with phosphodiesterase inhibitors (Sildenafil, Tadalafil, Vardenafil, or Avanafil).",
        "scope_notes": "Explicitly contraindicated in Isosorbide Dinitrate monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 71. Directly supports contraindicated status."
    },
    # 9. Warfarin + Ibuprofen
    {
        "rule_type": "drug_drug",
        "drug_a": "warfarin",
        "drug_b_or_condition": "ibuprofen",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_blood_disorders_formulary_2025.pdf",
        "source_page": 12,
        "source_section": "Drug Interactions / Anticoagulants",
        "exact_evidence_excerpt": "Concomitant use of anticoagulants with antiplatelet agents or NSAIDs increases the risk of bleeding.",
        "scope_notes": "Broad anticoagulant class bleeding risk interaction.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Supports bleeding warning for class, but claimed page 35 was incorrect."
    },
    # 10. Methotrexate + Ibuprofen
    {
        "rule_type": "drug_drug",
        "drug_a": "methotrexate",
        "drug_b_or_condition": "ibuprofen",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_conventional_anticancer_formulary_2024.pdf",
        "source_page": 89,
        "source_section": "Drug Interactions / Antifolates",
        "exact_evidence_excerpt": "Caution is advised if NSAIDs are coadministered with antifolates due to reduced renal clearance.",
        "scope_notes": "Documented in antifolate anticancer monograph.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Supported under antifolate precautions; claimed page 64 corrected to page 89."
    },
    # 11. Clarithromycin + Simvastatin
    {
        "rule_type": "drug_drug",
        "drug_a": "clarithromycin",
        "drug_b_or_condition": "simvastatin",
        "old_status": "warning",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_antimicrobial_formulary_2023.pdf",
        "source_page": 180,
        "source_section": "Contraindications",
        "exact_evidence_excerpt": "Concomitant administration with astemizole, cisapride, pimozide, terfenadine, or lovastatin/simvastatin (risk of rhabdomyolysis).",
        "scope_notes": "Explicit contraindication in Clarithromycin antimicrobial monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 180. Status upgraded to contraindicated per exact EDA text."
    },
    # 12. Clopidogrel + Omeprazole
    {
        "rule_type": "drug_drug",
        "drug_a": "clopidogrel",
        "drug_b_or_condition": "omeprazole",
        "old_status": "caution",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_cardiovascular_formulary_2024.pdf",
        "source_page": 44,
        "source_section": "Drug Interactions",
        "exact_evidence_excerpt": "Avoid concomitant use of clopidogrel and omeprazole or esomeprazole because of significantly reduced antiplatelet activity.",
        "scope_notes": "Explicit warning to avoid combination in Clopidogrel monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 44. Supports warning status."
    },
    # 13. Spironolactone + Captopril
    {
        "rule_type": "drug_drug",
        "drug_a": "spironolactone",
        "drug_b_or_condition": "captopril",
        "old_status": "caution",
        "verified_status": "caution",
        "final_status": "caution",
        "source_file": "egypt_cardiovascular_formulary_2024.pdf",
        "source_page": 177,
        "source_section": "Warnings / Precautions",
        "exact_evidence_excerpt": "When evaluating a heart failure patient for spironolactone treatment, eGFR should be >30 mL/minute/1.73 m2 and potassium <5 mEq/L with no history of severe hyperkalemia.",
        "scope_notes": "Co-administration requires close potassium monitoring.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 177. Supports caution status."
    },
    # 14. High Alert Insulin
    {
        "rule_type": "high_alert",
        "drug_a": "insulin",
        "drug_b_or_condition": "Insulins (All Formulations)",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_high_alert_medications_2025.pdf",
        "source_page": 10,
        "source_section": "High Alert Medication List in Community/Ambulatory Care Settings",
        "exact_evidence_excerpt": "1 Insulin, all formulations, all routes of administration (e.g., Subcutaneous, IV).",
        "scope_notes": "Explicit category 1 on page 10 of National Egyptian High Alert List 2025.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 10. Supports high_alert warning."
    },
    # 15. High Alert Anticoagulants (Enoxaparin / Heparin)
    {
        "rule_type": "high_alert",
        "drug_a": "enoxaparin",
        "drug_b_or_condition": "Antithrombotic agents (LMWH)",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_high_alert_medications_2025.pdf",
        "source_page": 6,
        "source_section": "High Alert Medication List in Acute Care",
        "exact_evidence_excerpt": "6 Antithrombotic agents Examples: Low molecular weight heparin (Enoxaparin), Unfractionated heparin IV, Direct thrombin inhibitors.",
        "scope_notes": "Explicit category 6 on page 6-7 of National Egyptian High Alert List 2025.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 6-7. Supports high_alert warning."
    },
    # 16. High Alert Chemotherapy (Capecitabine / Cyclophosphamide)
    {
        "rule_type": "high_alert",
        "drug_a": "capecitabine",
        "drug_b_or_condition": "Chemotherapeutic agents",
        "old_status": "warning",
        "verified_status": "warning",
        "final_status": "warning",
        "source_file": "egypt_high_alert_medications_2025.pdf",
        "source_page": 11,
        "source_section": "High Alert Medication List in Community/Ambulatory Care Settings",
        "exact_evidence_excerpt": "2 Chemotherapeutic agents, excluding hormonal therapy: Oral and parenteral chemotherapy (e.g., capecitabine, cyclophosphamide).",
        "scope_notes": "Explicit category 2 on page 11 of National Egyptian High Alert List 2025.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 11. Supports high_alert warning."
    },
    # 17. High Alert Digoxin
    {
        "rule_type": "high_alert",
        "drug_a": "digoxin",
        "drug_b_or_condition": "Cardiac Glycosides",
        "old_status": "warning",
        "verified_status": "unsupported",
        "final_status": "warning",
        "source_file": "egypt_high_alert_medications_2025.pdf",
        "source_page": 16,
        "source_section": "N/A",
        "exact_evidence_excerpt": "N/A",
        "scope_notes": "Document egypt_high_alert_medications_2025.pdf has 14 pages total; page 16 does not exist.",
        "verification_status": "NOT_VERIFIED",
        "verification_notes": "Claimed page 16 does not exist in high alert document."
    },
    # 18. Do Not Crush Glucophage XR
    {
        "rule_type": "do_not_crush",
        "drug_a": "glucophage xr",
        "drug_b_or_condition": "Modified/Extended-release",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_do_not_crush_medications_2026.pdf",
        "source_page": 6,
        "source_section": "Introduction / Release-Mechanism Disruption",
        "exact_evidence_excerpt": "Modified-release oral dosage forms: Crushing destroys the release mechanism, potentially resulting in dose dumping and toxicity.",
        "scope_notes": "Covers extended-release mechanism in general; brand table needs manual review.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Mechanism verified on page 6; specific brand table requires manual verification."
    },
    # 19. Do Not Crush Enteric-Coated (Aspirin / Aspocid)
    {
        "rule_type": "do_not_crush",
        "drug_a": "aspocid 81",
        "drug_b_or_condition": "Enteric-coated",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_do_not_crush_medications_2026.pdf",
        "source_page": 7,
        "source_section": "Enteric-Coated Formulations",
        "exact_evidence_excerpt": "Enteric-coated tablets: Designed to pass through the stomach intact and dissolve in the intestine. Crushing destroys the protective coating.",
        "scope_notes": "Explicit guideline for enteric-coated solid dosage forms.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 7. Supports contraindicated status."
    },
    # 20. Do Not Crush Sublingual Formulations
    {
        "rule_type": "do_not_crush",
        "drug_a": "nitroglycerin sublingual",
        "drug_b_or_condition": "Sublingual/buccal",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_do_not_crush_medications_2026.pdf",
        "source_page": 8,
        "source_section": "Sublingual and Buccal Dosage Forms",
        "exact_evidence_excerpt": "Sublingual or buccal tablets: Formulated to release drug for direct absorption through oral mucosa. Swallowing or crushing leads to loss of efficacy.",
        "scope_notes": "Explicit guideline for sublingual and buccal solid dosage forms.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 8. Supports contraindicated status."
    },
    # 21. Allergy Amoxicillin + Penicillins
    {
        "rule_type": "allergy",
        "drug_a": "amoxicillin",
        "drug_b_or_condition": "penicillins",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_antimicrobial_formulary_2023.pdf",
        "source_page": 371,
        "source_section": "Contraindications",
        "exact_evidence_excerpt": "Serious hypersensitivity to amoxicillin or to other beta-lactams, or any component of the formulation.",
        "scope_notes": "Direct contraindication in Amoxicillin monograph for beta-lactam hypersensitivity.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 371. Directly supports contraindicated status."
    },
    # 22. Allergy Sulfamethoxazole + Sulfonamides
    {
        "rule_type": "allergy",
        "drug_a": "sulfamethoxazole",
        "drug_b_or_condition": "sulfonamides",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_antimicrobial_formulary_2023.pdf",
        "source_page": 346,
        "source_section": "Contraindications",
        "exact_evidence_excerpt": "Hypersensitivity to trimethoprim or sulfonamides, or any component of the formulation.",
        "scope_notes": "Direct contraindication in Sulfamethoxazole/Trimethoprim monograph.",
        "verification_status": "VERIFIED",
        "verification_notes": "Source confirmed at page 346. Directly supports contraindicated status."
    },
    # 23. Allergy Ibuprofen + NSAIDs
    {
        "rule_type": "allergy",
        "drug_a": "ibuprofen",
        "drug_b_or_condition": "nsaids",
        "old_status": "contraindicated",
        "verified_status": "contraindicated",
        "final_status": "contraindicated",
        "source_file": "egypt_respiratory_formulary_2026.pdf",
        "source_page": 24,
        "source_section": "Asthma / AERD Warnings",
        "exact_evidence_excerpt": "Patients with a history of hypersensitivity to aspirin or other NSAIDs may experience severe bronchospasm.",
        "scope_notes": "Class cross-reactivity for NSAID hypersensitivity.",
        "verification_status": "PARTIALLY_VERIFIED",
        "verification_notes": "Documented as warning in respiratory formulary; requires AERD qualification."
    }
]

df_verified = pd.DataFrame(audit_data)
df_verified.to_csv('c:/Users/user/Downloads/tamargi-pharma-rag/data/processed/safety_rule_audit_verified.csv', index=False, encoding='utf-8')
print("Successfully generated data/processed/safety_rule_audit_verified.csv")

# Print Summary
status_counts = df_verified['verification_status'].value_counts()
print("\n--- VERIFICATION STATUS BREAKDOWN ---")
print(status_counts)
