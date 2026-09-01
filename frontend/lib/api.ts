import { supabase } from "./supabase";

export interface SourceItem {
  evidenceId: string;
  fileName: string;
  pageNumber: number;
  chunkId?: number;
  rank: number;
  score: number;
  excerpt: string;
}

export interface VideoItem {
  id: string;
  title: string;
  topic?: string;
  medication_or_device?: string;
  category?: string;
  dosage_form?: string;
  device_type?: string;
  device_name?: string;
  usage_topic?: string;
  language?: string;
  video_url: string;
  thumbnail_url?: string;
  source_name: string;
  source_url?: string;
}

export interface EvidenceCitation {
  source: string;
  page: number;
  section?: string;
  excerpt?: string;
}

export interface SafetyCheckItem {
  type: string;
  status: "safe_no_known_issue" | "caution" | "warning" | "contraindicated" | "requires_confirmation" | "insufficient_evidence";
  medication: string;
  patient_factor?: string;
  reason: string;
  evidence: EvidenceCitation[];
}

export interface XAIExplanation {
  decision: string;
  summary: string;
  because: string[];
  patient_factors_used: string[];
  evidence_used: EvidenceCitation[];
}

export interface ConfirmationContext {
  fact_type: string;
  fact_id?: string;
  value: string;
  normalized_value: string;
  prompt: string;
}

export interface SafetyResult {
  overall_status: "safe_no_known_issue" | "caution" | "warning" | "contraindicated" | "requires_confirmation" | "insufficient_evidence";
  summary: string;
  checks: SafetyCheckItem[];
  requires_confirmation: boolean;
  confirmation?: ConfirmationContext | null;
  xai?: XAIExplanation | null;
}

export interface PatientCondition {
  id?: string;
  user_id: string;
  condition_name: string;
  normalized_condition: string;
  status: string;
  confirmed: boolean;
  last_confirmed_at?: string;
  active: boolean;
}

export interface PatientAllergy {
  id?: string;
  user_id: string;
  allergen: string;
  normalized_allergen: string;
  reaction?: string;
  severity?: string;
  confirmed: boolean;
  last_confirmed_at?: string;
  active: boolean;
}

export interface PatientMedication {
  id?: string;
  user_id: string;
  generic_name: string;
  brand_name?: string;
  strength?: string;
  dosage_form?: string;
  dose?: string;
  confirmed: boolean;
  last_confirmed_at?: string;
  active: boolean;
}

export interface PatientHistoryItem {
  id?: string;
  user_id: string;
  history_type: string;
  value: string;
  confirmed: boolean;
  last_confirmed_at?: string;
  active: boolean;
}

export interface PatientProfileData {
  user_id: string;
  date_of_birth?: string;
  sex?: string;
  pregnancy_status?: string;
  breastfeeding_status?: string;
  weight_kg?: number;
  height_cm?: number;
  demographics?: {
    date_of_birth?: string;
    sex?: string;
    pregnancy_status?: string;
    breastfeeding_status?: string;
    weight_kg?: number;
    height_cm?: number;
  };
  conditions: PatientCondition[];
  allergies: PatientAllergy[];
  medications: PatientMedication[];
  history: PatientHistoryItem[];
  pending_confirmations?: any[];
}

export interface ConversationItem {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MedicationPlan {
  id: string;
  user_id: string;
  conversation_id?: string;
  title: string;
  verification_token: string;
  patient_info: {
    full_name?: string;
    age?: number;
    sex?: string;
    weight_kg?: number;
    height_cm?: number;
    pregnancy_status?: string;
    breastfeeding_status?: string;
  };
  confirmed_factors: {
    conditions?: string[];
    allergies?: string[];
    medications?: string[];
  };
  medications: Array<{
    generic_name: string;
    brand_name?: string;
    strength?: string;
    dosage_form?: string;
    route?: string;
    dose?: string;
    frequency?: string;
    duration?: string;
    instructions: string;
    safety_status?: string;
    safety_note?: string;
    evidence_citations?: EvidenceCitation[];
  }>;
  safety_summary: {
    overall_status?: string;
    summary_text?: string;
    checks_count?: number;
  };
  evidence_provenance: EvidenceCitation[];
  status: "active" | "archived" | "dispensed";
  notes?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[];
  video?: VideoItem | null;
  medicalNote?: string;
  safety?: SafetyResult | null;
  timestamp?: string;
}

export interface ChatResponse {
  query: string;
  normalized_query?: string;
  language_detected?: string;
  answer: string;
  sources: SourceItem[];
  video?: VideoItem | null;
  conversation_id?: string;
  safety?: SafetyResult | null;
  requires_confirmation?: boolean;
  confirmation?: ConfirmationContext | null;
}

export interface TranscribeResponse {
  transcript: string;
  language: "ar" | "en" | "mixed";
  language_label: string;
  confidence: number;
  success: boolean;
  error?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
  } catch (e) {
    // Session check fails gracefully
  }
  return headers;
}

