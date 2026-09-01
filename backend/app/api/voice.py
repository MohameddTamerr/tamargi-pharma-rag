import base64
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from pydantic import BaseModel
from typing import Optional
from app.voice.speech_to_text import transcribe_audio_bytes
from app.voice.text_to_speech import synthesize_speech
from app.language.detector import detect_language
from app.auth.supabase_auth import get_optional_user, AuthenticatedUser
from app.security.rate_limiter import check_user_rate_limit
from app.security.key_resolver import resolve_user_gemini_api_key

router = APIRouter()

class VoiceBase64Request(BaseModel):
    audio_base64: str
    mime_type: Optional[str] = "audio/webm"

class LanguageDetectRequest(BaseModel):
    text: str

@router.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """
    Transcribes audio file upload (WebM, WAV, OGG, MP4) using Gemini multimodal audio.
    Smartly detects whether spoken query is Arabic (Egyptian/MSA), English, or Mixed.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No audio file uploaded.")
    
    user_id = user.id if user else "guest_user"
    check_user_rate_limit(user_id, endpoint="voice")
    user_gemini_key, _ = resolve_user_gemini_api_key(user_id)

    try:
        audio_bytes = await file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

        mime_type = file.content_type or "audio/webm"
        result = transcribe_audio_bytes(audio_bytes, mime_type=mime_type, api_key=user_gemini_key)
        result["filename"] = file.filename
        return result
    except Exception as e:
        print(f"[Error in /voice/transcribe] {e}")
        return {
            "transcript": "",
            "language": "ar",
            "language_label": "عربي",
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }

@router.post("/voice/transcribe-base64")
async def transcribe_voice_base64(
    req: VoiceBase64Request,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """
    Transcribes base64 encoded audio payload.
    """
    if not req.audio_base64:
        raise HTTPException(status_code=400, detail="Audio base64 data required.")
    
    user_id = user.id if user else "guest_user"
    check_user_rate_limit(user_id, endpoint="voice")
    user_gemini_key, _ = resolve_user_gemini_api_key(user_id)

    try:
        # Strip potential data URL prefix if present
        raw_b64 = req.audio_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]

        audio_bytes = base64.b64decode(raw_b64)
        mime_type = req.mime_type or "audio/webm"
        result = transcribe_audio_bytes(audio_bytes, mime_type=mime_type, api_key=user_gemini_key)
        return result
    except Exception as e:
        print(f"[Error in /voice/transcribe-base64] {e}")
        return {
            "transcript": "",
            "language": "ar",
            "language_label": "عربي",
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }

@router.post("/voice/detect-language")
def detect_voice_language(req: LanguageDetectRequest):
    """
    Detects language of a text snippet (Egyptian Arabic, Standard Arabic, or English).
    """
    lang = detect_language(req.text)
    label_map = {
        "egyptian": "مصري (Egyptian Arabic)",
        "ar": "عربي (Arabic)",
        "en": "English"
    }
    return {
        "text": req.text,
        "language": lang,
        "language_label": label_map.get(lang, "عربي")
    }

@router.post("/voice/synthesize")
def synthesize_voice(text: str, language: str = "ar"):
    speech_meta = synthesize_speech(text, language=language)
    return speech_meta
