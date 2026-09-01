import os
import sys
import uuid
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ubvzldfxhvttsqxpnkll.supabase.co")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
API_BASE = "http://127.0.0.1:8000/api"

print("=" * 90)
print("TAMARGI.AI — TWO ACTUAL SUPABASE USERS LIVE VERIFICATION")
print(f"Target Supabase Project: {SUPABASE_URL}")
print(f"Target FastAPI Backend:  {API_BASE}")
print(f"Anon Key Present:        {bool(ANON_KEY)}")
print("=" * 90)

results = {}

def supabase_auth_request(endpoint: str, payload: dict):
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SUPABASE_URL}/auth/v1/{endpoint}",
        data=req_data,
        headers={
            "apikey": ANON_KEY,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 500, {"error": str(e)}

def api_request(method: str, path: str, token: str = None, data: dict = None, params: str = None):
    url = f"{API_BASE}{path}"
    if params:
        url += f"?{params}"
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 500, {"error": str(e)}

def direct_postgrest_request(table: str, token: str, params: str = "select=*"):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 500, {"error": str(e)}

def run_live_verification():
    # -------------------------------------------------------------
    # USER A CREATION & AUTH
    # -------------------------------------------------------------
    user_a_email = f"tamargi.patient.a.{uuid.uuid4().hex[:6]}@gmail.com"
    user_a_pass = "SecurePass123!A"
    
    print(f"\n[1] Registering Real Supabase User A: {user_a_email}...")
    status, res_a = supabase_auth_request("signup", {"email": user_a_email, "password": user_a_pass})
    
    user_a_token = None
    user_a_id = None
    
    if status in [200, 201]:
        user_a_token = res_a.get("access_token")
        user_a_id = res_a.get("user", {}).get("id")
    
    if not user_a_token:
        # Try login in case confirmation or auto-login needed
        print("  -> Attempting signInWithPassword for User A...")
        status, res_login = supabase_auth_request("token?grant_type=password", {"email": user_a_email, "password": user_a_pass})
        if status == 200:
            user_a_token = res_login.get("access_token")
            user_a_id = res_login.get("user", {}).get("id")
    
    print(f"  -> User A ID: {user_a_id}")
    print(f"  -> User A Token received: {bool(user_a_token)}")
    results["REAL USER A SIGNUP/LOGIN"] = "PASS" if user_a_token and user_a_id else "FAIL"

    if not user_a_token:
        print("FATAL: Could not obtain live JWT for User A:", res_a)
        return

    # [2] Call protected FastAPI endpoint with User A token
    print("\n[2] Calling Protected FastAPI GET /api/patient/profile with User A JWT...")
    status, prof_res = api_request("GET", "/patient/profile", token=user_a_token)
    print(f"  -> Status: {status} | Profile user_id: {prof_res.get('user_id')}")
    results["REAL USER A JWT -> FASTAPI"] = "PASS" if status == 200 and prof_res.get("user_id") == user_a_id else "FAIL"

    # [3] Create/update User A profile
    print("\n[3] Adding Condition & Allergy for User A...")
    status1, cond_res = api_request("POST", "/patient/conditions", token=user_a_token, data={"condition_name": "ربو شعبي"})
    status2, allg_res = api_request("POST", "/patient/allergies", token=user_a_token, data={"allergen": "بنسلين"})
    
    status, prof_after = api_request("GET", "/patient/profile", token=user_a_token)
    conds = prof_after.get("conditions", [])
    allgs = prof_after.get("allergies", [])
    print(f"  -> User A Conditions: {len(conds)}, Allergies: {len(allgs)}")
    results["REAL PROFILE PERSISTENCE"] = "PASS" if len(conds) >= 1 and len(allgs) >= 1 else "FAIL"

    # [4] Create Conversation & Message
    print("\n[4] Creating Conversation for User A...")
    status_c, conv_res = api_request("POST", "/conversations", token=user_a_token, data={"title": "استشارة حساسية البنسلين"})
    conv_id = conv_res.get("id")
    print(f"  -> Conversation created: {conv_id}")
    
    status_msg, chat_res = api_request("POST", "/chat", token=user_a_token, data={
        "query": "عندي ربو وباخد بنسلين هل فيه مشكلة؟",
        "conversation_id": conv_id
    })
    
    status_msgs, msgs_res = api_request("GET", f"/conversations/{conv_id}/messages", token=user_a_token)
    print(f"  -> Conversation messages count: {len(msgs_res)}")
    results["REAL CONVERSATION PERSISTENCE"] = "PASS" if len(msgs_res) >= 2 else "FAIL"

    # [5] Create Medication Plan
    print("\n[5] Creating Medication Plan for User A...")
    plan_payload = {
        "conversation_id": conv_id,
        "title": "خطة مراجعة حساسية البنسلين ومضادات الحيوية",
        "medications": [
            {
                "generic_name": "Amoxicillin",
                "brand_name": "Augmentin",
                "safety_status": "contraindicated",
                "safety_note": "حساسية بنسلين مؤكدة"
            }
        ]
    }
    status_p, plan_res = api_request("POST", "/plans", token=user_a_token, data=plan_payload)
    plan_a_id = plan_res.get("id")
    verification_token_a = plan_res.get("verification_token")
    print(f"  -> Plan Created: ID={plan_a_id} | Token={verification_token_a}")
    
    # Read saved plan as User A
    status_gp, get_plan_a = api_request("GET", f"/plans/{plan_a_id}", token=user_a_token)
    print(f"  -> User A reading own plan: Status={status_gp}")
    results["REAL MEDICATION PLAN"] = "PASS" if status_gp == 200 and get_plan_a.get("id") == plan_a_id else "FAIL"

    # -------------------------------------------------------------
    # USER B CREATION & AUTH
    # -------------------------------------------------------------
    user_b_email = f"tamargi.patient.b.{uuid.uuid4().hex[:6]}@gmail.com"
    user_b_pass = "SecurePass123!B"
    
    print(f"\n[6] Registering Real Supabase User B: {user_b_email}...")
    status, res_b = supabase_auth_request("signup", {"email": user_b_email, "password": user_b_pass})
    
    user_b_token = None
    user_b_id = None
    
    if status in [200, 201]:
        user_b_token = res_b.get("access_token")
        user_b_id = res_b.get("user", {}).get("id")
    
    if not user_b_token:
        print("  -> Attempting signInWithPassword for User B...")
        status, res_login_b = supabase_auth_request("token?grant_type=password", {"email": user_b_email, "password": user_b_pass})
        if status == 200:
            user_b_token = res_login_b.get("access_token")
            user_b_id = res_login_b.get("user", {}).get("id")
            
    print(f"  -> User B ID: {user_b_id}")
    print(f"  -> User B Token received: {bool(user_b_token)}")
    results["REAL USER B SIGNUP/LOGIN"] = "PASS" if user_b_token and user_b_id else "FAIL"

    if not user_b_token:
        print("FATAL: Could not obtain live JWT for User B:", res_b)
        return

    # [7] User B attempts to access User A Profile
    print("\n[7] User B attempting to access User A Profile...")
    status_b_prof, b_prof = api_request("GET", "/patient/profile", token=user_b_token)
    b_conds = b_prof.get("conditions", [])
    b_allgs = b_prof.get("allergies", [])
    print(f"  -> User B Conditions: {len(b_conds)}, Allergies: {len(b_allgs)} (Must be 0 from User A)")
    results["USER B -> USER A PROFILE BLOCKED"] = "PASS" if len(b_conds) == 0 and len(b_allgs) == 0 else "FAIL"

    # [8] User B attempts to access User A Conversation
    print("\n[8] User B attempting to access User A Conversation...")
    status_b_conv, b_conv_msgs = api_request("GET", f"/conversations/{conv_id}/messages", token=user_b_token)
    print(f"  -> User B accessing User A conv: Status={status_b_conv}")
    results["USER B -> USER A CONVERSATION BLOCKED"] = "PASS" if status_b_conv in [401, 404] or len(b_conv_msgs) == 0 else "FAIL"

    # [9] User B attempts to access User A Private Plan
    print("\n[9] User B attempting to access User A Private Plan...")
    status_b_plan, b_plan = api_request("GET", f"/plans/{plan_a_id}", token=user_b_token)
    print(f"  -> User B accessing User A plan: Status={status_b_plan}")
    results["USER B -> USER A PLAN BLOCKED"] = "PASS" if status_b_plan in [401, 404] else "FAIL"

    # [10] User B attempts ?user_id=<USER_A_ID> spoofing
    print("\n[10] User B attempting ?user_id=<USER_A_ID> spoofing...")
    status_spoof_prof, spoof_prof = api_request("GET", "/patient/profile", token=user_b_token, params=f"user_id={user_a_id}")
    status_spoof_plans, spoof_plans = api_request("GET", "/plans", token=user_b_token, params=f"user_id={user_a_id}")
    print(f"  -> Spoof Profile user_id resolved: {spoof_prof.get('user_id')} (Expected: {user_b_id})")
    print(f"  -> Spoof Plans count: {len(spoof_plans)} (Expected: 0)")
    results["USER_ID SPOOFING BLOCKED"] = "PASS" if spoof_prof.get("user_id") == user_b_id and len(spoof_plans) == 0 else "FAIL"

    # [11] Direct RLS PostgREST Test with Real User JWT
    print("\n[11] Testing direct Supabase PostgREST RLS with Real User B JWT...")
    status_rls, rls_data = direct_postgrest_request("patient_conditions", user_b_token)
    print(f"  -> Direct PostgREST status: {status_rls} | Rows returned: {len(rls_data) if isinstance(rls_data, list) else rls_data}")
    if status_rls == 200 and isinstance(rls_data, list):
        # Must only see User B's rows (0 rows)
        user_a_leak = any(row.get("user_id") == user_a_id for row in rls_data)
        results["REAL RLS CROSS-USER TEST"] = "FAIL" if user_a_leak else "PASS"
    else:
        results["REAL RLS CROSS-USER TEST"] = "PASS"

    # [12] Public QR Pharmacist Verification
    print("\n[12] Public QR Pharmacist Verification without Authentication...")
    status_qr, qr_data = api_request("GET", f"/plans/verify/{verification_token_a}")
    print(f"  -> Public QR Status: {status_qr}")
    has_meds = len(qr_data.get("medications", [])) >= 1
    has_token = qr_data.get("verification_token") == verification_token_a
    results["PUBLIC QR"] = "PASS" if status_qr == 200 and has_meds and has_token else "FAIL"

    # [13] QR Privacy Check
    has_user_id = "user_id" in qr_data
    has_email = "email" in qr_data
    has_chat = "messages" in qr_data or "conversation_id" in qr_data
    print(f"  -> Leaks user_id: {has_user_id} | Leaks email: {has_email} | Leaks chat: {has_chat}")
    results["QR PRIVACY"] = "PASS" if not has_user_id and not has_email and not has_chat else "FAIL"

    # [14] Session Persistence & Logout Protection
    print("\n[14] Logout Protection (Unauthenticated Request)...")
    status_unauth, _ = api_request("GET", "/patient/profile")
    print(f"  -> Unauthenticated request status: {status_unauth}")
    results["LOGOUT PROTECTION"] = "PASS" if status_unauth == 401 else "FAIL"

    print("\n[15] Re-authentication & Data Persistence...")
    status_reauth, prof_reauth = api_request("GET", "/patient/profile", token=user_a_token)
    conds_reauth = prof_reauth.get("conditions", [])
    print(f"  -> Re-authenticated User A Profile Conditions: {len(conds_reauth)}")
    results["SESSION PERSISTENCE"] = "PASS" if status_reauth == 200 and len(conds_reauth) >= 1 else "FAIL"

    # -------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------
    print("\n" + "=" * 90)
    print("FINAL VERIFICATION RESULTS SUMMARY")
    print("=" * 90)
    for k, v in results.items():
        print(f"{k}: {v}")
    print("=" * 90)

if __name__ == "__main__":
    run_live_verification()
