import uuid
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from app.language.detector import detect_language
from app.safety.models import SafetyResult, SafetyStatus, ConfirmationContext, PatientProfile
from app.safety.patient_context import (
    get_patient_profile,
    get_active_pending_confirmation,
    extract_patient_facts_from_chat
)
from app.orchestrator.intents import IntentType, detect_intents
from app.orchestrator.entity_extractor import extract_entities, ExtractedEntities
from app.orchestrator.tools import (
    tool_medication_resolver,
    tool_patient_profile,
    tool_safety_engine,
    tool_hybrid_rag,
    tool_drug_comparison_retrieval,
    tool_verified_video,
    tool_confirmation_handler,
    tool_medication_plan_generator
)
from app.orchestrator.response_composer import compose_final_response, is_insufficient_evidence
from app.database.supabase import save_chat_message, log_unanswered_query

class OrchestrationTrace(BaseModel):
    intent: str
    secondary_intents: List[str] = Field(default_factory=list)
    entities: ExtractedEntities
    tools_called: List[str] = Field(default_factory=list)
    confirmation_required: bool = False
    safety_status: Optional[str] = None
    video_checked: bool = False
    plan_generated: bool = False

class OrchestrationResult(BaseModel):
    query: str
    normalized_query: str
    language_detected: str
    answer: str
    sources: List[Any] = Field(default_factory=list)
    video: Optional[Dict[str, Any]] = None
    safety: Optional[SafetyResult] = None
    requires_confirmation: bool = False
    confirmation: Optional[ConfirmationContext] = None
    plan: Optional[Dict[str, Any]] = None
    trace: OrchestrationTrace