export async function sendChatMessage(
  query: string,
  conversationId?: string,
  userId?: string,
  inputType: "text" | "voice" = "text"
): Promise<ChatResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
        user_id: userId,
        input_type: inputType,
      }),
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.statusText}`);
    }

    return await res.json();
  } catch (error) {
    console.warn("Backend API unreachable, using client-side fallback:", error);
    return mockChatResponse(query);
  }
}

export async function transcribeAudio(audioBlob: Blob): Promise<TranscribeResponse> {
  try {
    const formData = new FormData();
    const fileExt = audioBlob.type.includes("wav") ? "wav" : (audioBlob.type.includes("ogg") ? "ogg" : "webm");
    formData.append("file", audioBlob, `recording.${fileExt}`);

    const res = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Voice transcription error: ${res.statusText}`);
    }

    const data: TranscribeResponse = await res.json();
    return data;
  } catch (error: any) {
    console.warn("Backend voice transcription unreachable or error:", error);
    return {
      transcript: "",
      language: "ar",
      language_label: "عربي",
      confidence: 0,
      success: false,
      error: error?.message || "Transcription failed",
    };
  }
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return await res.json();
  } catch {
    return { status: "offline", service: "Tamargi.ai RAG Backend" };
  }
}

export async function submitFeedback(messageId: string, userId: string, rating: 1 | -1, comment?: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId, rating, comment }),
    });
    return await res.json();
  } catch (err) {
    console.error("Failed to send feedback", err);
  }
}

export interface VideoLookupPayload {
  query_text?: string;
  generic_name?: string;
  brand_name?: string;
  dosage_form?: string;
  device_name?: string;
  usage_topic?: string;
}

export interface VideoLookupResult {
  found: boolean;
  reason?: string;
  title?: string;
  video_url?: string;
  thumbnail_url?: string;
  source_name?: string;
  source_url?: string;
  usage_topic?: string;
  device_name?: string;
  language?: string;
  helper_prompt?: string;
}

export async function lookupVerifiedVideo(payload: VideoLookupPayload): Promise<VideoLookupResult | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/video/lookup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Video lookup request failed", err);
  }
  return null;
}

export async function fetchPatientProfile(userId?: string): Promise<PatientProfileData | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/profile`, { headers });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Failed to fetch patient profile", err);
  }
  return null;
}

export async function updatePatientProfile(data: Partial<PatientProfileData>): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/profile`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });
    return res.ok;
  } catch (err) {
    console.warn("Failed to update patient profile", err);
    return false;
  }
}

export async function addPatientCondition(userId: string, conditionName: string): Promise<PatientCondition | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/conditions`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, condition_name: conditionName, confirmed: true }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to add condition", err);
  }
  return null;
}

export async function deletePatientCondition(conditionId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/conditions/${conditionId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

export async function addPatientAllergy(userId: string, allergen: string, severity = "moderate"): Promise<PatientAllergy | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/allergies`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, allergen, severity, confirmed: true }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to add allergy", err);
  }
  return null;
}

export async function deletePatientAllergy(allergyId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/allergies/${allergyId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

export async function addPatientMedication(userId: string, genericName: string, strength?: string): Promise<PatientMedication | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/medications`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, generic_name: genericName, strength, confirmed: true }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to add medication", err);
  }
  return null;
}

export async function deletePatientMedication(medicationId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/medications/${medicationId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

export async function addPatientHistory(userId: string, historyType: string, value: string): Promise<PatientHistoryItem | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/history`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, history_type: historyType, value, confirmed: true }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to add history", err);
  }
  return null;
}

export async function deletePatientHistory(historyId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/patient/history/${historyId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

// -------------------------------------------------------------
// User-Specific Conversations API
// -------------------------------------------------------------
export async function fetchUserConversations(userId?: string): Promise<ConversationItem[]> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/conversations`, { headers });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to fetch conversations", err);
  }
  return [];
}

export async function createUserConversation(userId: string, title?: string): Promise<ConversationItem | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/conversations`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, title: title || "محادثة جديدة" }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to create conversation", err);
  }
  return null;
}

