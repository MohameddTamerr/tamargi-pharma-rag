from typing import List, Dict, Any, Optional
import torch
from sentence_transformers import CrossEncoder
from app.config import settings

class RerankerModel:
    _instance = None

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = None
        self.is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RerankerModel()
        return cls._instance

    def load(self):
        if self.is_loaded:
            return
        print(f"[Reranker] Loading CrossEncoder model: {settings.RERANKER_MODEL} on {self.device}...")
        self.reranker = CrossEncoder(
            settings.RERANKER_MODEL,
            device=self.device
        )
        self.is_loaded = True
        print("[Reranker] Model loaded successfully.")

reranker_instance = RerankerModel.get_instance()

FORMULARY_MAP = {
    "warfarin": "egypt_blood_disorders_formulary_2025.pdf",
    "enoxaparin": "egypt_blood_disorders_formulary_2025.pdf",
    "heparin": "egypt_blood_disorders_formulary_2025.pdf",
    "omeprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "pantoprazole": "egypt_gastrointestinal_formulary_2025.pdf",
    "furosemide": "egypt_cardiovascular_formulary_2024.pdf",
    "spironolactone": "egypt_cardiovascular_formulary_2024.pdf",
    "bisoprolol": "egypt_cardiovascular_formulary_2024.pdf",
    "captopril": "egypt_cardiovascular_formulary_2024.pdf",
    "propranolol": "egypt_cardiovascular_formulary_2024.pdf",
    "nitroglycerin": "egypt_cardiovascular_formulary_2024.pdf",
    "clopidogrel": "egypt_cardiovascular_formulary_2024.pdf",
    "atorvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "simvastatin": "egypt_cardiovascular_formulary_2024.pdf",
    "amoxicillin": "egypt_antimicrobial_formulary_2023.pdf",
    "ciprofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "levofloxacin": "egypt_antimicrobial_formulary_2023.pdf",
    "clarithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "azithromycin": "egypt_antimicrobial_formulary_2023.pdf",
    "sulfamethoxazole": "egypt_antimicrobial_formulary_2023.pdf",
    "dexamethasone": "egypt_endocrine_formulary_2024.pdf",
    "metformin": "egypt_endocrine_formulary_2024.pdf",
    "methotrexate": "egypt_conventional_anticancer_formulary_2024.pdf",
    "capecitabine": "egypt_targeted_anticancer_formulary_2025.pdf",
    "sildenafil": "egypt_cardiovascular_formulary_2024.pdf",
    "ibuprofen": "egypt_blood_disorders_formulary_2025.pdf",
    "paracetamol": "egypt_otc_drug_list_2026.pdf"
}

