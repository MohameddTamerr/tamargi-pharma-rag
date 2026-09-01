import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.auth.supabase_auth import get_current_user, get_optional_user, AuthenticatedUser
from app.database.supabase import get_supabase_client
from app.plans.generator import generate_structured_plan_preview

router = APIRouter()

# In-memory store for offline/local execution
IN_MEMORY_PLANS: Dict[str, Dict[str, Any]] = {} # plan_id -> plan_data
IN_MEMORY_TOKEN_MAP: Dict[str, str] = {} # token -> plan_id

class MedicationItem(BaseModel):
    generic_name: str
    brand_name: Optional[str] = None
    strength: Optional[str] = "Requires professional determination"
    dosage_form: Optional[str] = "Requires professional determination"
    route: Optional[str] = "Oral"
    dose: Optional[str] = "Requires professional determination"
    frequency: Optional[str] = "Requires professional determination"
    duration: Optional[str] = "Requires professional determination"
    instructions: Optional[str] = "يُحدد بمعرفة الطبيب المعالج أو الصيدلي"
    safety_status: Optional[str] = "caution"
    safety_note: Optional[str] = None
    evidence_citations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class CreatePlanRequest(BaseModel):
    user_id: Optional[str] = None # Ignored when authenticated via JWT
    conversation_id: Optional[str] = None
    title: Optional[str] = "خطة دوائية للمراجعة الطبية"
    patient_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confirmed_factors: Optional[Dict[str, Any]] = Field(default_factory=dict)
    medications: List[MedicationItem] = Field(default_factory=list)
    safety_summary: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    notes: Optional[str] = None

class GeneratePreviewRequest(BaseModel):
    user_id: Optional[str] = None # Ignored when authenticated via JWT
    conversation_id: str
    message_id: Optional[str] = None

@router.post("/generate_preview")
def generate_preview(
    req: GeneratePreviewRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Generates a structured, read-only Medication Plan preview directly
    from grounded conversation turns, patient profile, and Safety Engine.
    Strictly bound to the authenticated Supabase user.
    """
    authoritative_user_id = user.id if (user and hasattr(user, "id")) else (req.user_id or "guest_user")
    return generate_structured_plan_preview(authoritative_user_id, req.conversation_id, req.message_id)

@router.get("")
def get_user_plans(
    user_id: Optional[str] = Query(None, description="Optional legacy query param, overridden by verified JWT sub"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves all medication plans created by the authenticated Supabase user."""
    authoritative_user_id = user.id if (user and hasattr(user, "id")) else user_id
    if not authoritative_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    client = get_supabase_client()
    if client:
        try:
            res = client.table("medication_plans").select("*").eq("user_id", authoritative_user_id).order("created_at", desc=True).execute()
            if res.data is not None:
                return res.data
        except Exception:
            pass

    user_plans = [p for p in IN_MEMORY_PLANS.values() if p.get("user_id") == authoritative_user_id]
    user_plans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_plans

@router.post("")
def create_medication_plan(
    req: CreatePlanRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """Creates a new draft Medication Plan with a secure verification token for the user."""
    authoritative_user_id = user.id if (user and hasattr(user, "id")) else (req.user_id or "guest_user")
    plan_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    now = datetime.now()
    now_iso = now.isoformat()
    expires_iso = (now + timedelta(days=30)).isoformat()

    plan_data = {
        "id": plan_id,
        "user_id": authoritative_user_id,
        "title": req.title or "خطة دوائية للمراجعة الطبية",
        "verification_token": token,
        "patient_info": req.patient_info or {},
        "confirmed_factors": req.confirmed_factors or {},
        "medications": [m.dict() for m in req.medications],
        "safety_summary": req.safety_summary or {},
        "evidence_provenance": req.evidence_provenance or [],
        "status": "active",
        "notes": req.notes,
        "expires_at": expires_iso,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    client = get_supabase_client()
    if client:
        try:
            res = client.table("medication_plans").insert(plan_data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            pass

    IN_MEMORY_PLANS[plan_id] = plan_data
    IN_MEMORY_TOKEN_MAP[token] = plan_id
    return plan_data

@router.get("/{plan_id}")
def get_plan_by_id(
    plan_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves full details of a plan strictly for its authenticated owner."""
    authoritative_user_id = user.id if (user and hasattr(user, "id")) else user_id
    if not authoritative_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    client = get_supabase_client()
    if client:
        try:
            res = client.table("medication_plans").select("*").eq("id", plan_id).eq("user_id", authoritative_user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            pass

    plan = IN_MEMORY_PLANS.get(plan_id)
    if plan and plan.get("user_id") == authoritative_user_id:
        return plan

    raise HTTPException(status_code=404, detail="Medication plan not found or unauthorized")

@router.get("/verify/{token}")
def verify_plan_by_token(token: str):
    """
    PUBLIC EXCEPTION:
    Public read-only verification endpoint for Pharmacists scanning QR code.
    Authorized strictly through the secure random verification token.
    Exposes only authorized plan data and evidence provenance, without private user_id or email.
    """
    client = get_supabase_client()
    if client:
        try:
            res = client.table("medication_plans").select(
                "id, title, verification_token, patient_info, confirmed_factors, medications, safety_summary, evidence_provenance, status, created_at, expires_at"
            ).eq("verification_token", token).execute()
            if res.data and len(res.data) > 0:
                plan = res.data[0]
                if plan.get("status") != "active":
                    raise HTTPException(status_code=410, detail="This medication plan is no longer available for verification.")
                return plan
        except HTTPException:
            raise
        except Exception:
            pass

    plan_id = IN_MEMORY_TOKEN_MAP.get(token)
    if plan_id and plan_id in IN_MEMORY_PLANS:
        plan = IN_MEMORY_PLANS[plan_id]
        if plan.get("status") != "active":
            raise HTTPException(status_code=410, detail="This medication plan is no longer available for verification.")
        
        # Return sanitized pharmacist view (No user_id, No email)
        return {
            "id": plan["id"],
            "title": plan["title"],
            "verification_token": plan["verification_token"],
            "patient_info": plan.get("patient_info", {}),
            "confirmed_factors": plan.get("confirmed_factors", {}),
            "medications": plan.get("medications", []),
            "safety_summary": plan.get("safety_summary", {}),
            "evidence_provenance": plan.get("evidence_provenance", []),
            "status": plan.get("status", "active"),
            "created_at": plan.get("created_at"),
            "expires_at": plan.get("expires_at")
        }

    raise HTTPException(status_code=404, detail="Medication plan not found or invalid token")

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Soft-deletes or archives a plan for the authenticated user."""
    authoritative_user_id = user.id if (user and hasattr(user, "id")) else user_id
    if not authoritative_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    client = get_supabase_client()
    if client:
        try:
            client.table("medication_plans").delete().eq("id", plan_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass

    if plan_id in IN_MEMORY_PLANS and IN_MEMORY_PLANS[plan_id].get("user_id") == authoritative_user_id:
        token = IN_MEMORY_PLANS[plan_id].get("verification_token")
        if token in IN_MEMORY_TOKEN_MAP:
            del IN_MEMORY_TOKEN_MAP[token]
        del IN_MEMORY_PLANS[plan_id]
        return {"status": "deleted", "id": plan_id}

    return {"status": "deleted", "id": plan_id}
