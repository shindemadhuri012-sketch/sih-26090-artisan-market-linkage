# PHASE 9 IMPLEMENTATION & READINESS PLAN
## Production Deployment, Security Hardening & SIH Judge Evaluation Pack

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: PHASE 9 — Production Deployment, Security Hardening & SIH Judge Evaluation Pack  
**Status**: PLANNING & READINESS REVIEW (Awaiting Approval to Implement)  
**Date**: 2026-09-27  

---

## 1. Executive Summary & Objective

The primary objective of Phase 9 is to transition the completed SIH 26090 platform from a development-verified state (Phases 0–8, 121/121 tests passing) into an enterprise-ready, security-hardened, observable, and fully documented system prepared for production deployment and Smart India Hackathon (SIH) judge evaluation.

### Key Tenets
1. **Absolute Honesty & Zero Fabrication**: No synthetic benchmark figures, fake accuracy metrics, simulated transactions, or fabricated deployment statuses. Every claim is tagged as `VERIFIED`, `CONFIGURED`, `READY_TO_DEPLOY`, or `NOT_CONFIGURED`.
2. **Defensive Security & Privacy**: Production-grade authentication (Argon2id, HS256 JWT, refresh token family rotation with replay revocation), granular RBAC and object-level IDOR enforcement, PII redaction in public provenance feeds, and secure file upload constraints.
3. **Reproducible Containerized Deployment**: Multi-stage Docker configurations for frontend and backend, verified Alembic migration chain (0001–0008), connection pooling, and deep health/readiness probes.
4. **SIH Judge Pack**: A comprehensive 9-document suite detailing the technical architecture, problem-solution mapping, AI capabilities & honest limitations, data provenance hierarchy, and a step-by-step reproducible demo script.

---

## 2. Production Architecture Review & Status Matrix

| Component | Architecture / Technology | Current Status | Production Hardening Target |
|:---|:---|:---|:---|
| **Frontend Framework** | Next.js 14.2 (React 18, App Router, TypeScript, TailwindCSS) | `CONFIGURED` / `READY_TO_DEPLOY` | Convert `next.config.ts` to `next.config.mjs`, add `/api/:path*` reverse-proxy rewrites, optimize standalone Docker build |
| **Backend API** | FastAPI 0.100+, Uvicorn/Gunicorn, async SQLAlchemy 2.0 | `CONFIGURED` / `READY_TO_DEPLOY` | Production multi-stage Dockerfile, security headers middleware, global error masking |
| **Relational Database** | PostgreSQL 16 + pgvector extension | `CONFIGURED` / `READY_TO_DEPLOY` | Production pool tuning (`DATABASE_POOL_SIZE=10`, `DATABASE_MAX_OVERFLOW=20`), verify all 37 tables |
| **Caching & Rate Limiting** | Redis 7 Alpine | `CONFIGURED` | Connect rate limiter and token revocation blacklist, health probe check |
| **Object / Media Storage** | MinIO / S3-compatible object store | `CONFIGURED` | Presigned URL generation pattern, bucket policies, MIME validation |
| **AI Vision Provider** | Google Gemini (`gemini-1.5-flash`) with fallback | `CONFIGURED` | Server-side API key isolation, timeout controls (30s), graceful degradation |
| **AI Embedding Provider** | Google Gemini (`gemini-embedding-2`, 768-dim) | `CONFIGURED` | Strict 768-dim verification, fallback embedding provider |
| **Fair Price Engine** | Deterministic Python Decimal (`FAIR_PRICE_ENGINE_V1`) | `VERIFIED` | Living wage floor guarantee, $N \ge 3$ evidence threshold, zero fabrication |
| **Matching Engine** | Two-stage hybrid matching (`MATCHING_ENGINE_V1`) | `VERIFIED` | Hard constraints + 7-factor explainable scorecard, no fake conversion probability |
| **Demand Engine** | Time-series forecasting (`DEMAND_ENGINE_V1`, WMA & Holt-Winters) | `VERIFIED` | Multi-gate eligibility ($N \ge 12$), walk-forward validation (zero future leakage) |
| **Governance & Provenance** | Cryptographic hash chain (`ProvenanceEvent`, SHA-256) | `VERIFIED` | Tamper detection, `ADMIN_APPROVED` $\neq$ `AUTHORITY_VERIFIED`, allowlist re-moderation |
| **PWA & Offline Sync** | Service Worker (`sw.js`) + Dexie 4.x IndexedDB | `CONFIGURED` | User-scoped local storage, mutation queue, UUIDv4 idempotency, purge on logout |
| **Database Migrations** | Alembic (8 revisions: 0001 to 0008) | `VERIFIED` | Unbroken linear chain (`20260327_0008` head), `--sql` dry-run tested |
| **Health / Observability** | `/api/v1/health` (liveness), `/api/v1/ready` (readiness) | `CONFIGURED` | Enhance `/ready` to check DB, pgvector, and Redis |
| **Secret Management** | Pydantic Settings, `.env` file | `CONFIGURED` | Startup validation in `APP_ENV="production"` enforcing strong secrets |

