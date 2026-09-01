from typing import Tuple, Optional
from app.config import settings
from app.database.supabase import get_user_gemini_key_record
from app.security.encryption import decrypt_api_key

def resolve_user_gemini_api_key(user_id: Optional[str]) -> Tuple[Optional[str], str]:
    """
    Resolves the authoritative Gemini API key for a request.
    
    Resolution hierarchy:
    1. Authenticated user's encrypted BYOK key stored in user_api_keys (decrypted in-memory).
    2. Server project fallback key (settings.GEMINI_API_KEY) ONLY if ALLOW_PROJECT_GEMINI_FALLBACK is True.
    3. None (Missing key).
    
    Returns:
        (api_key, source_type) where source_type is 'user_byok' | 'project_fallback' | 'missing_key'
    """
    if user_id and user_id not in ("guest_user", "anonymous"):
        try:
            record = get_user_gemini_key_record(user_id)
            if record and record.get("encrypted_key"):
                decrypted = decrypt_api_key(record["encrypted_key"])
                if decrypted and decrypted.strip():
                    return decrypted.strip(), "user_byok"
        except Exception as e:
            print(f"[KeyResolver] Failed to resolve user BYOK key: {e}")

    # Fallback to server project key if explicitly enabled
    if settings.ALLOW_PROJECT_GEMINI_FALLBACK and settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY, "project_fallback"

    return None, "missing_key"