def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: Optional[int] = None,
    target_medications: Optional[List[str]] = None,
    target_section: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Reranks candidate chunks with contextual cross-encoder input:
    Drug: [Canonical Drug]
    Section: [Normalized Section]
    Document: [Source Document]
    Text: [Chunk Text]
    """
    if top_k is None:
        top_k = settings.FINAL_K

    if not results:
        return []

    if not reranker_instance.is_loaded:
        reranker_instance.load()

    # 1. Build contextual candidate inputs for CrossEncoder
    pairs = []
    for res in results:
        c_drug = str(res.get("canonical_drug", "")).strip()
        c_sec = str(res.get("section", "")).strip()
        c_file = str(res.get("file", res.get("source_file", ""))).strip()
        c_text = str(res.get("text", "")).strip()

        header_lines = []
        if c_drug:
            header_lines.append(f"Drug: {c_drug.title()}")
        if c_sec and c_sec != "other":
            header_lines.append(f"Section: {c_sec.replace('_', ' ').title()}")
        if c_file:
            header_lines.append(f"Document: {c_file}")

        context_prefix = "\n".join(header_lines)
        cand_input = f"{context_prefix}\n\n{c_text}".strip() if context_prefix else c_text
        pairs.append([query, cand_input])

    raw_scores = reranker_instance.reranker.predict(pairs)

    q_lower = query.lower()
    is_otc_q = ("otc" in q_lower or "over the counter" in q_lower or "الجرعة القصوى" in query or "maximum daily" in q_lower)
    is_dnc_q = ("do not crush" in q_lower or "crush" in q_lower or "طحن" in query or "كسر" in query)
    is_ha_q = ("high alert" in q_lower or "high-alert" in q_lower or "عالي الخطورة" in query)

    target_meds = [m.lower().strip() for m in target_medications if m] if target_medications else []

    reranked = []
    for res, score in zip(results, raw_scores):
        new_res = res.copy()
        adj_score = float(score)
        c_text = str(res.get("text", "")).lower()
        c_file = str(res.get("file", res.get("source_file", ""))).lower()
        c_drug = str(res.get("canonical_drug", "")).lower().strip()
        c_sec = str(res.get("section", "")).lower().strip()

        # 1. Document priority for special guidelines
        if is_otc_q:
            if "egypt_otc_drug_list" in c_file:
                adj_score += 1.20
            else:
                adj_score -= 0.50
        elif is_dnc_q:
            if "egypt_do_not_crush" in c_file:
                adj_score += 1.20
            else:
                adj_score -= 0.50
        elif is_ha_q:
            if "egypt_high_alert" in c_file:
                adj_score += 1.20
            else:
                adj_score -= 0.50
        elif target_meds:
            for tm in target_meds:
                exp_doc = FORMULARY_MAP.get(tm, "")
                if exp_doc and exp_doc in c_file:
                    adj_score += 0.50

        # 2. Canonical Entity match priority
        if target_meds:
            is_exact_drug_mono = any(tm == c_drug or tm in c_drug or c_drug in tm for tm in target_meds if c_drug)
            mentions_target = any(tm in c_text for tm in target_meds)

            if is_exact_drug_mono:
                adj_score += 1.00
            elif mentions_target:
                adj_score += 0.50
            else:
                # Strong penalty for other unrelated drug monographs
                if c_drug and not any(tm in c_drug for tm in target_meds):
                    adj_score -= 1.20

        # 3. Canonical Section & Clinical Concept match priority
        if "cyp3a4" in q_lower and "cyp3a4" in c_text:
            adj_score += 0.90
        if "81 mg" in q_lower and ("81 mg" in c_text or "81mg" in c_text or "aspocid" in c_text):
            adj_score += 0.90
        if "sublingual" in q_lower and ("sublingual" in c_text or "تحت اللسان" in c_text):
            adj_score += 0.70
        if "ace inhibitor" in q_lower and ("ace inhibitor" in c_text or "captopril" in c_text or "enalapril" in c_text):
            adj_score += 0.80

        if target_section and c_sec == target_section:
            adj_score += 0.75
        elif "contraindication" in q_lower or "موانع" in query or "ممنوع" in query:
            if c_sec == "contraindications" or "contraindication" in c_text:
                adj_score += 0.65
        elif "warning" in q_lower or "precaution" in q_lower or "تحذير" in query:
            if c_sec == "warnings_precautions" or "warning" in c_text:
                adj_score += 0.65
        elif "interaction" in q_lower or "تفاعل" in query or "تعارض" in query or "تداخل" in query:
            if c_sec == "drug_interactions" or "interaction" in c_text:
                adj_score += 0.85
        elif "adverse" in q_lower or "side effect" in q_lower or "اثار" in query or "أعراض" in query:
            if c_sec == "adverse_reactions" or "adverse" in c_text or "rupture" in c_text:
                adj_score += 0.65
        elif "administration" in q_lower or "طريقة" in query or "كيفية" in query:
            if c_sec == "administration" or "administer" in c_text or "take with" in c_text:
                adj_score += 0.65
        elif "dosage" in q_lower or "dose" in q_lower or "جرعة" in query:
            if c_sec in ("dosage", "dosage_adjustment", "dosage_form_strength") or "dose" in c_text or "mg" in c_text:
                adj_score += 0.65

        new_res["reranker_score"] = adj_score
        reranked.append(new_res)

    reranked = sorted(reranked, key=lambda x: x.get("reranker_score", 0.0), reverse=True)
    return reranked[:top_k]