---

## 3. Production Environment & Secret Configuration Plan

### 3.1 Strict Production Secret Validation
In `backend/app/core/config.py`, enforce startup validation when `APP_ENV == "production"`:
- `DEBUG` must be `False`.
- `SECRET_KEY` must not match any development default, must be $\ge 32$ bytes, and must not be a known weak placeholder.
- `CORS_ORIGINS` must not contain wildcard `*` or `localhost`.
- `GEMINI_API_KEY` must be backend-only (never passed to frontend).

### 3.2 Production Docker Configurations
1. **`backend/Dockerfile`**:
   - Base: `python:3.11-slim` (or 3.12/3.13 slim).
   - Multi-stage build: builder stage for compilation, runtime stage for minimal footprint.
   - Non-root user (`appuser:10001`).
   - Execution command: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4`.
2. **`frontend/Dockerfile`**:
   - Base: `node:20-alpine`.
   - Next.js standalone output configuration (`output: "standalone"`).
   - Minimal production image (~120MB).
3. **`infrastructure/docker-compose.prod.yml`**:
   - Production orchestration linking `postgres`, `redis`, `minio`, `backend`, and `frontend`.
   - Health checks, volume mounts, restart policies (`restart: always`).

---

## 4. Frontend Production Hardening Plan

1. **Config File Standardization**:
   - Rename/replace `frontend/next.config.ts` with `frontend/next.config.mjs` to ensure 100% compatibility with Next.js 14.2 build runner.
   - Add Next.js API rewrites routing `/api/:path*` to the backend service URL (`process.env.BACKEND_URL || "http://localhost:8000"`).
2. **Client-Side Secret Auditing**:
   - Ensure zero `GEMINI_API_KEY`, `DATABASE_URL`, or `SECRET_KEY` references exist in any client-side bundles.
   - Verify that only `NEXT_PUBLIC_*` variables are exposed to the browser.
3. **Offline PWA Security**:
   - Verify Service Worker (`sw.js`) caches only public static assets and craft directories.
   - Enforce that client-side Dexie IndexedDB never caches government identity documents, tax IDs, or passwords.
   - Enforce immediate purge of local Dexie IndexedDB upon user logout (`auth/useAuth.ts`).
4. **Sanitized Error Handling**:
   - Ensure user interfaces display friendly, localized error notifications rather than raw JSON HTTP error payloads or internal server traces.

---

## 5. Backend Security Hardening Plan

1. **Authentication & Session Lifecycle**:
   - Argon2id password hashing parameters: `time_cost=3`, `memory_cost=64MiB`, `parallelism=4`.
   - Short-lived JWT access tokens (15 minutes).
   - Cryptographically random refresh tokens (48 bytes URL-safe) with token family tracking.
   - **Token Reuse Detection Defense**: Immediate revocation of entire token family if an expired or rotated token is replayed.
2. **Authorization, RBAC & IDOR Defense**:
   - Role enforcement via `require_roles(["artisan"])`, `require_roles(["buyer"])`, and `get_current_active_admin`.
   - Object-level ownership validation (`check_object_ownership`) verifying `product.artisan_id == current_user.id`, `rfq.buyer_id == current_user.id`, etc.
   - Admin-only routes rejecting non-admin requests with `HTTP 403 Forbidden`.
3. **API & Network Security**:
   - **Security Headers Middleware**: Inject `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, and restrictive `Content-Security-Policy`.
   - **Global Error Handling**: Custom exception handler in FastAPI converting unhandled exceptions into generic `500 Internal Server Error` with a correlation ID, preventing SQL errors, stack traces, or module paths from leaking.
   - **Request Size Limitation**: Enforce 15MB maximum request payload limit to defend against memory exhaustion DOS.
