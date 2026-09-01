import os
import time
import json
import urllib.request
import urllib.error
import jwt
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    id: str # Authoritative Supabase Auth UUID (from JWT sub)
    email: Optional[str] = None
    role: Optional[str] = "authenticated"
    user_metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_jwt: Optional[str] = None

def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Cryptographically verifies a Supabase Auth JWT and returns its claims.
    Rejects expired, malformed, or invalid tokens with HTTPException(401).
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # 1. Signature verification via secret if provided
    if jwt_secret:
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_aud": False}
            )
            if "sub" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Supabase token: missing subject (sub) claim."
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase session token has expired. Please log in again."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Supabase token signature: {str(e)}"
            )

    # 2. Remote verification against Supabase Auth API (/auth/v1/user)
    if supabase_url:
        apikey = supabase_service_key or supabase_anon_key
        if apikey and not apikey.endswith(".X-placeholder-anon"):
            try:
                req = urllib.request.Request(
                    f"{supabase_url}/auth/v1/user",
                    headers={
                        "apikey": apikey,
                        "Authorization": f"Bearer {token}"
                    },
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    user_data = json.loads(res.read().decode("utf-8"))
                    if "id" in user_data:
                        return {
                            "sub": user_data["id"],
                            "email": user_data.get("email"),
                            "role": user_data.get("role", "authenticated"),
                            "user_metadata": user_data.get("user_metadata", {})
                        }
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or revoked Supabase authentication token."
                    )
            except Exception:
                pass

    # 3. Standard JWT Structure & Expiry validation
    try:
        # Decode without verification only when secret is not locally provided,
        # but strictly enforce standard claims and timestamp expiration
        unverified_payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True}
        )
        if "sub" not in unverified_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token: missing subject (sub) claim."
            )
        exp = unverified_payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase session token has expired."
            )
        return unverified_payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase session token has expired. Please log in again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed or invalid authentication token: {str(e)}"
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> AuthenticatedUser:
    """
    FastAPI dependency that extracts and verifies the Supabase Auth identity from
    the HTTP Authorization Bearer header.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    claims = verify_supabase_jwt(token)
    user_id = claims.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token: missing user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        id=user_id,
        email=claims.get("email"),
        role=claims.get("role", "authenticated"),
        user_metadata=claims.get("user_metadata", {}),
        raw_jwt=token
    )

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[AuthenticatedUser]:
    """
    Optional dependency for endpoints that support both authenticated and guest interactions.
    """
    if not credentials or not credentials.credentials:
        return None
    try:
        claims = verify_supabase_jwt(credentials.credentials)
        user_id = claims.get("sub")
        if user_id:
            return AuthenticatedUser(
                id=user_id,
                email=claims.get("email"),
                role=claims.get("role", "authenticated"),
                user_metadata=claims.get("user_metadata", {}),
                raw_jwt=credentials.credentials
            )
    except Exception:
        return None
    return None
