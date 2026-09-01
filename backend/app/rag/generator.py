import os
import time
from google import genai
from google.genai import types
from app.config import settings
from app.rag.grounding import STRICT_GROUNDING_PROMPT, build_evidence

def get_genai_client():
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def generate_grounded_answer(query: str, results: list[dict], user_language: str = "en") -> str:
    """
    Sends user question and formatted retrieved evidence to Gemini with strict grounding prompt.
    """
    evidence = build_evidence(results)

    lang_instruction = "Respond entirely in English." if user_language == "en" else "Respond in Arabic (or Egyptian dialect) matching the user."
    prompt = (
        f"Target Response Language: {lang_instruction}\n\n"
        f"Question:\n{query}\n\n"
        f"Retrieved evidence:\n{evidence}"
    )

    if not settings.GEMINI_API_KEY and "GEMINI_API_KEY" not in os.environ:
        # Safe fallback if key is missing during offline testing
        return "System Warning: GEMINI_API_KEY is not configured on the backend server."

    client = get_genai_client()

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
