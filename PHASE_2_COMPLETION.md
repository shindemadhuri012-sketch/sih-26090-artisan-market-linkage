# PHASE 2 COMPLETION REPORT
## SIH 26090 — Artisan Market Linkage & Smart Seller Matching
### Phase 2: Authentication, RBAC, Core Profile APIs & Craft Passport Verification

---

## 1. Executive Summary of Phase 2

Phase 2 of **SIH 26090: Artisan Market Linkage & Smart Seller Matching** has been executed to completion in strict alignment with the approved system architecture, security strategy, and database specifications.

This phase establishes the identity, access control, and trust verification foundation for the entire platform. It accommodates both rural artisans requiring low-friction mobile passwordless authentication and institutional/B2B buyers requiring corporate credential governance. Crucially, Phase 2 implements the **Digital Craft Passport** engine, providing non-sequential identifiers, tamper-evident cryptographic provenance hashing, self-contained QR code generation, and open public verification endpoints that protect artisan PII while demonstrating craft authenticity.

All 43 automated unit and integration tests across the repository pass cleanly (100% pass rate).

---

## 2. Completed Architecture Components

```mermaid
graph TB
    subgraph Identity & Security Core
        ARGON[Argon2id Password Hasher<br/>t=3, m=64MB, p=4]
        JWT[JWT Issuer HS256<br/>15-min TTL with jti]
        ROT[Refresh Token Rotator<br/>SHA-256 Hashed, Token Family Tracking]
        OTP[Numeric OTP Challenge Engine<br/>Rate-limited 3 attempts, 5-min TTL]
        RBAC[RBAC & Ownership Guards<br/>require_roles, check_object_ownership]
        AUDIT[Immutable Audit Logger<br/>audit_logs asynchronous persistence]
    end

    subgraph API Surface Layer
        AUTH_API["/api/v1/auth/*<br/>(7 routes)"]
        ART_API["/api/v1/artisans/*<br/>(4 routes)"]
        BUY_API["/api/v1/buyers/*<br/>(3 routes)"]
        PASS_API["/api/v1/passports/*<br/>(3 routes)"]
        VERIF_API["/api/v1/verifications/*<br/>(4 routes)"]
        PUB_API["/api/v1/public/*<br/>(1 route)"]
    end

    subgraph Trust & Provenance Core
        PASSPORT[Digital Craft Passport Generator<br/>Non-sequential CP-XXXXXXXX]
        PROV_HASH[Cryptographic Provenance Digest<br/>SHA-256 Digest of Cluster & GI metadata]
        QR_GEN[Self-Contained QR Generator<br/>Embedded Base64 PNG Data URLs]
        ADMIN_REV[Administrative KYC Review<br/>State transitions & audit events]
    end

    Identity & Security Core --> API Surface Layer
    API Surface Layer --> Trust & Provenance Core
```

1. **Security & Cryptography Core**: Argon2id password hashing, signed short-lived JWT access tokens, SHA-256 hashed refresh token storage with automatic family revocation upon reuse, and SMS/OTP challenge generation.
2. **Authorization & RBAC**: Role-based access control dependencies (`require_roles(["artisan"])`, `require_roles(["buyer"])`, `require_roles(["admin"])`) paired with object-level authorization (`check_object_ownership`) to eliminate Insecure Direct Object Reference (IDOR) vulnerabilities.
3. **Audit Engine**: Asynchronous, structured audit recording writing immutable events into the `audit_logs` entity across all authentication, profile, passport, and administrative actions.
4. **Artisan & Buyer Profile Subsystems**: Private `/me` CRUD workflows with foreign-key linkage to the master craft catalog, coupled with a sanitized public profile endpoint that strips sensitive phone numbers, addresses, and Pehchan IDs.
5. **Digital Craft Passport Engine**: Automated issuance of non-sequential public identifiers (`CP-XXXXXXXX`), cryptographic SHA-256 provenance hashes, embedded QR code generation, and public verification endpoints.
6. **Administrative Review Workflow**: Multi-state KYC verification queue (`SUBMITTED`, `UNDER_REVIEW`, `VERIFIED_APPROVED`, `REJECTED`, `REQUEST_CORRECTION`) that promotes artisan status to `GOVERNMENT_VERIFIED_GI` and propagates authenticity badges to all associated passports.
7. **Database Migrations**: Alembic revision `20260326_0002_auth_refresh_otp` adding `refresh_token_sessions`, `otp_challenges`, and extending `craft_passports` and `verifications`.