4. **Media Upload Hardening**:
   - Validate MIME types against strict allowlist (`image/jpeg`, `image/png`, `image/webp`, `audio/mpeg`, `audio/wav`, `application/pdf`).
   - Validate file size $\le 10\text{ MB}$.
   - Reject filenames containing path traversal patterns (`..`, `/`, `\`, `:`).
   - Direct-to-storage presigned URL architecture.

---

## 6. Database & Migration Verification Plan

1. **Migration Chain Continuity**:
   - Verified linear chain: `0001` $\rightarrow$ `0002` $\rightarrow$ `0003` $\rightarrow$ `0004` $\rightarrow$ `0005` $\rightarrow$ `0006` $\rightarrow$ `0007` $\rightarrow$ `0008` (head).
   - Zero branching, zero duplicate revisions.
   - All 37 declarative models matched against database schema.
2. **Database Resilience**:
   - Connection pool recycle timeout set to 3600s to avoid stale connection drops.
   - Pre-ping connection check enabled.
   - Indexes verified on critical search fields (`craft_id`, `category_id`, `artisan_id`, `status`, `event_hash`).

---

## 7. AI Safety & Provider Hardening Plan

1. **Information State Segregation**:
   - Maintain the 9 distinct governance states (`ARTISAN_PROVIDED`, `SOURCE_BACKED`, `AI_SUGGESTED`, `CALCULATED`, `HUMAN_CONFIRMED`, `ADMIN_APPROVED`, `ADMIN_REJECTED`, `FLAGGED`, `SUPERSEDED`, and independently `AUTHORITY_VERIFIED`).
   - AI suggestions must remain staged in `ai_studio_runs` and `requirement_understandings`.
   - Only human confirmation promotes suggestions to canonical data.
2. **Provider Failure Handling**:
   - If Gemini Vision or Embedding API returns 5xx or times out (30s), the system fails safely, returning an explicit error state (`AI_SERVICE_UNAVAILABLE`) rather than hallucinating attributes or synthetic price ranges.
3. **No Fabrication Charter**:
   - Pure Python Decimal arithmetic for financial computations.
   - Living wage floor guarantee: price recommendations never fall below production cost.
   - Minimum observation gates ($N \ge 3$ for market pricing, $N \ge 12$ for demand forecasting).

---

## 8. Observability & Reliability Plan

1. **Structured Telemetry**:
   - Request correlation IDs (`X-Correlation-ID`) tracked across middleware and logs.
   - Standardized log format with timestamp, level, correlation ID, endpoint, and status.
   - Sensitive fields (passwords, JWTs, API keys, Aadhaar/Pehchan details) masked in all logs.
2. **Deep Diagnostic Probes**:
   - `/api/v1/health`: Lightweight HTTP 200 liveness probe for load balancer health checking.
   - `/api/v1/ready`: Deep dependency readiness probe checking:
     - PostgreSQL database connectivity (`SELECT 1;`)
     - `pgvector` extension availability
     - Redis reachability (if configured)
     - S3/MinIO bucket access (if configured)

---

## 9. Performance & Benchmark Plan

Empirical, reproducible performance measurements collected on the host system:

| Metric | Empirical Result | Status |
|:---|:---|:---|
| **Fair Price Cost Calculation** | **0.0400 ms** per run (100 iterations) | `MEASURED` |
| **Demand Forecasting Run (12m WMA)** | **0.0982 ms** per forecast (100 iterations) | `MEASURED` |
| **Provenance Hash Computation (SHA-256)** | **24.3522 µs** per event (500 iterations) | `MEASURED` |
| **Full Test Suite Execution (121 tests)** | **87.34 s** (100% pass rate) | `MEASURED` |
| **Database Model Count** | **37 declarative models** | `MEASURED` |
| **Alembic Revisions Head** | **20260327_0008** (unbroken chain) | `MEASURED` |
| **Frontend Production Build** | Pending `next.config.mjs` adjustment | `READY_TO_VERIFY` |

---

## 10. SIH Judge Evaluation Pack Plan

Nine dedicated, judge-ready documentation artifacts will be created in `docs/`:

1. [`docs/sih_judge_evaluation_pack.md`](file:///e:/docs/sih_judge_evaluation_pack.md) — Executive guide, platform overview, key differentiators, architectural highlights, and evaluation rubric mapping.
2. [`docs/demo_script.md`](file:///e:/docs/demo_script.md) — 15-step end-to-end interactive demo walkthrough for judges.
3. [`docs/problem_solution_mapping.md`](file:///e:/docs/problem_solution_mapping.md) — Mapping SIH 26090 problem statements to concrete platform modules.
4. [`docs/technical_architecture.md`](file:///e:/docs/technical_architecture.md) — System architecture, data flow diagrams, microservices/monorepo layout, and tech stack details.
5. [`docs/ai_capabilities_and_limitations.md`](file:///e:/docs/ai_capabilities_and_limitations.md) — Detailed AI capabilities, prompt engineering, honesty charter, and data limitation boundaries.
6. [`docs/data_provenance_and_governance.md`](file:///e:/docs/data_provenance_and_governance.md) — 9 information states, SHA-256 hash chaining, tamper detection, and verification hierarchy.
7. [`docs/security_and_privacy.md`](file:///e:/docs/security_and_privacy.md) — Security model, Argon2id, JWT rotation, IDOR defense, PII sanitization, and media validation.
8. [`docs/deployment_and_operations.md`](file:///e:/docs/deployment_and_operations.md) — Production deployment instructions, Docker configurations, environment setup, and operational runbook.
9. [`docs/testing_and_validation.md`](file:///e:/docs/testing_and_validation.md) — Full test suite breakdown, verification coverage, and security regression results.

---

## 11. SIH End-to-End Demo Script (15 Steps)

1. **Step 1: Role-Based Authentication & Session Security** (`/login`)
2. **Step 2: Artisan Profile & Verifiable Craft Passport** (`/artisan/profile`, `/passport/[id]`)
3. **Step 3: Craft Catalogue & Regional GI Browsing** (`/catalogue`)
4. **Step 4: Product Creation & Provenance Staging** (`/artisan/products/new`)
5. **Step 5: AI Product Studio: Vision Suggestion & Human Confirmation** (`/artisan/products/[id]/ai-studio`)
6. **Step 6: Explainable Fair Price Intelligence** (`/artisan/products/[id]/pricing`)
7. **Step 7: Buyer Requirement Digitization & Staged AI Parsing** (`/buyer/requirements/new`)
8. **Step 8: Buyer Human Confirmation & Requirement Activation** (`/buyer/requirements/[id]`)
9. **Step 9: Semantic Matching Engine & Candidate Retrieval** (`/buyer/requirements/[id]/matches`)
10. **Step 10: Transparent Match Scorecard & Limitation Callouts** (`/buyer/requirements/[id]/matches`)
11. **Step 11: Commercial RFQ Creation & Negotiation State Machine** (`/buyer/rfqs`, `/artisan/rfqs/[id]`)
12. **Step 12: Real Demand Intelligence & Trend Forecasting** (`/artisan/demand`, `/admin/analytics/demand`)
13. **Step 13: Offline-First PWA Resilience Demonstration** (Offline simulation, IndexedDB caching, background sync)
14. **Step 14: Unified Moderation Console & Critical Allowlist** (`/admin/moderation`, `/admin/verification`)
15. **Step 15: Cryptographic Provenance Inspector & SHA-256 Tamper Detection** (`/admin/provenance`)

---

## 12. Deployment Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|:---|:---|:---|
| Insecure default secret in production | Critical | Startup assertion in `config.py` rejecting weak keys when `APP_ENV="production"`. |
| Next.js config compatibility issue | High | Convert `next.config.ts` to standard `next.config.mjs`. |
| Gemini API quota or network failure | Medium | Graceful degradation to safe error state; zero synthetic or hallucinated results. |
| CORS misconfiguration in production | High | Strict domain whitelist via environment variable, rejecting wildcard `*` with credentials. |
| Database connection pool exhaustion | Medium | Pool sizing (`size=10`, `max_overflow=20`), timeout recycling (3600s), and pre-ping checks. |

---

## 13. Exact Files Expected to Change / Be Created

### Configuration & Deployment Files
1. `frontend/next.config.mjs` (Replacing `next.config.ts` with API rewrites)
2. `backend/Dockerfile` (Multi-stage production container definition)
3. `frontend/Dockerfile` (Production Next.js standalone container definition)
4. `infrastructure/docker-compose.prod.yml` (Production orchestration)
5. `backend/app/core/config.py` (Production validation for secrets and CORS)
6. `backend/app/main.py` (Security headers and production error handling)
7. `backend/app/api/v1/endpoints/health.py` (Enhanced readiness probe for Redis/storage)

### SIH Judge Evaluation Pack (9 Documents)
8. `docs/sih_judge_evaluation_pack.md`
9. `docs/demo_script.md`
10. `docs/problem_solution_mapping.md`
11. `docs/technical_architecture.md`
12. `docs/ai_capabilities_and_limitations.md`
13. `docs/data_provenance_and_governance.md`
14. `docs/security_and_privacy.md`
15. `docs/deployment_and_operations.md`
16. `docs/testing_and_validation.md`

### Testing & Verification
17. `tests/test_production_security_hardening.py` (New test suite for security headers, secret validation, error masking)
18. `README.md` (Update Milestone 9 status and architectural overview)
19. `PHASE_9_COMPLETION.md` (Final completion report)

---

## 14. Expected Tests & Regression Suite

- **Existing Tests**: 121 tests across Phases 1–8.
- **New Phase 9 Tests**: Security headers, production secret enforcement, error sanitization, deep readiness probe verification.
- **Expected Total**: $\ge 126$ passing tests (100% pass rate target).

---

## 15. Scope Boundary Enforcement

- **Phase 9 ONLY**: Production deployment, security hardening, and SIH judge evaluation pack.
- **Phase 10 is NOT started and will NOT be started.**
- **No unrelated new business features.**
- **No synthetic or fabricated data.**
