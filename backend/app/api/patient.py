from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime

from app.auth.supabase_auth import get_current_user, AuthenticatedUser
from app.safety.models import (
    PatientProfileData,
    PatientCondition,
    PatientAllergy,
    PatientMedication,
    PatientHistoryItem
)
from app.safety.patient_context import (
    get_patient_profile,
    add_patient_condition,
    add_patient_allergy,
    add_patient_medication,
    add_patient_history,
    IN_MEMORY_PROFILES,
    IN_MEMORY_CONDITIONS,
    IN_MEMORY_ALLERGIES,
    IN_MEMORY_MEDICATIONS,
    IN_MEMORY_HISTORY
)
from app.database.supabase import get_supabase_client

router = APIRouter(prefix="/api/patient", tags=["Patient Profile"])

class ProfileUpdateRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    pregnancy_status: Optional[str] = "none"
    breastfeeding_status: Optional[str] = "none"
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None

class ConditionCreateRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    condition_name: str
    confirmed: bool = True

class AllergyCreateRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    allergen: str
    severity: Optional[str] = "moderate"
    confirmed: bool = True

class MedicationCreateRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    generic_name: str
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    confirmed: bool = True

class HistoryCreateRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    history_type: str
    value: str
    confirmed: bool = True

@router.get("/profile", response_model=PatientProfileData)
def get_profile(
    user_id: Optional[str] = Query(None, description="Optional legacy query param, overridden by verified JWT sub"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Fetches patient profile for the authenticated Supabase user."""
    authoritative_user_id = user.id
    return get_patient_profile(authoritative_user_id)

@router.post("/profile")
def update_profile(
    req: ProfileUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Updates demographic and physiological fields for the authenticated Supabase user."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_profiles").upsert({
                "user_id": authoritative_user_id,
                "date_of_birth": req.date_of_birth.isoformat() if req.date_of_birth else None,
                "sex": req.sex,
                "pregnancy_status": req.pregnancy_status,
                "breastfeeding_status": req.breastfeeding_status,
                "weight_kg": req.weight_kg,
                "height_cm": req.height_cm,
                "updated_at": datetime.now().isoformat()
            }, on_conflict="user_id").execute()
        except Exception as e:
            print(f"[Supabase Profile Upsert Error] {e}")

    # Update in-memory fallback
    data_dict = req.model_dump(mode="json")
    data_dict["user_id"] = authoritative_user_id
    IN_MEMORY_PROFILES[authoritative_user_id] = data_dict
    return {"status": "success", "user_id": authoritative_user_id}

@router.post("/conditions", response_model=PatientCondition)
def create_condition(
    req: ConditionCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    return add_patient_condition(user.id, req.condition_name, req.confirmed)

@router.delete("/conditions/{condition_id}")
def delete_condition(
    condition_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Soft-deletes condition by marking active=false, strictly bounded by authenticated user."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_conditions").update({"active": False}).eq("id", condition_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass
    for c in IN_MEMORY_CONDITIONS.get(authoritative_user_id, []):
        if c.get("id") == condition_id:
            c["active"] = False
    return {"status": "success", "id": condition_id}

@router.post("/allergies", response_model=PatientAllergy)
def create_allergy(
    req: AllergyCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    return add_patient_allergy(user.id, req.allergen, req.confirmed, req.severity or "moderate")

@router.delete("/allergies/{allergy_id}")
def delete_allergy(
    allergy_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_allergies").update({"active": False}).eq("id", allergy_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass
    for a in IN_MEMORY_ALLERGIES.get(authoritative_user_id, []):
        if a.get("id") == allergy_id:
            a["active"] = False
    return {"status": "success", "id": allergy_id}

@router.post("/medications", response_model=PatientMedication)
def create_medication(
    req: MedicationCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    return add_patient_medication(user.id, req.generic_name, req.brand_name, req.strength, req.dose, req.confirmed)

@router.delete("/medications/{medication_id}")
def delete_medication(
    medication_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_medications").update({"active": False}).eq("id", medication_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass
    for m in IN_MEMORY_MEDICATIONS.get(authoritative_user_id, []):
        if m.get("id") == medication_id:
            m["active"] = False
    return {"status": "success", "id": medication_id}

@router.post("/history", response_model=PatientHistoryItem)
def create_history(
    req: HistoryCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    return add_patient_history(user.id, req.history_type, req.value, req.confirmed)

@router.delete("/history/{history_id}")
def delete_history(
    history_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("patient_medical_history").update({"active": False}).eq("id", history_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass
    for h in IN_MEMORY_HISTORY.get(authoritative_user_id, []):
        if h.get("id") == history_id:
            h["active"] = False
    return {"status": "success", "id": history_id}