---

## 3. Table of New Files Created

| Relative File Path | Component Purpose | Lines of Code |
|---|---|---|
| `backend/alembic/versions/20260326_0002_auth_refresh_otp.py` | Alembic migration for refresh sessions, OTP challenges, and passport status | 79 |
| `backend/app/core/security.py` | Argon2id hasher, JWT encoder/decoder, SHA-256 hashers, token generators | 96 |
| `backend/app/core/permissions.py` | FastAPI auth dependencies (`get_current_user`, `require_roles`, IDOR guard) | 99 |
| `backend/app/services/audit_service.py` | Centralized asynchronous audit event logging service | 37 |
| `backend/app/schemas/auth.py` | Pydantic v2 schemas for registration, login, token refresh, and OTP flows | 80 |
| `backend/app/schemas/artisan.py` | Pydantic v2 schemas for artisan profile CRUD and sanitized public views | 64 |
| `backend/app/schemas/buyer.py` | Pydantic v2 schemas for buyer profile CRUD and procurement preferences | 63 |
| `backend/app/schemas/passport.py` | Pydantic v2 schemas for craft passport issuance and public verification | 54 |
| `backend/app/schemas/verification.py` | Pydantic v2 schemas for KYC document submission and admin review actions | 55 |
| `backend/app/api/v1/endpoints/auth.py` | 7 auth routes (register, login, refresh, logout, otp/request, otp/verify, me) | 462 |
| `backend/app/api/v1/endpoints/artisans.py` | 4 artisan profile routes (GET/POST/PUT /artisans/me, GET /{id}/public) | 215 |
| `backend/app/api/v1/endpoints/buyers.py` | 3 buyer profile routes (GET/POST/PUT /buyers/me) | 154 |
| `backend/app/api/v1/endpoints/passports.py` | 3 passport routes (POST /, GET /my, POST /{id}/submit) | 217 |
| `backend/app/api/v1/endpoints/verifications.py` | 4 verification review routes (submit, my, admin/pending, admin/{id}/review) | 228 |
| `backend/app/api/v1/endpoints/public.py` | Public unauthenticated QR code resolution endpoint | 64 |
| `tests/conftest.py` | In-memory SQLite async engine, StaticPool fixtures, seeded users & tokens | 209 |
| `tests/test_auth.py` | 14 tests for registration, login, token rotation, reuse detection, logout, OTP | 299 |
| `tests/test_rbac.py` | 8 tests for role isolation, unauthenticated access, tampered JWTs, IDOR | 124 |
| `tests/test_profiles.py` | 2 integration tests for artisan/buyer lifecycle & sanitized public views | 146 |
| `tests/test_passports_and_verifications.py` | 3 integration tests for passport issuance, QR, and admin review approval/rejection | 205 |
| `frontend/src/app/login/page.tsx` | Next.js interactive dual-mode login page (Password and SMS OTP) | 301 |
| `frontend/src/app/register/page.tsx` | Next.js registration page with E.164 validation and role selection | 204 |
| `frontend/src/app/artisan/profile/page.tsx` | Next.js artisan workspace with KYC upload and Craft Passports with QR codes | 307 |
| `frontend/src/app/buyer/profile/page.tsx` | Next.js buyer procurement profile management page | 205 |
| `frontend/src/app/passport/[id]/page.tsx` | Next.js public Craft Passport QR scan verification view | 172 |
| `docs/authentication.md` | In-depth technical architecture for authentication and token sessions | 120 |
| `docs/rbac.md` | Role-based access control matrix and IDOR defense engineering | 84 |
| `docs/profiles.md` | Profile management specifications, craft linkage, and privacy boundaries | 87 |
| `docs/craft_passport.md` | Craft Passport issuance, cryptographic hashing, and QR generation guide | 107 |
| `docs/verification_workflow.md` | KYC and GI document review workflow and state transition guide | 109 |
| `docs/security_notes.md` | Threat modeling, OWASP Top 10 mitigation, and deployment hardening guide | 55 |

---

## 4. Table of Modified Files

