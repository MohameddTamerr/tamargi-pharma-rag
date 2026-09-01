import sys
import io
import os
import uuid
import time
import json
import jwt
from fastapi.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.main import app
from app.auth.supabase_auth import AuthenticatedUser, verify_supabase_jwt

client = TestClient(app)

def create_mock_supabase_jwt(user_id: str, email: str, role: str = "authenticated", expires_in: int = 3600) -> str:
    """Creates a standard Supabase Auth formatted JWT with proper claims."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "iat": now,
        "exp": now + expires_in,
        "user_metadata": {
            "full_name": f"User {user_id[:8]}"
        }
    }
    # Unsigned/raw JWT for payload testing
    return jwt.encode(payload, "secret-key", algorithm="HS256")

def run_auth_architecture_tests():
    print("=" * 90)
    print("TAMARGI.AI — AUTHORITATIVE SUPABASE AUTH & JWT VERIFICATION E2E TEST SUITE")
    print("=" * 90)

    # 1. Generate User A and User B Identities
    user_a_id = str(uuid.uuid4())
    user_a_email = "user_a_patient@example.com"
    token_a = create_mock_supabase_jwt(user_a_id, user_a_email)

    user_b_id = str(uuid.uuid4())
    user_b_email = "user_b_patient@example.com"
    token_b = create_mock_supabase_jwt(user_b_id, user_b_email)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print("\n--- 1. Testing Unauthenticated Request Rejections (HTTP 401) ---")
    res_no_auth = client.get("/api/patient/profile")
    assert res_no_auth.status_code == 401, f"Expected 401 for unauthenticated profile, got {res_no_auth.status_code}"
    print(f"GET /api/patient/profile without token: {res_no_auth.status_code} Unauthorized [PASS]")

    res_no_auth_conv = client.get("/api/conversations")
    assert res_no_auth_conv.status_code == 401, f"Expected 401 for unauthenticated convs, got {res_no_auth_conv.status_code}"
    print(f"GET /api/conversations without token: {res_no_auth_conv.status_code} Unauthorized [PASS]")

    res_no_auth_plan = client.get("/api/plans")
    assert res_no_auth_plan.status_code == 401, f"Expected 401 for unauthenticated plans, got {res_no_auth_plan.status_code}"
    print(f"GET /api/plans without token: {res_no_auth_plan.status_code} Unauthorized [PASS]")

    # 2. Test Expired JWT Rejection
    print("\n--- 2. Testing Expired Token Rejection (HTTP 401) ---")
    expired_token = create_mock_supabase_jwt(user_a_id, user_a_email, expires_in=-3600)
    res_expired = client.get("/api/patient/profile", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401, f"Expected 401 for expired token, got {res_expired.status_code}"
    print(f"GET /api/patient/profile with expired token: {res_expired.status_code} {res_expired.json().get('detail')} [PASS]")

    # 3. User A Profile Creation & Verification
    print("\n--- 3. Testing User A Profile Data Bound to JWT sub ---")
    prof_update = client.post(
        "/api/patient/profile",
        headers=headers_a,
        json={"weight_kg": 72.5, "sex": "male"}
    )
    assert prof_update.status_code == 200, f"Profile update failed: {prof_update.text}"
    assert prof_update.json()["user_id"] == user_a_id, "User ID was not bound to JWT sub!"

    # Add condition & allergy
    cond_res = client.post(
        "/api/patient/conditions",
        headers=headers_a,
        json={"condition_name": "ارتفاع ضغط الدم", "confirmed": True}
    )
    assert cond_res.status_code == 200
    assert cond_res.json()["user_id"] == user_a_id

    allergy_res = client.post(
        "/api/patient/allergies",
        headers=headers_a,
        json={"allergen": "بنسلين", "severity": "severe", "confirmed": True}
    )
    assert allergy_res.status_code == 200
    assert allergy_res.json()["user_id"] == user_a_id

    prof_a = client.get("/api/patient/profile", headers=headers_a).json()
    assert prof_a["user_id"] == user_a_id
    assert len(prof_a["conditions"]) == 1
    assert len(prof_a["allergies"]) == 1
    print(f"User A Profile Loaded: Conditions={len(prof_a['conditions'])}, Allergies={len(prof_a['allergies'])} [PASS]")

    # 4. User B Isolation Verification (Cannot access User A profile)
    print("\n--- 4. Testing User B Isolation from User A Profile ---")
    prof_b = client.get("/api/patient/profile", headers=headers_b).json()
    assert prof_b["user_id"] == user_b_id, "User B received wrong profile user_id!"
    assert len(prof_b["conditions"]) == 0, "User B leaked User A's conditions!"
    assert len(prof_b["allergies"]) == 0, "User B leaked User A's allergies!"
    print("User B Profile: 100% empty (Zero leakage from User A) [PASS]")

    # Even if User B passes ?user_id=user_a_id in query, JWT sub overrides it
    spoofed_prof = client.get(f"/api/patient/profile?user_id={user_a_id}", headers=headers_b).json()
    assert spoofed_prof["user_id"] == user_b_id, "Spoofed user_id query parameter overrode JWT sub!"
    print("User B Spoofed Query Param Attempt: Properly ignored, resolved to User B identity [PASS]")

    # 5. User A Conversation Creation
    print("\n--- 5. Testing User A Conversation Creation & Isolation ---")
    conv_res = client.post(
        "/api/conversations",
        headers=headers_a,
        json={"title": "استشارة دوائية بنسلين"}
    )
    assert conv_res.status_code == 200
    conv_a = conv_res.json()
    conv_a_id = conv_a["id"]
    assert conv_a["user_id"] == user_a_id

    user_a_convs = client.get("/api/conversations", headers=headers_a).json()
    assert len(user_a_convs) >= 1
    assert any(c["id"] == conv_a_id for c in user_a_convs)

    # User B cannot see User A conversations
    user_b_convs = client.get("/api/conversations", headers=headers_b).json()
    assert not any(c["id"] == conv_a_id for c in user_b_convs)
    print("User A Conversation Created & Isolated from User B [PASS]")

    # 6. User A Medication Plan Creation & Verification
    print("\n--- 6. Testing User A Medication Plan Creation & QR Verification ---")
    plan_res = client.post(
        "/api/plans",
        headers=headers_a,
        json={
            "title": "خطة دوائية لمراجعة الباراسيتامول",
            "patient_info": {"age": 45, "gender": "male"},
            "medications": [
                {
                    "generic_name": "Paracetamol",
                    "strength": "500mg",
                    "instructions": "قرص عند اللزوم",
                    "safety_status": "safe_no_known_issue"
                }
            ]
        }
    )
    assert plan_res.status_code == 200
    plan_a = plan_res.json()
    plan_a_id = plan_a["id"]
    token_qr = plan_a["verification_token"]
    assert plan_a["user_id"] == user_a_id
    print(f"User A Plan Created: ID={plan_a_id}, Token={token_qr} [PASS]")

    # User B cannot retrieve User A private plan
    user_b_plan_attempt = client.get(f"/api/plans/{plan_a_id}", headers=headers_b)
    assert user_b_plan_attempt.status_code == 404, f"Expected 404 for unauthorized plan access, got {user_b_plan_attempt.status_code}"
    print("User B Access to User A Private Plan: Denied (HTTP 404 Unauthorized) [PASS]")

    # 7. Public QR Verification Route (Public Exception)
    print("\n--- 7. Testing Public Pharmacist QR Verification Exception ---")
    qr_res = client.get(f"/api/plans/verify/{token_qr}")
    assert qr_res.status_code == 200, f"QR verification failed: {qr_res.text}"
    qr_data = qr_res.json()
    assert qr_data["verification_token"] == token_qr
    assert qr_data["title"] == "خطة دوائية لمراجعة الباراسيتامول"
    assert "user_id" not in qr_data, "VULNERABILITY: Public QR exposed private user_id!"
    assert "email" not in qr_data, "VULNERABILITY: Public QR exposed private email!"
    print("Public Pharmacist Verification: Accessible without auth, Sanitized & Safe [PASS]")

    # 8. Check Old Custom Auth Endpoints are Completely Removed
    print("\n--- 8. Verifying Obsolete Custom Auth Endpoints are 404 Not Found ---")
    for endpoint in ["/api/auth/login", "/api/auth/signup", "/api/auth/session", "/api/auth/logout", "/api/auth/forgot-password"]:
        res_old = client.post(endpoint, json={})
        assert res_old.status_code in [404, 405], f"Expected {endpoint} to be 404/405, got {res_old.status_code}"
        print(f"Endpoint {endpoint}: DELETED (HTTP {res_old.status_code}) [PASS]")

    print("\n" + "=" * 90)
    print("FINAL RESULT: ALL AUTHORIZATION & SUPABASE AUTH E2E TESTS PASSED (100%)")
    print("=" * 90)

if __name__ == "__main__":
    run_auth_architecture_tests()
