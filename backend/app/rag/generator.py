import os
import time
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.rag.grounding import STRICT_GROUNDING_PROMPT, build_evidence

def get_genai_client(api_key: Optional[str] = None):
    effective_key = (api_key or "").strip()
    if not effective_key:
        if settings.ALLOW_PROJECT_GEMINI_FALLBACK:
            effective_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        else:
            effective_key = os.environ.get("GEMINI_API_KEY", "")
    if not effective_key:
        print("[WARNING] No active Gemini API key provided.")
    return genai.Client(api_key=effective_key)

def generate_grounded_answer(
    query: str,
    results: list[dict],
    user_language: str = "en",
    api_key: Optional[str] = None
) -> str:
    """
    Sends user question and formatted retrieved evidence to Gemini with strict grounding prompt.
    Supports user-provided BYOK Gemini API key.
    """
    evidence = build_evidence(results)

    lang_instruction = "Respond entirely in English." if user_language == "en" else "Respond in Arabic (or Egyptian dialect) matching the user."
    prompt = (
        f"Target Response Language: {lang_instruction}\n\n"
        f"Question:\n{query}\n\n"
        f"Retrieved evidence:\n{evidence}"
    )

    effective_key = (api_key or "").strip()
    if not effective_key:
        if settings.ALLOW_PROJECT_GEMINI_FALLBACK:
            effective_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        else:
            effective_key = os.environ.get("GEMINI_API_KEY", "")

    if not effective_key:
        if user_language in ("ar", "egyptian"):
            return "يرجى إضافة مفتاح Gemini API الخاص بك من صفحة الملف الطبي والإعدادات لتفعيل الإجابات الذكية المدعومة بالأدلة."
        return "Please configure your Gemini API key in Settings to enable AI-grounded responses."

    client = get_genai_client(api_key=effective_key)

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=STRICT_GROUNDING_PROMPT,
                    temperature=0.1
                )
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                time.sleep(5 * (attempt + 1))
            else:
                time.sleep(2)

            if attempt == 2:
                print(f"[Warning] Gemini API generation fallback triggered: {e}")
                if results:
                    lead_chunk = results[0]
                    lead_text = lead_chunk.get('text', '')[:300]
                    lead_src = lead_chunk.get('file', 'EDA Monograph')
                    lead_page = lead_chunk.get('page', '')
                    if user_language in ('ar', 'egyptian'):
                        return f"بناءً على الأدلة المعتمدة في {lead_src} (صفحة {lead_page}):\n{lead_text}"
                    else:
                        return f"Based on evidence from {lead_src} (page {lead_page}):\n{lead_text}"
                return "No sufficient evidence found in verified monographs."
