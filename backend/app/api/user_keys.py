from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from google import genai

from app.config import settings
from app.auth.supabase_auth import get_current_user, AuthenticatedUser
from app.database.supabase import (
    save_user_gemini_key,
    get_user_gemini_key_record,
    delete_user_gemini_key
)
from app.security.encryption import encrypt_api_key, mask_api_key

router = APIRouter(prefix="/user/keys", tags=["User API Keys"])

class KeyStatusResponse(BaseModel):
    has_key: bool
    key_hint: Optional[str] = None
    updated_at: Optional[str] = None
    fallback_allowed: bool

class SaveKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=15, max_length=120)

class SaveKeyResponse(BaseModel):
    status: str
    key_hint: str
    updated_at: str

@router.get("/gemini", response_model=KeyStatusResponse)
def get_user_gemini_key_status(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the configuration status and safe masked hint of the user's Gemini API key.
    Never exposes the plaintext or encrypted key.
    """
    record = get_user_gemini_key_record(user.id)
    if record and record.get("encrypted_key"):
        return KeyStatusResponse(
            has_key=True,
            key_hint=record.get("key_hint", "AIza...****"),
            updated_at=record.get("updated_at"),
            fallback_allowed=settings.ALLOW_PROJECT_GEMINI_FALLBACK
        )
    
    return KeyStatusResponse(
        has_key=False,
        key_hint=None,
        updated_at=None,
        fallback_allowed=settings.ALLOW_PROJECT_GEMINI_FALLBACK
    )

@router.post("/gemini", response_model=SaveKeyResponse)
def set_user_gemini_key(
    req: SaveKeyRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Validates a user-supplied Gemini API key with Google AI Studio, encrypts it securely,
    and stores it associated strictly with the authenticated user ID.
    """
    candidate_key = req.api_key.strip()
    if not candidate_key or len(candidate_key) < 15:
        raise HTTPException(status_code=400, detail="Invalid API key format. Please enter a valid Gemini API key.")

    # 1. Real validation against Google GenAI API
    try:
        test_client = genai.Client(api_key=candidate_key)
        # Fast lightweight model check
        test_client.models.get(model=settings.GEMINI_MODEL)
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "INVALID_ARGUMENT" in err_msg or "PERMISSION_DENIED" in err_msg or "400" in err_msg or "403" in err_msg:
            raise HTTPException(
                status_code=400,
                detail="فشل التحقق من مفتاح Gemini API. تأكد من نسخ المفتاح الصحيح من Google AI Studio."
            )
        # If rate limit or temporary network issue on Google's end during validation, accept format with warning
        print(f"[Warning during Gemini key validation] {e}")

    # 2. Encrypt key before database storage
    try:
        encrypted_token = encrypt_api_key(candidate_key)
        hint = mask_api_key(candidate_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to encrypt API key: {e}")

    # 3. Store encrypted token in database under authenticated user_id
    success = save_user_gemini_key(user_id=user.id, encrypted_key=encrypted_token, key_hint=hint)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save API key to database.")

    return SaveKeyResponse(
        status="valid",
        key_hint=hint,
        updated_at=datetime.now().isoformat()
    )

@router.delete("/gemini")
def remove_user_gemini_key(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Deletes the configured Gemini API key for the authenticated user.
    """
    success = delete_user_gemini_key(user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove API key.")
    
    return {"status": "deleted", "message": "Gemini API key successfully removed."}