| Relative File Path | Nature of Changes | Current Line Count |
|---|---|---|
| `backend/app/models/auth.py` | Added `RefreshTokenSession` and `OTPChallenge` models, relationships on User | 115 |
| `backend/app/models/craft.py` | Added `status` column to `CraftPassport` with lifecycle states | 80 |
| `backend/app/models/artisan.py` | Added `admin_notes` and `decision_date` columns to `Verification` | 64 |
| `backend/app/models/__init__.py` | Re-exported `RefreshTokenSession` and `OTPChallenge` (25 tables in metadata) | 45 |
| `backend/app/api/v1/router.py` | Mounted `auth`, `artisans`, `buyers`, `passports`, `verifications`, `public` | 26 |
| `tests/test_models.py` | Updated assertions to verify all 25 registered entity tables in metadata | 115 |

---

## 5. Authentication System Architecture & Test Results

The platform implements dual authentication channels:
1. **Password Authentication**: For registered artisans and institutional buyers.
2. **Passwordless Mobile OTP**: For rural artisans via E.164 phone numbers with 5-minute cryptographic challenges.

### Test Results (`tests/test_auth.py`):
- `test_artisan_registration_success`: PASSED (valid E.164 mobile, artisan role, default active status).
- `test_buyer_registration_success`: PASSED (valid email + phone, buyer role).
- `test_registration_duplicate_phone`: PASSED (409 Conflict returned on duplicate mobile registration).
- `test_registration_validation_rules`: PASSED (422 returned on non-E.164 format, weak passwords < 8 chars, and unauthorized self-assignment of admin role).
- `test_login_by_phone_success`: PASSED (returns access_token, refresh_token, bearer type, user UUID).
- `test_login_by_email_success`: PASSED (authenticates buyer by email address).
- `test_login_invalid_password`: PASSED (returns 401 Unauthorized, records `LOGIN_FAILED` audit event).
- `test_login_inactive_user`: PASSED (returns 403 Forbidden for suspended/disabled accounts).
- `test_get_me_profile`: PASSED (returns authenticated user profile data).
- `test_get_me_unauthorized`: PASSED (returns 401 Unauthorized when Bearer token is omitted).
- `test_refresh_token_rotation_flow`: PASSED (issues new access/refresh pair, invalidates old token).
- `test_refresh_token_reuse_detection`: PASSED (replay of rotated token invalidates entire family, returns 401).
- `test_logout_session_revocation`: PASSED (revokes active refresh session, blocks subsequent refresh).
- `test_otp_challenge_and_verification_flow`: PASSED (handles OTP generation, invalid code rejection, single-use consumption, and account auto-provisioning).

---

## 6. Secure Password Handling Verification

Password security conforms to modern NIST and OWASP cryptographic requirements:
- **Algorithm**: `Argon2id` via `argon2-cffi`.
- **Configuration**:
  - `time_cost = 3` iterations
  - `memory_cost = 65536 KiB` (64 MiB RAM requirement per hash)
  - `parallelism = 4` parallel execution threads
  - `hash_len = 32` bytes
  - `salt_len = 16` bytes cryptographic random salt
- **Verification Evidence**:
  - Validated by 14 passing automated tests in `tests/test_auth.py`.
  - Passwords are encrypted before database insertion; zero plaintext passwords appear in database dumps or telemetry logs.
  - Constant-time verification prevents side-channel timing analysis attacks.

---

## 7. Access & Refresh Token Architecture

