import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

def _derive_fernet_key(secret: str) -> bytes:
    """
    Derives a standard 32-byte URL-safe base64-encoded key suitable for Fernet
    from an arbitrary input passphrase or secret string using SHA-256.
    """
    sha256_digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(sha256_digest)

def get_fernet_cipher(secret: Optional[str] = None) -> Fernet:
    """Returns a Fernet cipher initialized with the derived encryption key."""
    raw_secret = secret or settings.BYOK_ENCRYPTION_KEY or "tamargi-pharma-rag-default-encryption-secret-key-32b"
    key = _derive_fernet_key(raw_secret)
    return Fernet(key)

def encrypt_api_key(plaintext_key: str, secret: Optional[str] = None) -> str:
    """
    Encrypts a user-supplied plaintext API key into an authenticated ciphertext string.
    Never stores or returns plaintext.
    """
    if not plaintext_key or not plaintext_key.strip():
        raise ValueError("Cannot encrypt an empty API key.")
    
    clean_key = plaintext_key.strip()
    cipher = get_fernet_cipher(secret)
    encrypted_bytes = cipher.encrypt(clean_key.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_api_key(encrypted_token: str, secret: Optional[str] = None) -> str:
    """
    Decrypts an encrypted API key ciphertext into plaintext for runtime client instantiation.
    Raises ValueError if the token is invalid or corrupted.
    """
    if not encrypted_token or not encrypted_token.strip():
        raise ValueError("Cannot decrypt an empty ciphertext token.")
    
    cipher = get_fernet_cipher(secret)
    try:
        decrypted_bytes = cipher.decrypt(encrypted_token.strip().encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise ValueError("Decryption failed: invalid or corrupted API key ciphertext.")

def mask_api_key(key: str) -> str:
    """
    Returns a safe masked hint of the API key for display in settings (e.g., 'AIzaSy...****' or 'AIza...4xyz').
    Full key is never returned to the frontend.
    """
    if not key or len(key) < 8:
        return "********"
    
    prefix = key[:6] if len(key) >= 12 else key[:4]
    suffix = key[-4:] if len(key) >= 12 else ""
    if suffix:
        return f"{prefix}...{suffix}"
    return f"{prefix}..."
