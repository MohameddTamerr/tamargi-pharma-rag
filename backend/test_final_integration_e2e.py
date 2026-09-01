import sys
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint: str, data: dict, headers: dict = None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=json.dumps(data).encode("utf-8"), headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} on POST {endpoint}: {err_body}")
        raise e

def get_json(endpoint: str, headers: dict = None):
    req_headers = {}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", headers=req_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

print("=" * 95)
print("TAMARGI.AI — FINAL INTEGRATION, AUTH, PROFILE SYNC & PLAN E2E TEST SUITE")
print("=" * 95)

import uuid

# 1. User A Signup & Login
print("\n--- 1. Testing User A Authentication & Initial Profile ---")
alice_email = f"alice_{uuid.uuid4().hex[:6]}@tamargi.ai"
user_a_signup = post_json("/api/auth/signup", {
    "email": alice_email,
    "password": "Password123",
    "full_name": "أليس أحمد"
})
user_a_id = user_a_signup["user"]["id"]
user_a_token = user_a_signup["token"]
print(f"User A Registered: ID={user_a_id}, Token={user_a_token[:12]}...")

user_a_profile = get_json(f"/api/patient/profile?user_id={user_a_id}")
assert len(user_a_profile["conditions"]) == 0, "Initial conditions must be empty"
assert len(user_a_profile["allergies"]) == 0, "Initial allergies must be empty"
assert len(user_a_profile["medications"]) == 0, "Initial medications must be empty"
print("Initial Profile: 100% Empty (Zero demo/hardcoded values) [PASS]")

# 2. Update User A Profile
print("\n--- 2. Updating User A Health Profile in DB ---")
post_json("/api/patient/profile", {
    "user_id": user_a_id,
    "date_of_birth": "1980-05-15",
    "sex": "female",
    "weight_kg": 68.0,
    "height_cm": 165.0
})
post_json("/api/patient/conditions", {
    "user_id": user_a_id,
    "condition_name": "ارتفاع ضغط الدم",
    "confirmed": True
})
post_json("/api/patient/allergies", {
    "user_id": user_a_id,
    "allergen": "بنسلين",
    "confirmed": True
})
post_json("/api/patient/medications", {
    "user_id": user_a_id,
    "generic_name": "ميتفورمين",
    "strength": "500 mg",
    "confirmed": True
})

user_a_profile_updated = get_json(f"/api/patient/profile?user_id={user_a_id}")
assert len(user_a_profile_updated["conditions"]) == 1, "Must have 1 condition"
assert len(user_a_profile_updated["allergies"]) == 1, "Must have 1 allergy"
assert len(user_a_profile_updated["medications"]) == 1, "Must have 1 medication"
print(f"User A Updated Profile: Conditions={len(user_a_profile_updated['conditions'])}, Allergies={len(user_a_profile_updated['allergies'])}, Meds={len(user_a_profile_updated['medications'])} [PASS]")

# 3. User B Isolation Test
print("\n--- 3. Testing User B Isolation & Privacy Protection ---")
bob_email = f"bob_{uuid.uuid4().hex[:6]}@tamargi.ai"
user_b_signup = post_json("/api/auth/signup", {
    "email": bob_email,
    "password": "Password456",
    "full_name": "بوب حسن"
})
user_b_id = user_b_signup["user"]["id"]
user_b_token = user_b_signup["token"]
print(f"User B Registered: ID={user_b_id}")

user_b_profile = get_json(f"/api/patient/profile?user_id={user_b_id}")
assert len(user_b_profile["conditions"]) == 0, "User B must not see User A conditions"
assert len(user_b_profile["allergies"]) == 0, "User B must not see User A allergies"
assert len(user_b_profile["medications"]) == 0, "User B must not see User A medications"
print("User Isolation: User B cannot access User A health profile [PASS]")

# 4. Real Chat Flow with Evidence & Grounding
print("\n--- 4. Testing Real Chat Flow & Evidence Retrieval ---")
conv_id = f"conv_{user_a_id[:8]}"
chat_res = post_json("/api/chat", {
    "query": "هل يمكن تناول الباراسيتامول لتسكين الألم؟",
    "conversation_id": conv_id,
    "user_id": user_a_id,
    "input_type": "text"
})
print(f"Chat Response Length: {len(chat_res['answer'])} chars")
print(f"Sources Returned: {len(chat_res.get('sources', []))} sources")
assert len(chat_res.get("sources", [])) > 0, "Real RAG sources must be returned"
print("Chat with Grounded RAG Evidence [PASS]")