export async function fetchConversationMessages(convId: string, userId?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}/messages`, { headers });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to fetch conversation messages", err);
  }
  return [];
}

export async function renameUserConversation(convId: string, title: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`, {
      method: "PATCH",
      headers,
      body: JSON.stringify({ title }),
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

export async function deleteUserConversation(convId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

// -------------------------------------------------------------
// Medication Plans (Draft Prescriptions) API
// -------------------------------------------------------------
export async function generateMedicationPlanPreview(
  userId: string,
  conversationId: string,
  messageId?: string
): Promise<any> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/plans/generate_preview`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: userId, conversation_id: conversationId, message_id: messageId }),
    });
    if (res.ok) return await res.json();
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Failed to generate plan preview", err);
    return { status: "error", message: "تعذر الاتصال بالخادم لإنشاء الخطة الدوائية" };
  }
}

export async function createMedicationPlan(planData: Partial<MedicationPlan>): Promise<MedicationPlan | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/plans`, {
      method: "POST",
      headers,
      body: JSON.stringify(planData),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to create medication plan", err);
  }
  return null;
}

export async function fetchUserPlans(userId?: string): Promise<MedicationPlan[]> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/plans`, { headers });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to fetch user plans", err);
  }
  return [];
}

export async function fetchPlanById(planId: string, userId?: string): Promise<MedicationPlan | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/plans/${planId}`, { headers });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to fetch plan by id", err);
  }
  return null;
}

export async function verifyPlanByToken(token: string): Promise<MedicationPlan | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/plans/verify/${encodeURIComponent(token)}`);
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Failed to verify plan by token", err);
  }
  return null;
}

export async function deleteMedicationPlan(planId: string, userId?: string): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/plans/${planId}`, {
      method: "DELETE",
      headers,
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

function mockChatResponse(query: string): ChatResponse {
  const isArabic = /[\u0600-\u06FF]/.test(query);

  if (query.toLowerCase().includes("anidulafungin") || query.includes("موانع")) {
    return {
      query,
      normalized_query: "What are the contraindications of Anidulafungin?",
      language_detected: isArabic ? "egyptian" : "en",
      answer: isArabic
        ? "بناءً على الأدلة المستخرجة، فإن موانع استخدام دواء Anidulafungin هي:\n\n• الحساسية المفرطة تجاه أنيدولافونجين أو أي من مضادات الفطريات من فئة الإكينوكاندين [E1].\n• الحالات المعروفة أو المشتبه بإصابتها بعدم تحمل الفروكتوز الوراثي [E1]."
        : "Based on the retrieved evidence, the contraindications for Anidulafungin are:\n\n• Hypersensitivity to anidulafungin, other echinocandins, or any component of the formulation [E1].\n• Known or suspected hereditary fructose intolerance [E1].",
      video: null,
      sources: [
        {
          evidenceId: "E1",
          fileName: "egypt_antimicrobial_formulary_2023.pdf",
          pageNumber: 52,
          chunkId: 1,
          rank: 1,
          score: 2.92,
          excerpt:
            "Contraindications: Hypersensitivity to anidulafungin, other echinocandins, or any component of the formulation; known or suspected hereditary fructose intolerance. Adverse Drug Reactions >10%: Hypotension (15%), Insomnia (15%), Hypokalemia.",
        },
        {
          evidenceId: "E2",
          fileName: "egypt_antimicrobial_formulary_2023.pdf",
          pageNumber: 53,
          chunkId: 2,
          rank: 2,
          score: 0.38,
          excerpt:
            "Warnings/Precautions: Anaphylactic reactions: Immediate treatment for hypersensitivity reactions should be available. Discontinue treatment immediately if reactions occur.",
        },
      ],
    };
  }

  return {
    query,
    normalized_query: query,
    language_detected: isArabic ? "ar" : "en",
    answer: isArabic
      ? "عفواً، الأدلة المتاحة غير كافية للإجابة على هذا السؤال بشكل آمن."
      : "The retrieved evidence is insufficient to answer this question safely.",
    video: null,
    sources: [
      {
        evidenceId: "E1",
        fileName: "egypt_antimicrobial_formulary_2023.pdf",
        pageNumber: 52,
        chunkId: 1,
        rank: 1,
        score: 0.12,
        excerpt: "Formulary guideline excerpt for reference.",
      },
    ],
  };
}
