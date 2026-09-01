from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.auth.supabase_auth import get_optional_user, AuthenticatedUser
from app.safety.models import SafetyResult, ConfirmationContext
from app.orchestrator.orchestrator import TamargiOrchestrator, OrchestrationTrace

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = "default_conv"
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    input_type: Optional[str] = "text"

class SourceItem(BaseModel):
    evidenceId: str
    fileName: str
    pageNumber: int
    chunkId: Optional[int] = None
    rank: int
    score: float
    excerpt: str

class VideoItem(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    medication_or_device: Optional[str] = None
    category: Optional[str] = None
    dosage_form: Optional[str] = None
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    usage_topic: Optional[str] = None
    language: Optional[str] = "en"
    video_url: str
    thumbnail_url: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None

class ChatResponse(BaseModel):
    query: str
    normalized_query: str
    language_detected: str
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
    video: Optional[VideoItem] = None
    conversation_id: Optional[str] = None
    safety: Optional[SafetyResult] = None
    requires_confirmation: bool = False
    confirmation: Optional[ConfirmationContext] = None
    plan: Optional[Dict[str, Any]] = None
    trace: Optional[OrchestrationTrace] = None

@router.post("/chat", response_model=ChatResponse)
def handle_chat(
    request: ChatRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    original_query = request.query.strip()
    # Derive authoritative user ID from verified Supabase token if present, else guest
    authoritative_user_id = user.id if user else (request.user_id or "guest_user")
    conv_id = request.conversation_id or "default_conv"
    input_type = request.input_type or "text"

    # Route through Central Agentic Orchestrator
    result = TamargiOrchestrator.orchestrate(
        query=original_query,
        conversation_id=conv_id,
        user_id=authoritative_user_id,
        input_type=input_type
    )

    formatted_sources = [
        SourceItem(
            evidenceId=s.get("evidenceId", f"E{idx+1}"),
            fileName=s.get("fileName", ""),
            pageNumber=int(s.get("pageNumber", 1)),
            chunkId=s.get("chunkId"),
            rank=int(s.get("rank", idx+1)),
            score=float(s.get("score", 0.0)),
            excerpt=s.get("excerpt", "")
        )
        for idx, s in enumerate(result.sources)
    ]

    video_item = VideoItem(**result.video) if result.video and result.video.get("found") else None

    return ChatResponse(
        query=result.query,
        normalized_query=result.normalized_query,
        language_detected=result.language_detected,
        answer=result.answer,
        sources=formatted_sources,
        video=video_item,
        conversation_id=conv_id,
        safety=result.safety,
        requires_confirmation=result.requires_confirmation,
        confirmation=result.confirmation,
        plan=result.plan,
        trace=result.trace
    )