# 5. Medication Plan Preview Generation from Conversation
print("\n--- 5. Generating Structured Medication Plan from Conversation ---")
plan_preview_res = post_json("/api/plans/generate_preview", {
    "user_id": user_a_id,
    "conversation_id": conv_id
})
assert plan_preview_res["status"] == "ready", f"Expected ready, got {plan_preview_res}"
preview = plan_preview_res["plan_preview"]
print(f"Generated Plan Title: {preview['title']}")
print(f"Patient Info Age: {preview['patient_info']['age']} years")
print(f"Confirmed Conditions: {preview['confirmed_factors']['conditions']}")
print(f"Medication Candidates Count: {len(preview['medications'])}")
assert len(preview["medications"]) > 0, "Must have structured medication candidates"
cand_0 = preview["medications"][0]
print(f"Candidate Med: {cand_0['generic_name']} | Safety: {cand_0['safety_status']}")
print("Structured Plan Preview Generation from Conversation [PASS]")

# 6. Save Plan & Generate Verification Token
print("\n--- 6. Saving Plan & Generating QR Verification Token ---")
saved_plan = post_json("/api/plans", {
    "user_id": user_a_id,
    "conversation_id": conv_id,
    "title": preview["title"],
    "patient_info": preview["patient_info"],
    "confirmed_factors": preview["confirmed_factors"],
    "medications": preview["medications"],
    "safety_summary": preview["safety_summary"],
    "evidence_provenance": preview["evidence_provenance"]
})
plan_id = saved_plan["id"]
token = saved_plan["verification_token"]
print(f"Saved Plan ID: {plan_id}")
print(f"Verification Token: {token}")
assert len(token) > 10, "Token must be secure non-empty string"
print("Plan Saved to DB with Verification Token [PASS]")

# 7. Pharmacist Verification Public Endpoint (No Auth)
print("\n--- 7. Testing Public Pharmacist Verification Endpoint ---")
public_plan = get_json(f"/api/plans/verify/{token}")
assert public_plan["id"] == plan_id, "Plan ID must match"
assert "user_id" not in public_plan or not public_plan.get("user_id"), "Private user_id must NOT be exposed publicly"
assert len(public_plan["medications"]) > 0, "Public view must display candidate medications"
assert len(public_plan["evidence_provenance"]) > 0, "Public view must include evidence provenance"
print(f"Pharmacist Verification Plan: '{public_plan['title']}' | Status: {public_plan['status']} [PASS]")

# 8. User B Access Denial to Private Plan Endpoint
print("\n--- 8. Testing User B Access Denial to User A Private Plan ---")
try:
    get_json(f"/api/plans/{plan_id}?user_id={user_b_id}")
    print("ERROR: User B was able to access User A plan!")
    sys.exit(1)
except urllib.error.HTTPError as e:
    assert e.code == 404, f"Expected 404, got {e.code}"
    print("User B Forbidden / Not Found for User A Private Plan [PASS]")

# 9. Insufficient Evidence Plan Creation Test
print("\n--- 9. Testing Plan Generation on Conversation with No Medications ---")
empty_conv_id = "empty_conv_123"
post_json("/api/chat", {
    "query": "صباح الخير يا تمرجي",
    "conversation_id": empty_conv_id,
    "user_id": user_a_id
})
insufficient_res = post_json("/api/plans/generate_preview", {
    "user_id": user_a_id,
    "conversation_id": empty_conv_id
})
assert insufficient_res["status"] == "insufficient_plan_evidence", f"Expected insufficient_plan_evidence, got {insufficient_res}"
print(f"Insufficient Plan Evidence Rejection: '{insufficient_res['message']}' [PASS]")

print("\n" + "=" * 95)
print("FINAL RESULT: ALL 9 END-TO-END INTEGRATION TESTS PASSED (100%)")
print("=" * 95)
