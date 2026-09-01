# Tamargi.ai — Comprehensive Authentication Architecture Audit

**Date**: September 1, 2026  
**Auditor**: Antigravity AI  
**Scope**: Full authentication system, session lifecycle, token issuance, identity resolution, authorization boundaries, and RLS enforcement across Tamargi.ai.

---

## 1. Executive Summary & Audit State

During previous development phases, when the frontend Supabase anon key encountered an invalid signature format (`.X-placeholder-anon`), a temporary parallel authentication mechanism was implemented with custom endpoints (`/api/auth/signup`, `/api/auth/login`, `/api/auth/session`, `/api/auth/logout`, `/api/auth/forgot-password`) and custom SHA-256 password hashing.

This audit evaluates the exact security posture, failure modes, and architectural divergence between the current state and the target production architecture.

---

## 2. Technical Audit Matrix (16 Core Dimensions)

| Dimension | Current Implementation | Target Production Architecture | Security & Architectural Impact |
|---|---|---|---|
| **1. Where users are stored** | In-memory dictionary `IN_MEMORY_USERS` in `backend/app/api/auth.py` | `auth.users` (Supabase Auth) + `public.profiles` (linked via `id REFERENCES auth.users(id)`) | **High Risk**: Users lost on restart; identity namespace uncoupled from database RLS. |
| **2. Where passwords are stored** | `IN_MEMORY_USERS[email]["password_hash"]` | `auth.users.encrypted_password` in Supabase GoTrue schema | **High Risk**: Custom storage violates separation of concerns. Passwords must never touch app code. |
| **3. Who hashes passwords** | Python `hashlib.sha256(password + salt)` in backend | Supabase Auth (GoTrue) using standard `bcrypt` | **High Risk**: SHA-256 without adaptive work factor is vulnerable to offline cracking. |
| **4. Who issues access tokens** | `backend/app/api/auth.py` | Supabase Auth Service | **Critical**: Custom token issuer bypasses Supabase cryptographic signatures. |
| **5. Token format** | Opaque random string (`tok_<32_hex_chars>`) | Standard RFC 7519 JWT (`header.payload.signature`) signed with HMAC-SHA256 | **Critical**: Opaque tokens cannot be verified statelessly or forwarded to Supabase PostgREST. |
| **6. Token expiration** | Fixed 30-day timestamp in application memory | Configurable JWT lifetime (default 3600s / 1 hour) with refresh token rotation | **Moderate**: Long-lived opaque tokens lack revocation and standard refresh mechanisms. |
| **7. Session persistence mechanism** | Browser `localStorage` (`tamargi_custom_session`) checked against backend memory | Supabase Client SDK (`@supabase/supabase-js`) auto-persisted session with silent refresh | **Moderate**: Custom persistence lacks automatic token renewal on expiry. |
| **8. How backend resolves `user_id`** | Reads `?user_id=...` query param or JSON `body.user_id` without cryptographic proof | Extracted server-side from verified `Authorization: Bearer <Supabase_JWT>` (`payload["sub"]`) | **Critical Vulnerability**: Client can supply arbitrary `user_id` and impersonate any patient. |
| **9. Whether backend tokens are Supabase JWTs** | **NO** (Custom opaque strings) | **YES** (Standard Supabase Auth JWTs) | **Incompatible**: Cannot be used with Supabase APIs or database functions. |
| **10. Whether `auth.uid()` works with current flow** | **NO** (`auth.uid()` evaluates to `NULL` because no valid Supabase JWT is passed) | **YES** (`auth.uid()` resolves to `payload["sub"]`) | **Critical**: Supabase Row Level Security cannot distinguish users without JWT. |
| **11. Whether RLS is actually protecting requests** | **NO** (Requests either use memory fallback or backend `service_role` which bypasses RLS) | **YES** (Direct user-scoped client or server-verified identity bounds all queries) | **Critical**: Database-level data isolation is inactive under `service_role`. |
| **12. Whether frontend talks directly to Supabase Auth** | **NO** (Routed through custom `/api/auth` endpoints) | **YES** (`supabase.auth.signUp()`, `signInWithPassword()`, `signOut()`, etc.) | **Divergence**: Unnecessary custom backend proxy layer. |
| **13. Whether backend `service_role` bypasses RLS** | **YES** (`service_role` key bypasses all PostgreSQL RLS policies by design) | **YES** (by definition, but usage must be strictly constrained and audited) | **Architecture Rule**: `service_role` must only exist server-side; backend must enforce verified user ID. |
| **14. Which endpoints use `service_role`** | All DB calls in `patient.py`, `conversations.py`, `plans.py`, `patient_context.py`, `repository.py` | Only administrative background jobs and verified server-side RAG indexing | **Remediation Needed**: Patient CRUD must be user-bound. |
| **15. Whether any client can supply arbitrary `user_id`** | **YES** (Endpoints trust `user_id` parameter directly from HTTP request) | **NO** (Backend overrides/extracts `user_id` strictly from cryptographically validated token) | **Critical Vulnerability**: Must be closed immediately. |
| **16. Whether custom auth and Supabase Auth coexist** | **YES** (Dual system present) | **NO** (Single authoritative Supabase Auth identity provider) | **Architecture Debt**: Redundant code paths create security surface. |

