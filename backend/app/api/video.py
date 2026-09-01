from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.video.video_matcher import get_verified_video, APPROVED_USAGE_TOPICS

router = APIRouter()

class VideoLookupRequest(BaseModel):
    query_text: Optional[str] = None
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    dosage_form: Optional[str] = None
    device_name: Optional[str] = None
    usage_topic: Optional[str] = None

class VideoLookupResponse(BaseModel):
    found: bool
    reason: Optional[str] = None
    title: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    usage_topic: Optional[str] = None
    device_name: Optional[str] = None
    language: Optional[str] = "ar"
    helper_prompt: Optional[str] = None

DEVICE_HELP_PROMPT = "في أنواع مختلفة من أجهزة الاستنشاق وطريقة استخدامها بتختلف. ابعتلي اسم الجهاز أو اسم الدواء المكتوب على البخاخ عشان أجيبلك فيديو الاستخدام الصحيح."

@router.post("/lookup", response_model=VideoLookupResponse)
def lookup_video(req: VideoLookupRequest):
    """
    Looks up verified medical instructional video with strict device matching hierarchy.
    """
    res = get_verified_video(
        generic_name=req.generic_name,
        brand_name=req.brand_name,
        dosage_form=req.dosage_form,
        device_name=req.device_name,
        usage_topic=req.usage_topic,
        query_text=req.query_text
    )

    if res.get("found"):
        return VideoLookupResponse(
            found=True,
            title=res.get("title"),
            video_url=res.get("video_url"),
            thumbnail_url=res.get("thumbnail_url"),
            source_name=res.get("source_name"),
            source_url=res.get("source_url"),
            usage_topic=res.get("usage_topic"),
            device_name=res.get("device_name"),
            language=res.get("language", "ar")
        )

    reason = res.get("reason", "no_verified_video")
    helper = DEVICE_HELP_PROMPT if reason in ("exact_device_unknown", "brand_required") else None

    return VideoLookupResponse(
        found=False,
        reason=reason,
        helper_prompt=helper
    )

@router.get("/topics", response_model=List[str])
def list_topics():
    """Lists all approved instructional usage topics."""
    return APPROVED_USAGE_TOPICS