class TamargiOrchestrator:
    """
    Central Agentic Orchestrator for Tamargi.ai.
    Coordinates deterministic tools based on intent and structured healthcare entities.
    """

    @classmethod
    def orchestrate(
        cls,
        query: str,
        conversation_id: Optional[str] = "default_conv",
        user_id: Optional[str] = "guest_user",
        input_type: Optional[str] = "text"
    ) -> OrchestrationResult:
        original_query = query.strip()
        conv_id = conversation_id or "default_conv"
        uid = user_id or "guest_user"
        tools_called: List[str] = []

        # -------------------------------------------------------------
        # 1. Check for Pending Medical Fact Confirmation Continuation
        # -------------------------------------------------------------
        has_pending = get_active_pending_confirmation(uid, conv_id) is not None

        is_resolved, decision, pending_item = tool_confirmation_handler(uid, conv_id, original_query)
        if is_resolved and pending_item:
            tools_called.append("confirmation_resolver")
            ack_msg = ""
            if decision == "confirmed":
                ack_msg = f"شكراً لتأكيدك. تم تحديث ملفك الطبي بأن معلومة ({pending_item.normalized_value}) ما زالت صحيحة ومؤكدة لديك."
            else:
                ack_msg = f"شكراً لتوضيحك. تم تحديث ملفك الطبي واستبعاد ({pending_item.normalized_value})."

            # AUTOMATIC CONTINUATION: If an original question was paused, resume it immediately!
            if pending_item.original_question and pending_item.medication_context:
                tools_called.append("patient_profile")
                tools_called.append("safety_engine")
                tools_called.append("hybrid_rag")

                prof = tool_patient_profile(uid)
                resumed_rag, resumed_sources, resumed_rag_ans = tool_hybrid_rag(pending_item.original_question)

                safety_eval = tool_safety_engine(
                    medication=pending_item.medication_context,
                    patient_profile=prof,
                    query_text=pending_item.original_question,
                    conversation_id=conv_id,
                    retrieved_evidence=resumed_rag
                )

                composed_ans = compose_final_response(
                    primary_answer=resumed_rag_ans,
                    safety_result=safety_eval,
                    is_confirmation_turn=True,
                    confirmation_ack=ack_msg
                )

                trace = OrchestrationTrace(
                    intent="confirmation_response",
                    entities=ExtractedEntities(medications=[pending_item.medication_context]),
                    tools_called=tools_called,
                    confirmation_required=False,
                    safety_status=safety_eval.overall_status.value if safety_eval else None
                )

                # Persist messages
                cls._persist_interaction(conv_id, uid, original_query, composed_ans, input_type, resumed_sources)

                return OrchestrationResult(
                    query=original_query,
                    normalized_query=pending_item.original_question,
                    language_detected="ar",
                    answer=composed_ans,
                    sources=resumed_sources,
                    safety=safety_eval,
                    trace=trace
                )

            # Standalone confirmation reply
            trace = OrchestrationTrace(
                intent="confirmation_response",
                entities=ExtractedEntities(),
                tools_called=tools_called,
                confirmation_required=False
            )
            cls._persist_interaction(conv_id, uid, original_query, ack_msg, input_type, [])
            return OrchestrationResult(
                query=original_query,
                normalized_query=original_query,
                language_detected="ar",
                answer=ack_msg,
                sources=[],
                trace=trace
            )

        # -------------------------------------------------------------
        # 2. Extract Explicit Facts & Entities
        # -------------------------------------------------------------
        tools_called.append("entity_extractor")
        extract_patient_facts_from_chat(uid, original_query)
        entities = extract_entities(original_query)

        # -------------------------------------------------------------
        # 3. Detect Intent
        # -------------------------------------------------------------
        intent_res = detect_intents(
            query_text=original_query,
            has_pending_confirmation=has_pending,
            candidate_medications=entities.medications,
            candidate_devices=entities.devices,
            candidate_symptoms=entities.symptoms
        )
        primary_intent = intent_res.primary_intent
        secondary_intents = intent_res.secondary_intents

        # -------------------------------------------------------------
        # 4. Route to Required Tools by Intent
        # -------------------------------------------------------------
        sources = []
        video_result = None
        safety_result = None
        plan_result = None
        primary_answer = ""
        lang = detect_language(original_query)
        normalized_q = original_query

        if primary_intent == IntentType.DRUG_COMPARISON and len(entities.medications) >= 2:
            # Dual separate retrieval for Drug A and Drug B
            tools_called.append("comparison_retrieval")
            med_a, med_b = entities.medications[0], entities.medications[1]
            reranked, sources, primary_answer = tool_drug_comparison_retrieval(med_a, med_b, original_query, lang)

        elif primary_intent == IntentType.MEDICATION_PLAN_REQUEST:
            # Medication Plan Request Flow
            tools_called.append("patient_profile")
            tools_called.append("safety_engine")
            tools_called.append("hybrid_rag")
            tools_called.append("medication_plan_generator")

            prof = tool_patient_profile(uid)
            rag_chunks, sources, primary_answer = tool_hybrid_rag(original_query, lang)

            # Evaluate safety for all mentioned medications
            safety_evals: List[SafetyResult] = []
            med_list = entities.medications if entities.medications else ["medication_review"]
            for med in med_list:
                s_eval = tool_safety_engine(med, prof, original_query, conv_id, rag_chunks)
                safety_evals.append(s_eval)
                if s_eval.requires_confirmation:
                    # Pause plan creation until relevant fact confirmed
                    trace = OrchestrationTrace(
                        intent=primary_intent.value,
                        secondary_intents=[s.value for s in secondary_intents],
                        entities=entities,
                        tools_called=tools_called,
                        confirmation_required=True,
                        safety_status=s_eval.overall_status.value
                    )
                    prompt_text = s_eval.confirmation.prompt if s_eval.confirmation else "يرجى تأكيد حالتك الصحية أولاً."
                    return OrchestrationResult(
                        query=original_query,
                        normalized_query=normalized_q,
                        language_detected=lang,
                        answer=prompt_text,
                        sources=sources,
                        requires_confirmation=True,
                        confirmation=s_eval.confirmation,
                        trace=trace
                    )

            plan_result = tool_medication_plan_generator(
                user_id=uid,
                medications=med_list,
                patient_profile=prof,
                safety_evaluations=safety_evals,
                evidence_chunks=rag_chunks,
                plan_title=f"خطة دوائية: {original_query[:40]}"
            )
            safety_result = safety_evals[0] if safety_evals else None

        elif primary_intent in (IntentType.MEDICATION_SAFETY, IntentType.DRUG_INTERACTION):
            # Personalized Medication Safety / DDI Flow
            tools_called.append("medication_resolver")
            tools_called.append("patient_profile")
            tools_called.append("safety_engine")
            tools_called.append("hybrid_rag")

            prof = tool_patient_profile(uid)
            rag_chunks, sources, primary_answer = tool_hybrid_rag(original_query, lang)

            safety_eval = None
            for med in entities.medications:
                eval_res = tool_safety_engine(med, prof, original_query, conv_id, rag_chunks)
                if eval_res.requires_confirmation:
                    safety_eval = eval_res
                    break
                if eval_res.overall_status in (SafetyStatus.CONTRAINDICATED, SafetyStatus.WARNING, SafetyStatus.CAUTION):
                    safety_eval = eval_res
                    break
                if not safety_eval:
                    safety_eval = eval_res

            # If multiple medications mentioned in query, also check pairwise DDI between them
            if len(entities.medications) >= 2 and (not safety_eval or safety_eval.overall_status == SafetyStatus.INSUFFICIENT_EVIDENCE):
                from app.safety.drug_drug_checker import check_drug_drug
                from app.safety.models import PatientMedication
                temp_meds = [PatientMedication(id="temp", user_id=uid, generic_name=m, confirmed=True) for m in entities.medications[1:]]
                pair_checks = check_drug_drug(entities.medications[0], temp_meds)
                if pair_checks:
                    from app.safety.safety_engine import build_xai_explanation
                    safety_eval = SafetyResult(
                        medication=entities.medications[0],
                        overall_status=pair_checks[0].status,
                        summary=f"تداخل دوائي موثق ومؤكد: {pair_checks[0].reason}",
                        checks=pair_checks,
                        xai=build_xai_explanation(pair_checks[0].status, pair_checks)
                    )

            if safety_eval:
                if safety_eval.requires_confirmation:
                    trace = OrchestrationTrace(
                        intent=primary_intent.value,
                        secondary_intents=[s.value for s in secondary_intents],
                        entities=entities,
                        tools_called=tools_called,
                        confirmation_required=True,
                        safety_status=safety_eval.overall_status.value
                    )
                    prompt_text = safety_eval.confirmation.prompt if safety_eval.confirmation else "يرجى تأكيد حالتك الصحية أولاً."
                    return OrchestrationResult(
                        query=original_query,
                        normalized_query=normalized_q,
                        language_detected=lang,
                        answer=prompt_text,
                        sources=sources,
                        requires_confirmation=True,
                        confirmation=safety_eval.confirmation,
                        trace=trace
                    )
                safety_result = safety_eval

        elif primary_intent == IntentType.DEVICE_USAGE:
            # Device Usage Flow -> Match Video + Inhaler check
            tools_called.append("verified_video")
            tools_called.append("hybrid_rag")

            rag_chunks, sources, primary_answer = tool_hybrid_rag(original_query, lang)
            video_result = tool_verified_video(original_query)

        elif primary_intent == IntentType.SYMPTOM_QUESTION:
            # Symptom Guidance Flow (No diagnosis fabrication)
            tools_called.append("hybrid_rag")
            rag_chunks, sources, primary_answer = tool_hybrid_rag(original_query, lang)

        else:
            # General Medication / Health Question (Zero patient profile interference)
            tools_called.append("hybrid_rag")
            rag_chunks, sources, primary_answer = tool_hybrid_rag(original_query, lang)

        # -------------------------------------------------------------
        # 5. Fallback Video Check if Device Mentioned
        # -------------------------------------------------------------
        if not video_result and entities.devices:
            tools_called.append("verified_video")
            video_result = tool_verified_video(original_query)

        # -------------------------------------------------------------
        # 6. Compose Final User-Facing Response
        # -------------------------------------------------------------
        final_answer = compose_final_response(
            primary_answer=primary_answer,
            safety_result=safety_result,
            video_result=video_result,
            plan_result=plan_result
        )

        # 7. Check for Abstention / Insufficient Evidence Logging
        if is_insufficient_evidence(final_answer):
            log_unanswered_query(
                original_query=original_query,
                normalized_query=normalized_q,
                language_detected=lang,
                user_id=uid,
                conversation_id=conv_id,
                top_sources=sources,
                reason="insufficient_evidence"
            )

        # 8. Construct Trace
        trace = OrchestrationTrace(
            intent=primary_intent.value,
            secondary_intents=[s.value for s in secondary_intents],
            entities=entities,
            tools_called=tools_called,
            confirmation_required=False,
            safety_status=safety_result.overall_status.value if safety_result else None,
            video_checked="verified_video" in tools_called,
            plan_generated=plan_result is not None
        )

        # 9. Persist Interaction
        cls._persist_interaction(conv_id, uid, original_query, final_answer, input_type, sources)

        return OrchestrationResult(
            query=original_query,
            normalized_query=normalized_q,
            language_detected=lang,
            answer=final_answer,
            sources=sources,
            video=video_result,
            safety=safety_result,
            plan=plan_result,
            trace=trace
        )

    @classmethod
    def _persist_interaction(cls, conv_id: str, user_id: str, query: str, answer: str, input_type: str, sources: List[Any]):
        """Persists user and assistant messages to database."""
        if conv_id and user_id:
            save_chat_message(
                conversation_id=conv_id,
                user_id=user_id,
                role="user",
                content=query,
                input_type=input_type or "text"
            )
            save_chat_message(
                conversation_id=conv_id,
                user_id=user_id,
                role="assistant",
                content=answer,
                input_type="text",
                sources=sources
            )
