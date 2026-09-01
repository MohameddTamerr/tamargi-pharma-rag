from typing import Optional, List, Dict, Any
from app.safety.models import SafetyResult, SafetyStatus

def is_insufficient_evidence(answer: str) -> bool:
    """Checks if the answer is an insufficient evidence refusal."""
    if not answer:
        return False
    ans_clean = answer.strip().lower()
    insufficient_phrases = [
        "the retrieved evidence is insufficient to answer this question safely.",
        "الأدلة المسترجعة غير كافية للإجابة عن هذا السؤال بأمان.",
        "عفواً، الأدلة المتاحة غير كافية للإجابة على هذا السؤال بشكل آمن.",
        "insufficient to answer",
        "غير كافية للإجابة",
        "لم تتوفر أدلة كافية"
    ]
    return any(phrase.lower() in ans_clean for phrase in insufficient_phrases)

def compose_final_response(
    primary_answer: str,
    safety_result: Optional[SafetyResult] = None,
    video_result: Optional[Dict[str, Any]] = None,
    plan_result: Optional[Dict[str, Any]] = None,
    is_confirmation_turn: bool = False,
    confirmation_ack: Optional[str] = None
) -> str:
    """
    Composes a coherent, polished user-facing response from structured tool outputs.
    Avoids exposing raw internal JSON and highlights critical safety callouts clearly.
    """
    if is_confirmation_turn and confirmation_ack:
        if primary_answer and primary_answer.strip():
            return f"{confirmation_ack}\n\n{primary_answer}"
        return confirmation_ack

    final_text = primary_answer.strip() if primary_answer else ""

    # 1. Append Safety Engine Warning / Contraindication Callout Box
    if safety_result and safety_result.overall_status in (SafetyStatus.CONTRAINDICATED, SafetyStatus.WARNING, SafetyStatus.CAUTION):
        if not is_insufficient_evidence(final_text):
            status_label = "⛔ تحذير طبي هام (ممنوع الاستخدام):" if safety_result.overall_status == SafetyStatus.CONTRAINDICATED else "🛡️ تنبيه الأمان الدوائي:"
            safety_box = f"\n\n> {status_label} {safety_result.summary}"
            for chk in safety_result.checks:
                safety_box += f"\n> - **{chk.patient_factor}**: {chk.reason}"
            
            if safety_box not in final_text:
                final_text = safety_box + "\n\n" + final_text

    # 2. Append Inhaler Video Helper Prompt if exact device was unknown
    if video_result and not video_result.get("found"):
        if video_result.get("reason") in ("exact_device_unknown", "brand_required"):
            helper_msg = "\n\n> 💡 **ملاحظة بخصوص طريقة الاستخدام:** في أنواع مختلفة من أجهزة الاستنشاق وطريقة استخدامها بتختلف. ابعتلي اسم الجهاز أو اسم الدواء المكتوب على البخاخ عشان أجيبلك فيديو الاستخدام الصحيح."
            if helper_msg not in final_text:
                if is_insufficient_evidence(final_text):
                    final_text = helper_msg.strip()
                else:
                    final_text += helper_msg

    # 3. Append Medication Plan Creation Summary
    if plan_result:
        plan_id = plan_result.get("id", "")
        token = plan_result.get("verification_token", "")
        plan_summary = f"\n\n📋 **تم إعداد مسودة الخطة الدوائية للمراجعة الطبية بنجاح.**\n- **رقم الخطة:** `{plan_id[:13]}...`\n- يمكنك استعراض الخطة وطباعتها ومسح رمز QR الموثق لتقديمه للصيدلي عبر صفحة [الخطط الدوائية](/plans)."
        if plan_summary not in final_text:
            final_text += plan_summary

    return final_text
