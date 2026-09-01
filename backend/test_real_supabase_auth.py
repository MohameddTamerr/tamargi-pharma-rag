import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv("backend/.env")

url = os.getenv("SUPABASE_URL", "https://ubvzldfxhvttsqxpnkll.supabase.co")
anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

print("Testing Real Supabase Auth Endpoints on:", url)
print("Anon Key Configured:", bool(anon_key) and not anon_key.endswith(".X-placeholder-anon"))

def test_supabase_signup(email: str, password: str):
    req_data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/auth/v1/signup",
        data=req_data,
        headers={
            "apikey": anon_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            print("[REAL SUPABASE SIGNUP] Success:", data.get("user", {}).get("id"))
            return True, data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[REAL SUPABASE SIGNUP] HTTP {e.code}:", body)
        return False, body
    except Exception as e:
        print("[REAL SUPABASE SIGNUP] Exception:", e)
        return False, str(e)

def test_supabase_forgot_password(email: str):
    req_data = json.dumps({"email": email}).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/auth/v1/recover",
        data=req_data,
        headers={
            "apikey": anon_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            print("[REAL SUPABASE FORGOT PASSWORD] Success:", data)
            return True, data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[REAL SUPABASE FORGOT PASSWORD] HTTP {e.code}:", body)
        return False, body
    except Exception as e:
        print("[REAL SUPABASE FORGOT PASSWORD] Exception:", e)
        return False, str(e)

if __name__ == "__main__":
    test_supabase_signup("test_patient_user@example.com", "SecurePassword123!")
    test_supabase_forgot_password("test_patient_user@example.com")
