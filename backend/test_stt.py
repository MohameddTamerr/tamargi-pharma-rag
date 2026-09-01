import wave
import io
import json
from google import genai
from google.genai import types
from app.config import settings

# Create a tiny 1-second silent WAV file in memory
buf = io.BytesIO()
with wave.open(buf, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(16000)
    wav_file.writeframes(b'\x00\x00' * 16000)
audio_bytes = buf.getvalue()

client = genai.Client(api_key=settings.GEMINI_API_KEY)
prompt = """You are an expert multilingual medical speech-to-text transcriber for Tamargi.ai.
Listen to the audio and transcribe the user's speech accurately.
Preserve medical and pharmaceutical terminology accurately (such as drug names, dosages, side effects).
Detect if the spoken language is:
- 'ar' (Egyptian Arabic or Standard Arabic)
- 'en' (English)
- 'mixed' (Mixed Arabic and English)

Respond in valid JSON format:
{
  "transcript": "<exact text spoken, or empty if silence/unclear>",
  "language": "ar" | "en" | "mixed",
  "language_name": "Arabic" | "English" | "Mixed (Arabic/English)",
  "confidence": 0.0 to 1.0
}
Output only JSON."""

try:
    res = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav'),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            temperature=0.1
        )
    )
    print('JSON output:', res.text)
except Exception as e:
    print('Error:', e)
