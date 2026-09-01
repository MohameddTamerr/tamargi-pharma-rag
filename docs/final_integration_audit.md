# Tamargi.ai — Final Integration & Database Wiring Audit (Phase 0)

This audit documents all runtime mock/hardcoded values, authentication configuration discrepancies, fake pharmacist triggers, and Medication Plan authoring fields discovered during inspection prior to code modification.

---

## 1. Audit Findings Catalog

| # | File | Component / Function | Problem Identified | Current Data Source | Required Data Source | Fix Status |
|---|---|---|---|---|---|---|
| 1 | `frontend/lib/supabase.ts` | `createClient(supabaseUrl, supabaseAnonKey)` | Missing/placeholder environment variable (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) crashes signup with "Invalid API key" | Placeholder fallback string in code | Proper environment variable loading with developer-safe missing-configuration error | **PENDING** |
| 2 | `frontend/components/RightPanel.tsx` | `RightPanel({ allergies, currentMeds, chronicConditions })` | Default props contain hardcoded medical data ("فيتامين د", "ضغط الدم", "لا توجد") | Hardcoded default parameters | Dynamic `/api/patient/profile` record for authenticated user | **PENDING** |
| 3 | `frontend/components/RightPanel.tsx` | `RightPanel` — Pharmacist Card | Card displays fake live chat trigger ("تحتاج التحدث مع صيدلي الآن؟" "بدء محادثة مباشرة") without an underlying real pharmacist service | Static JSX markup | Truthful plan review preparation card ("جهّز خطتك الدوائية لمراجعة الصيدلي") linking to `/plans` | **PENDING** |
| 4 | `frontend/components/RightPanel.tsx` | `RightPanel` — FAQ List | FAQ questions hardcoded in JSX and unlinked from active chat handler | Static array | Centralized questions config dispatching real queries to the Agentic Orchestrator + RAG V2 | **PENDING** |
| 5 | `frontend/app/plans/page.tsx` | `PlansContent` Draft State | Manual plan modal allows authoring patient name, age, and typing free-text medications ("باراسيتامول / سيمبيكورت") with hardcoded factor arrays | Hardcoded initial `useState` and static input forms | Read-only structured candidate preview generated from conversation turns + RAG + Safety Engine | **PENDING** |
| 6 | `frontend/components/chat/ChatMessage.tsx` | `ChatMessage` — Plan Button | Button navigates to `/plans?draftQuery=...` triggering manual plan entry modal | Query parameter passing raw assistant text | Backend generation endpoint `/api/plans/generate_from_conversation` | **PENDING** |
| 7 | `frontend/app/chat/page.tsx` | `ChatPage` | `RightPanel` rendered without profile data or query click handler | Unwired component | Connected to user context, loading real Health Summary with appropriate empty state copy | **PENDING** |
| 8 | `frontend/components/Sidebar.tsx` | `Sidebar` | Uses `user?.id || "guest_user"` without auth redirect protection | Unauthenticated fallback | Protected route wrapper redirecting unauthenticated users to `/login` | **PENDING** |
| 9 | `frontend/app/profile/page.tsx` | `ProfilePage` | Health changes in profile not synced automatically with active chat Health Summary | Isolated page state | Shared data refresh between `/profile` and Health Summary | **PENDING** |
| 10 | `backend/app/api/plans.py` | `MedicationItem` / `CreatePlanRequest` | Free-text instructions permitted without structured conversation provenance | Manual client payload | Structured conversation-derived candidates with Safety snapshot & EDA evidence | **PENDING** |
| 11 | `frontend/app/verify-plan/[token]/page.tsx` | `VerifyPlanPage` | Verify plan page needs to be read-only, exposing only necessary review data without private account identifiers | Public token verification API | Verified secure read-only token view | **PENDING** |

---

## 2. Medical Data Invariants Enforced
- **Zero Runtime Fabrication**: No fake patient demographics, medications, or allergies rendered as defaults.
- **Empty State Truthfulness**:
  - If no allergy: `"لا توجد حساسية مسجلة"` (Never medically affirming "لا توجد").
  - If no conditions: `"لا توجد حالات مزمنة مسجلة"`.
  - If no medications: `"لا توجد أدوية حالية مسجلة"`.
- **Prescription Authoring Ban**: Medication Plans cannot be manually typed or fabricated. They must originate from grounded conversation turns with RAG evidence and Safety Engine verification.