- **Access Tokens**:
  - Compact JWT signed with `HS256`.
  - Expiry: 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 15`).
  - Claims: `sub` (User UUID), `role`, `iat`, `exp`, `jti` (unique cryptographic token ID).
- **Refresh Tokens & Family Rotation**:
  - 48-byte cryptographically secure random token generated via `secrets.token_urlsafe(48)`.
  - Only the **SHA-256 digest** (`token_hash`) is persisted in `refresh_token_sessions`.
  - Every refresh request rotates the token: marks the presented token `is_revoked = True` and creates a new token session linked to the same `token_family`.
- **Theft & Reuse Defense**:
  - If a revoked token is presented to `POST /api/v1/auth/refresh`, the system detects an unauthorized replay attempt.
  - All sessions across the `token_family` are immediately marked `is_revoked = True`.
  - A `TOKEN_REUSE_DETECTED` security alert is written to `audit_logs`, and the caller is denied with `401 Unauthorized`.

---

## 8. OTP / Passwordless Authentication Foundation

Designed specifically for Indian rural artisans with low digital literacy:
- **Phone Standard**: E.164 international format (e.g. `+919876543210`), validated via regex `^\+[1-9]\d{7,14}$`.
- **Challenge Security**:
  - Generates 6-digit cryptographically random numeric code (`secrets.randbelow`).
  - Stores SHA-256 hash in `otp_challenges` entity.
  - Expiry: 5 minutes.
  - Enforces a maximum of 3 attempts before the challenge is permanently consumed and locked.
- **Account Auto-Provisioning**:
  - On first-time phone verification, if the artisan user does not exist, an active `artisan` user is automatically provisioned and issued authentication tokens immediately.
- **Development Testing Facility**: In `development` mode, the generated OTP code is surfaced in `dev_otp_code` to allow end-to-end automated test suites to execute deterministically without third-party SMS gateway dependencies.

---

## 9. RBAC Matrix & Enforcement Test Results

Access control is enforced at both the role level and the object level:

| Route | Minimum Role | Object Ownership Check | Test Case | Status |
|---|---|---|---|---|
| `GET/POST/PUT /artisans/me` | `artisan` | Bound to `current_user.id` | `test_buyer_forbidden_from_artisan_endpoints` | PASSED (403) |
| `GET/POST/PUT /buyers/me` | `buyer` | Bound to `current_user.id` | `test_artisan_forbidden_from_buyer_endpoints` | PASSED (403) |
| `GET /verifications/admin/pending` | `admin` | Global administrative scope | `test_artisan_forbidden_from_admin_review` | PASSED (403) |
| `POST /verifications/admin/{id}/review` | `admin` | Global administrative scope | `test_buyer_forbidden_from_admin_review` | PASSED (403) |
| `POST /passports/{id}/submit` | `artisan` | Verified artisan owns passport | `test_idor_defense_cross_artisan_passport_submission` | PASSED (403) |
| All protected routes | Any authenticated | Missing Bearer token | `test_unauthenticated_request_rejected` | PASSED (401) |
| All protected routes | Any authenticated | Forged / modified JWT | `test_tampered_jwt_token_rejected` | PASSED (401) |

---

## 10. Artisan Profile API Capabilities & Test Results

- **Private Management (`/api/v1/artisans/me`)**:
  - `GET`: Retrieves private artisan details (capacity, cooperative, Pehchan card, street address, verification status).
  - `POST`: Creates initial artisan profile linked to master `crafts.id`. Rejects non-existent craft IDs (`400 Bad Request`) and duplicate creations (`409 Conflict`).
  - `PUT`: Updates production capacity, cooperative membership, or geographic location.
- **Sanitized Public Profile (`/api/v1/artisans/{id}/public`)**:
  - Returns only safe, public discoverability attributes: artisan full name, origin state, origin district, primary craft title, years of experience, and verification status.
  - Strictly omits personal contact numbers, street addresses, pincodes, and Pehchan IDs.
- **Test Evidence**: `tests/test_profiles.py::test_artisan_profile_lifecycle_and_sanitized_public_view` PASSED.

---

## 11. Buyer Profile API Capabilities & Test Results

- **Private Management (`/api/v1/buyers/me`)**:
  - `GET`: Retrieves company profile, GSTIN, verified buyer status, and typical order volume.
  - `POST`: Initializes buyer profile. Enforces valid taxonomy (`RETAIL_CURATOR`, `INSTITUTIONAL_GIFTING`, `GOVERNMENT_GEM`, `EXPORT_AGGREGATOR`). Rejects duplicate creations (`409 Conflict`).
  - `PUT`: Updates procurement volume and business attributes.
- **Test Evidence**: `tests/test_profiles.py::test_buyer_profile_lifecycle` PASSED.

---

## 12. Craft Passport Verification System Architecture

The **Digital Craft Passport** provides verifiable provenance for authentic crafts:
1. **Issuance (`POST /api/v1/passports/`)**:
   - Generates non-sequential public ID `CP-` + 16 uppercase hex characters (e.g., `CP-FE7054110FD37600`).
   - Computes SHA-256 provenance hash: `SHA256(artisan_id:craft_id:public_id:gi_tag_number)`.
   - Generates embedded base64 PNG QR code data URI pointing to the public verification URL.
   - Status defaults to `DRAFT`.
2. **Artisan Passport Listing (`GET /api/v1/passports/my`)**:
   - Lists all passports issued to the artisan with eager-loaded craft metadata.
3. **Passport Review Submission (`POST /api/v1/passports/{id}/submit`)**:
   - Transitions state from `DRAFT` to `SUBMITTED`.
   - Enforces IDOR check: only the artisan who owns the passport can submit it.
4. **Public Verification Endpoint (`GET /api/v1/public/passports/{public_id}`)**:
   - Resolves passport without requiring authentication.
   - Returns craft name, GI tag number, origin state, origin district, cultural heritage summary, traditional raw materials, provenance hash, and validity badge.
   - Zero private PII is exposed to scanning consumers.
- **Test Evidence**: `tests/test_passports_and_verifications.py::test_passport_lifecycle_and_public_verification` PASSED.

---

## 13. Verification Review Workflow Details

Connects field documentation with platform verification:
1. **Artisan KYC Submission (`POST /api/v1/verifications/submit`)**:
   - Artisan submits official document (`GI_AUTHORIZED_USER_CERT`, `PEHCHAN_CARD`, `COOPERATIVE_MEMBERSHIP`, `STATE_CRAFT_AWARD`).
   - Automatically transitions artisan passports from `DRAFT`/`SUBMITTED` to `UNDER_REVIEW`.
   - Status set to `SUBMITTED`.
2. **Administrator Queue (`GET /api/v1/verifications/admin/pending`)**:
   - Displays unreviewed submissions for administrative inspection.
3. **Administrator Review Action (`POST /api/v1/verifications/admin/{id}/review`)**:
   - `APPROVE`: Sets verification status to `VERIFIED_APPROVED`, updates artisan verification status to `GOVERNMENT_VERIFIED_GI`, sets `User.is_verified = True`, and promotes all associated passports to `VERIFIED`.
   - `REJECT`: Sets verification status to `REJECTED`, marks associated passports `REJECTED`, and records detailed feedback in `rejection_reason`.
   - `REQUEST_CORRECTION`: Prompts artisan to upload clearer documentation.
4. **Immutable Audit Trail**:
   - Every action records an entry in `audit_logs` capturing actor UUID, timestamp, action type, IP address, and payload.
- **Test Evidence**: `tests/test_passports_and_verifications.py::test_verification_workflow_and_admin_approval` and `test_admin_rejection_workflow` both PASSED.

---

## 14. Database Migration Details

- **Revision Identifier**: `20260326_0002`
- **Down Revision**: `20260326_0001`
- **File**: `backend/alembic/versions/20260326_0002_auth_refresh_otp.py`
- **Operations Executed**:
  1. `CREATE TABLE refresh_token_sessions` (with `id`, `user_id`, `token_hash`, `token_family`, `is_revoked`, `expires_at`, `created_at`, `user_agent`, `ip_address`).
  2. `CREATE INDEX idx_refresh_user`, `idx_refresh_family`, `idx_refresh_token_hash`.
  3. `CREATE TABLE otp_challenges` (with `id`, `phone_number`, `otp_code_hash`, `attempts`, `max_attempts`, `is_consumed`, `expires_at`, `created_at`).
  4. `CREATE INDEX idx_otp_phone`, `idx_otp_expires`.
  5. `ALTER TABLE craft_passports ADD COLUMN status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL`.
  6. `CREATE INDEX idx_craft_passports_status ON craft_passports (status)`.
  7. `ALTER TABLE verifications ADD COLUMN admin_notes TEXT`.
  8. `ALTER TABLE verifications ADD COLUMN decision_date TIMESTAMP WITH TIME ZONE`.
- **Validation**: Verified with offline SQL compilation (`alembic upgrade head --sql`) and runtime in-memory execution.

---

## 15. Complete Test Suite Results

### Execution Command: `python -m pytest tests/`
**Result Summary**: **43 passed, 0 failed, 1 warning (starlette deprecation notice) in 14.62s**

| Test Module | Tests | Passing | Purpose |
|---|---|---|---|
| `tests/test_api_health.py` | 2 | 2 | API initialization, diagnostic probes, and root endpoint |
| `tests/test_auth.py` | 14 | 14 | Registration, Argon2id login, JWT, refresh rotation, reuse detection, OTP |
| `tests/test_config.py` | 2 | 2 | Environment settings, JWT algorithms, database URLs |
| `tests/test_deduplication.py` | 3 | 3 | Artisan phone and GI tag number deduplication pipelines |
| `tests/test_ingestion_validation.py` | 5 | 5 | Master craft and artisan ingestion schema validations |
| `tests/test_models.py` | 2 | 2 | Metadata verification of all 25 tables and foreign key integrity |
| `tests/test_passports_and_verifications.py` | 3 | 3 | Passport issuance, QR generation, admin approval and rejection |
| `tests/test_profiles.py` | 2 | 2 | Artisan/buyer `/me` lifecycle and public profile sanitization |
| `tests/test_provenance.py` | 2 | 2 | Data provenance levels (`GOVERNMENT_REGISTRY`, `USER_DECLARED`) |
| `tests/test_rbac.py` | 8 | 8 | Role boundaries, unauthenticated access, tampered tokens, IDOR defense |
| **TOTAL** | **43** | **43** | **100% Pass Rate across all unit and integration tests** |

---

## 16. Frontend Verification Pages Summary

Five dedicated frontend pages have been created in `frontend/src/app/` using React and Next.js App Router:
1. `login/page.tsx`: Interactive sign-in page supporting both credential login and passwordless SMS OTP login with development code hints.
2. `register/page.tsx`: Role-aware registration interface with E.164 phone validation, role toggle (Artisan vs Buyer), and preferred language selector.
3. `artisan/profile/page.tsx`: Artisan workspace displaying profile details, verification badge, KYC document upload form, and issued digital Craft Passports with live scannable QR codes.
4. `buyer/profile/page.tsx`: Buyer workspace displaying company credentials, buyer category badge, GSTIN, and editable procurement batch preferences.
5. `passport/[id]/page.tsx`: Public Craft Passport verification page resolving `CP-XXXXXXXX` IDs, displaying authenticity badges, GI registry details, craft heritage summaries, and cryptographic signatures.

---

## 17. Documentation Files Created

The documentation suite in `docs/` has been expanded with six comprehensive, technical markdown documents:
1. `docs/authentication.md` (120 lines): Detailed authentication flow, Argon2id specs, JWT structure, and refresh token rotation mechanics.
2. `docs/rbac.md` (84 lines): Complete permissions matrix, dependency factories, and IDOR defense principles.
3. `docs/profiles.md` (87 lines): Artisan and buyer profile architectures, schema mappings, and privacy boundaries.
4. `docs/craft_passport.md` (107 lines): Craft Passport issuance, non-sequential UUIDs, cryptographic digests, and QR code embedding.
5. `docs/verification_workflow.md` (109 lines): KYC document taxonomy, administrator review queue, and audited state transitions.
6. `docs/security_notes.md` (55 lines): Threat modeling, OWASP Top 10 mitigation mappings, and production hardening checklist.

---

## 18. Security Verification Summary

1. **IDOR Defenses**: Every resource access point verifies either direct object ownership (`artisan.user_id == current_user.id`) or admin authorization. Tested explicitly in `test_idor_defense_cross_artisan_passport_submission`.
2. **PII Leakage Prevention**: Public endpoints (`GET /artisans/{id}/public` and `GET /public/passports/{public_id}`) strictly filter out phone numbers, street addresses, pincodes, and financial identifiers.
3. **Input Validation**: All incoming requests are strictly validated using Pydantic v2 schemas with E.164 phone regex enforcement, minimum password lengths (8 characters), and explicit enum constraints on `buyer_type` and `document_type`.
4. **Token Security**: Passwords hashed with Argon2id; refresh tokens stored exclusively as SHA-256 hashes; automatic family invalidation on detected token reuse.

---

## 19. Known Limitations & Deferred Items (Phase 3+ Only)

In strict adherence to the project boundary rules, the following capabilities have been deliberately deferred:
- **Product Digitization & Multilingual Voice Cataloguing**: Deferred to Phase 3.
- **Fair-Price Intelligence Engine & Cost Breakdown Estimators**: Deferred to Phase 4.
- **Semantic Vector Embeddings & Explainable Buyer-Artisan Matching**: Deferred to Phase 5.
- **Marketplace RFQ & Order Negotiation Chat**: Deferred to Phase 6.
- **Production SMS Gateway Integration (Twilio/Gupshup)**: In Phase 2, OTP generation and verification use local cryptographic generation with dev-mode visibility; live telecom gateway credentials will be integrated in Phase 7 (Deployment).

---

## 20. Explicit Readiness Declaration for Phase 3

Phase 2 is **100% complete and fully verified**.

The repository provides a secure, audited identity layer, robust RBAC boundaries, artisan and buyer profile management, and a cryptographically sound Craft Passport verification engine.

The platform is **architecturally and technically ready to proceed to Phase 3: Product Digitization, AI-Assisted Cataloguing, Voice/Multilingual Interaction Foundation & Media Pipeline**.