---

## 3. Detailed Root Cause Analysis of "Invalid API key"

### The Issue
In `.env.local` (frontend) and `.env` (backend):
- `NEXT_PUBLIC_SUPABASE_URL=https://ubvzldfxhvttsqxpnkll.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidnpsZGZ4aHZ0dHNxeHBua2xsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxOTMyMTYsImV4cCI6MjMwMDc2OTIxNX0.X-placeholder-anon`

### Technical Cause
1. The JWT string ends with `.X-placeholder-anon` which is an invalid HMAC signature.
2. When the Supabase API Gateway (Kong / GoTrue) receives this key in the `apikey` header, it verifies the HMAC-SHA256 signature using the project's secret.
3. Because the signature does not match the project secret, Supabase returns:
   ```json
   {
     "message": "Invalid API key",
     "hint": "Double check your Supabase `anon` or `service_role` API key."
   }
   ```
4. Rather than diagnosing and providing a valid Supabase project key or local Supabase emulator instance, a parallel custom authentication router was introduced.

---

## 4. Remediation Architecture Plan

```mermaid
flowchart TD
    subgraph Client [Frontend Browser]
        UI[Tamargi.ai Next.js App]
        SupaClient[Supabase Client SDK]
    end

    subgraph SupaAuth [Supabase Cloud / Auth Provider]
        GoTrue[Supabase Auth / GoTrue]
        AuthDB[(auth.users)]
    end

    subgraph BackendAPI [FastAPI Backend]
        AuthDep[JWT Verification Dependency]
        Endpoints[Protected Endpoints /chat, /patient/*, /plans, /conversations]
    end

    subgraph Postgres [Supabase PostgreSQL Database]
        RLS[Row Level Security auth.uid()]
        AppDB[(public.profiles, public.medication_plans, etc.)]
    end

    UI -->|1. signUp / signInWithPassword| SupaClient
    SupaClient -->|2. Direct Auth Request| GoTrue
    GoTrue -->|3. Validate & Hash bcrypt| AuthDB
    GoTrue -->|4. Return Supabase Session JWT| SupaClient
    
    UI -->|5. API Request with Bearer JWT| BackendAPI
    BackendAPI -->|6. Cryptographically Verify JWT| AuthDep
    AuthDep -->|7. Extract Verified sub UUID| Endpoints
    
    Endpoints -->|8. User-Scoped Query with auth.uid()| Postgres
    Postgres -->|9. Enforce RLS Policies| RLS
    RLS -->|10. Return User Data| AppDB
```

---

## 5. Summary of Actions Required

1. **Delete Custom Auth Router**: Remove `backend/app/api/auth.py` and unregister it from `backend/app/main.py`.
2. **Standardize Frontend Auth Context**: Re-point `frontend/lib/auth-context.tsx` directly to `supabase.auth.signUp()`, `supabase.auth.signInWithPassword()`, `supabase.auth.signOut()`, and `supabase.auth.resetPasswordForEmail()`.
3. **Implement Backend Supabase JWT Verification**:
   - Create `backend/app/auth/supabase_auth.py` with an `AuthenticatedUser` dependency.
   - Verify incoming `Authorization: Bearer <token>` against the Supabase JWT secret / JWKS or `supabase.auth.get_user(token)`.
   - Inject the verified `user.id` into all route handlers.
4. **Refactor Protected Endpoints**:
   - `GET /api/patient/profile`: use `authenticated_user.id`.
   - `POST /api/patient/profile`: use `authenticated_user.id`.
   - `POST /api/patient/conditions`: use `authenticated_user.id`.
   - `POST /api/patient/allergies`: use `authenticated_user.id`.
   - `POST /api/patient/medications`: use `authenticated_user.id`.
   - `GET /api/conversations`: use `authenticated_user.id`.
   - `POST /api/chat`: use `authenticated_user.id`.
   - `GET /api/plans`: use `authenticated_user.id`.
   - `POST /api/plans`: use `authenticated_user.id`.
   - `GET /api/plans/{id}`: enforce `plan["user_id"] == authenticated_user.id`.
5. **Keep Public QR Route Exception**: `/api/plans/verify/{token}` remains public and authorizes strictly through the verification token without exposing private user identity.
