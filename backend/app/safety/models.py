from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SafetyStatus(str, Enum):
    SAFE_NO_KNOWN_ISSUE = "safe_no_known_issue"
    CAUTION = "caution"
    WARNING = "warning"
    CONTRAINDICATED = "contraindicated"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class ConfirmationStatus(str, Enum):
    CONFIRMED_CURRENT = "confirmed_current"
    NEEDS_CONFIRMATION = "needs_confirmation"
    DENIED = "denied"
    UNKNOWN = "unknown"

class EvidenceCitation(BaseModel):
    rule_id: Optional[str] = None
    source: str
    page: int
    section: Optional[str] = None
    chunk_id: Optional[int] = None
    excerpt: Optional[str] = None

class VerifiedSafetyRule(BaseModel):
    id: Optional[str] = None
    rule_type: str # 'allergy', 'drug_disease', 'drug_drug', 'high_alert', 'do_not_crush', 'pregnancy', 'breastfeeding'
    drug_a: str
    drug_b: Optional[str] = None
    condition_name: Optional[str] = None
    allergen_class: Optional[str] = None
    dosage_form: Optional[str] = None
    status: SafetyStatus
    reason: Optional[str] = None
    source_file: str
    source_page: int
    source_monograph: Optional[str] = None
    source_section: Optional[str] = None
    evidence_excerpt: str
    source_authority: str = "Egyptian Drug Authority"
    verified: bool = False
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SafetyCheckItem(BaseModel):
    type: str # 'allergy', 'drug_disease', 'drug_drug', 'pregnancy', 'breastfeeding', 'high_alert', 'do_not_crush'
    status: SafetyStatus
    medication: str
    patient_factor: Optional[str] = None
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)
    evidence: List[EvidenceCitation] = Field(default_factory=list)

class XAIExplanation(BaseModel):
    decision: SafetyStatus
    summary: str
    because: List[str] = Field(default_factory=list)
    patient_factors_used: List[str] = Field(default_factory=list)
    evidence_used: List[EvidenceCitation] = Field(default_factory=list)

class ConfirmationContext(BaseModel):
    fact_type: str # 'condition', 'allergy', 'medication', 'history', 'pregnancy'
    fact_id: Optional[str] = None
    value: str
    normalized_value: str
    prompt: str

class SafetyResult(BaseModel):
    medication: Optional[str] = None
    overall_status: SafetyStatus
    summary: str
    checks: List[SafetyCheckItem] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation: Optional[ConfirmationContext] = None
    xai: Optional[XAIExplanation] = None

# Patient Domain Models
class PatientCondition(BaseModel):
    id: Optional[str] = None
    user_id: str
    condition_name: str
    normalized_condition: str
    status: str = "active"
    confirmed: bool = False
    last_confirmed_at: Optional[datetime] = None
    source: str = "chat"
    active: bool = True
    created_at: Optional[datetime] = None

class PatientAllergy(BaseModel):
    id: Optional[str] = None
    user_id: str
    allergen: str
    normalized_allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = "moderate"
    confirmed: bool = False
    last_confirmed_at: Optional[datetime] = None
    active: bool = True
    created_at: Optional[datetime] = None

class PatientMedication(BaseModel):
    id: Optional[str] = None
    user_id: str
    generic_name: str
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    indication: Optional[str] = None
    confirmed: bool = False
    last_confirmed_at: Optional[datetime] = None
    active: bool = True
    created_at: Optional[datetime] = None

class PatientHistoryItem(BaseModel):
    id: Optional[str] = None
    user_id: str
    history_type: str # 'surgery', 'hospitalization', 'previous_adverse_reaction', 'pregnancy_history', 'other'
    value: str
    normalized_value: str
    confirmed: bool = False
    last_confirmed_at: Optional[datetime] = None
    active: bool = True
    created_at: Optional[datetime] = None

class PendingConfirmation(BaseModel):
    id: Optional[str] = None
    user_id: str
    conversation_id: str
    fact_type: str
    fact_id: Optional[str] = None
    normalized_value: str
    original_question: str
    medication_context: Optional[str] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class PatientProfileData(BaseModel):
    user_id: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    pregnancy_status: Optional[str] = "none"
    breastfeeding_status: Optional[str] = "none"
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    conditions: List[PatientCondition] = Field(default_factory=list)
    allergies: List[PatientAllergy] = Field(default_factory=list)
    medications: List[PatientMedication] = Field(default_factory=list)
    medical_history: List[PatientHistoryItem] = Field(default_factory=list)

PatientProfile = PatientProfileData
