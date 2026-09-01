import os
import json
import re
from google import genai
from google.genai import types
from app.config import settings

def normalize_mime_type(mime_type: str) -> str:
    """Normalizes browser mime type string (e.g. 'audio/webm;codecs=opus' -> 'audio/webm')."""
    if not mime_type:
        return "audio/webm"
    mime_base = mime_type.split(";")[0].strip().lower()
    if mime_base in ("audio/webm", "video/webm"):
        return "audio/webm"
    if mime_base in ("audio/ogg", "application/ogg"):
        return "audio/ogg"
    if mime_base in ("audio/wav", "audio/x-wav", "audio/wave"):
        return "audio/wav"
    if mime_base in ("audio/mp4", "audio/m4a", "audio/x-m4a", "video/mp4"):
        return "audio/mp4"
    if mime_base in ("audio/mp3", "audio/mpeg"):
        return "audio/mp3"
    return mime_base

from typing import Optional

def transcribe_audio_bytes(
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    api_key: Optional[str] = None
) -> dict:
    """
    Transcribes spoken audio bytes using Gemini multimodal audio capabilities.
    Smartly detects language (Egyptian Arabic, Standard Arabic, English, or mixed bilingual speech).
    Supports user-supplied BYOK Gemini API key.
    """
    effective_key = (api_key or "").strip()
    if not effective_key:
        if settings.ALLOW_PROJECT_GEMINI_FALLBACK:
            effective_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        else:
            effective_key = os.environ.get("GEMINI_API_KEY", "")

    if not effective_key:
        print("[Warning] No active Gemini API key configured for voice transcription.")
        return {
            "transcript": "",
            "language": "ar",
            "language_label": "عربي",
            "confidence": 0.0,
            "success": False,
            "error": "Gemini API key is required. Please configure your key in Settings."
        }

    clean_mime = normalize_mime_type(mime_type)
    client = genai.Client(api_key=effective_key)

    prompt = """You are an expert multilingual medical speech-to-text transcriber for Tamargi.ai.
Your task:
1. Listen carefully to the user's spoken audio.
2. Transcribe the spoken words accurately into text.
3. Accurately preserve medical, pharmaceutical, device, and symptom terminology (e.g. Paracetamol, Ibuprofen, Anidulafungin, Ventolin, Inhaler, Insulin pen, بخاخ, قلم أنسولين).
4. Preserve the speaker's dialect and phrasing (Egyptian Arabic, Modern Standard Arabic, or English) exactly as spoken without summarizing or translating.
5. Detect the spoken language accurately:
   - "ar": Spoken in Arabic / Egyptian Arabic.
   - "en": Spoken in English.
   - "mixed": Spoken in mixed Arabic and English (medical code-switching, e.g. "ايه الـ side effects بتاعة الباراسيتامول؟").

Respond in valid JSON format:
{
  "transcript": "<exact transcribed text, or empty if silence/unintelligible>",
  "language": "ar" | "en" | "mixed",
  "language_label": "العربية" | "English" | "مختلط (عربي / English)",
  "confidence": 0.95
}
Output only JSON."""

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=clean_mime
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )

        resp_text = response.text.strip() if response.text else ""
        
        # Clean potential markdown fences
        if resp_text.startswith("```"):
            resp_text = re.sub(r"^```(?:json)?\s*", "", resp_text)
            resp_text = re.sub(r"\s*```$", "", resp_text)

        parsed = json.loads(resp_text)
        transcript = parsed.get("transcript", "").strip()
        lang = parsed.get("language", "ar").strip().lower()
        if lang not in ("ar", "en", "mixed"):
            lang = "ar" if re.search(r"[\u0600-\u06FF]", transcript) else "en"

        label = parsed.get("language_label")
        if not label:
            label = "العربية" if lang == "ar" else ("English" if lang == "en" else "مختلط (عربي / English)")

        confidence = float(parsed.get("confidence", 0.9))

        return {
            "transcript": transcript,
            "language": lang,
            "language_label": label,
            "confidence": confidence,
            "success": bool(transcript)
        }

    except Exception as e:
        print(f"[Error] Audio transcription failed: {e}")
        return {
            "transcript": "",
            "language": "ar",
            "language_label": "عربي",
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }
