# SIH 26090: Artisan Market Linkage & Smart Seller Matching

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-0.5+-blue.svg)](https://github.com/pgvector/pgvector)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-orange.svg)](https://www.sih.gov.in)

A production-grade, AI-powered platform linking Indian artisans directly with enterprise, institutional, and retail buyers through intelligent product digitization, AI-assisted cataloguing, fair-price intelligence, craft provenance, explainable buyer-artisan matching, demand intelligence, voice/multilingual interaction, and low-bandwidth usability.

---

## 1. Project Overview

The core problem addressed by SIH 26090 is **intelligent market linkage between artisans and buyers**. This is not a generic e-commerce website; it is an intelligent linkage platform providing:
- **AI Artisan Profile & Craft Passport**: Verifiable craft provenance grounded in official Indian Geographical Indications (GI) and Ministry of Textiles Pehchan registrations.
- **Voice-First & Multilingual Digitization**: Multimodal catalogue creation via local dialect voice notes and product photos.
- **Transparent Fair-Price Intelligence**: Algorithmic cost-plus-margin engine ensuring artisans realize fair living wages based on actual labor hours and raw material commodity benchmarks.
- **Explainable Matching Engine**: Transparent, auditable multi-stage candidate scoring with factor scorecards (no arbitrary black-box percentages).
- **Demand Intelligence with AI Honesty**: Seasonal trend forecasting grounded in verified historical observations, with strict protocols refusing to hallucinate when data is sparse.
- **Offline-First PWA Resilience**: Local IndexedDB draft caching and background sync for rural clusters with intermittent 2G/3G connectivity.

---

## 2. Monorepo Structure

```
sih-26090-artisan-market-linkage/
├── backend/               # FastAPI async REST API & SQLAlchemy 2.0 ORM
│   ├── app/               # Core application modules (api, core, models, schemas, services)
│   ├── alembic/           # Database migration versions
│   └── requirements.txt   # Backend dependencies
├── frontend/              # Next.js 14+ App Router, React 19, TypeScript PWA
│   ├── src/app/           # Next.js App Router routes & components
│   └── package.json       # Frontend dependencies
├── ai/                    # Independent AI inference pipelines (Vision, Voice, Matching, Pricing)
├── data/                  # Real data assets, ingestion manifests & processed seeds
│   ├── raw/               # Immutable raw source downloads
│   ├── processed/         # Validated, deduplicated JSON/Parquet seeds
│   └── manifests/         # Ingestion audit receipts and checksums
├── scripts/               # Ingestion, validation, and maintenance utilities
│   └── ingestion/         # Modular ingestion pipelines (GI Registry, ODOP, Commodity Indices)
├── tests/                 # Comprehensive test suite (unit, integration, validation, deduplication)
├── infrastructure/        # Docker Compose configurations for local Postgres/pgvector & Redis
├── docs/                  # Architectural blueprints, data strategy, and technical specifications
├── .env.example           # Environment configuration template
└── PHASE_1_COMPLETION.md  # Phase 1 milestone verification report
```

---

## 3. Quickstart & Local Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 16+ with `pgvector` extension (or Docker for `infrastructure/docker-compose.yml`)
- Node.js 18+ (for frontend)

### Backend Configuration
```bash
# 1. Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Copy environment template
cp .env.example .env

# 4. Start local infrastructure (Postgres with pgvector, Redis, MinIO)
docker compose -f infrastructure/docker-compose.yml up -d

# 5. Run database migrations
cd backend
alembic upgrade head

# 6. Execute real-data ingestion (GI Registry & ODOP)
python ../scripts/ingestion/run_ingestion.py

# 7. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at `http://localhost:8000/docs`.

---

## 4. Current Milestone Status

- **Phase 0**: Architecture, Blueprint & Strategy Specification — **COMPLETED**
- **Phase 1**: Monorepo Scaffolding, Database Models, Alembic Migrations & Real Data Ingestion — **COMPLETED**
- **Phase 2**: Authentication, RBAC, Core Profile APIs & Craft Passport Verification — **COMPLETED**
- **Phase 3**: Craft Catalogue, Artisan Product Foundation & Product Data APIs — **COMPLETED**
- **Phase 4**: AI Product Studio (Image Understanding, Staged Suggestions & Human Confirmation) — **COMPLETED**
- **Phase 5**: Explainable Fair Price Intelligence (Cost Breakdown, Real Market Evidence, Defensible Price Range, Traceable Explanation & Artisan Confirmation) — **COMPLETED** (82 / 82 tests passing)
- **Phase 6**: Buyer–Artisan Semantic Matching Engine & RFQ Linkage — **COMPLETED** (97 / 97 tests passing)
- **Phase 7**: Demand Intelligence, Real Analytics & Offline-First PWA — **COMPLETED** (111 / 111 tests passing)
- **Phase 8**: Admin Moderation, Governance & Provenance Auditing — **COMPLETED** (121 / 121 tests passing)
- **Phase 9**: Production Deployment, Security Hardening & SIH Judge Evaluation Pack — **COMPLETED** (128 / 128 tests passing)
- **Phase 10**: Final Judge Demonstration, Field Pilot Readiness & Project Completion — **COMPLETED** (128 / 128 tests passing)

---

## 10. Final Judge Demonstration, Field Pilot Readiness & Project Completion (Phase 10)

Phase 10 represents the final completion milestone of the **SIH 26090** platform, consolidating all technical, governance, and verification deliverables:
- **15-Step SIH Judge Demonstration Flow ([`docs/final_sih_demo_plan.md`](docs/final_sih_demo_plan.md))**:
  - Detailed narrative script spanning 6 key actors (`PUBLIC`, `ARTISAN`, `BUYER`, `MODERATOR`, `ADMIN`, `AUDITOR`).
  - Covers every capability from craft passport browsing, staged AI cataloguing, fair-price calculation, semantic matching, RFQ negotiation, offline PWA simulation, demand forecasting, to cryptographic provenance audit.
  - Includes explicit inputs, expected API outputs, judge observation checkpoints, fallback contingency plans, and empirical host benchmark timings.
- **Field Pilot Readiness Protocol ([`docs/field_pilot_readiness.md`](docs/field_pilot_readiness.md))**:
  - Standardized protocol designed for 3 craft clusters: Jaipur (Blue Pottery), Varanasi (Zari/Brocade), and Bastar (Dhokra/Bell Metal).
  - Explicitly classified as **`PROPOSED TARGET / PILOT SUCCESS CRITERION`** (zero field pilot activity has been executed to date; platform is technically `READY_FOR_PILOT`).
  - Contains vernacular physical consent forms, 15-second audio consent protocol, offline facilitator runbooks, and strict PWA privacy rules (zero offline KYC/Aadhaar/bank document storage).
- **Data & AI Integrity Charter ([`docs/final_data_and_ai_integrity.md`](docs/final_data_and_ai_integrity.md))**:
  - Strict Zero-Fabrication Mandate: Prohibits synthetic competitor prices, simulated demand histories, phantom user profiles, or fabricated ML accuracy metrics.
  - Standardized Nine Canonical Information States (`RECORD_CONFIRMED`, `RECORD_PROVISIONAL`, `ESTIMATE_STATISTICAL`, `INSUFFICIENT_HISTORY`, `DATA_NOT_VERIFIED`, `SAMPLE_DATA_ONLY`, `DEMO_ONLY`, `PROPOSED_TARGET`, `NOT_APPLICABLE`).
  - Strict `AUTHORITY_VERIFIED` rule: Internal admin review can never grant authority status without statutory government gazette / GI certificate documentation.
- **Comprehensive Feature Capability Matrix ([`docs/final_feature_matrix.md`](docs/final_feature_matrix.md))**:
  - Itemizes 40 distinct platform capabilities mapped to code routers, database models, and test evidence.
  - Enforces the project's standardized 11-state taxonomy without marketing hyperbole.
- **Automated Test Matrix ([`docs/final_test_matrix.md`](docs/final_test_matrix.md))**:
  - 128 / 128 tests passing across 38 test files with 100% pass rate.
  - Zero test failures, zero regressions, and full coverage of RBAC, IDOR, fair pricing, semantic matching, offline sync, and provenance hash chains.
- **Master Project Handover & Runbook ([`docs/final_project_handover.md`](docs/final_project_handover.md))**:
  - Production deployment blueprints, environment variables reference, 8-revision Alembic migration runbooks, and disaster recovery procedures.
- **Definitive Completion Report ([`PHASE_10_COMPLETION.md`](PHASE_10_COMPLETION.md))**:
  - Exhaustive 23-section milestone completion certificate formally concluding the project.


---

## 5. Fair Price Intelligence Architecture (Phase 5)

The platform includes a transparent, deterministic, and evidence-grounded pricing engine (`FAIR_PRICE_ENGINE_V1`):
- **Deterministic Decimal Arithmetic**: Built exclusively with Python `Decimal` (`ROUND_HALF_UP`) ensuring zero floating-point drift.
- **Cost-Plus Economic Foundation**: Sums raw materials, labor (hourly living wage or fixed piece rate), workshop overhead, packaging, and freight.
- **Living Wage Floor Guarantee**: Enforces `floor_price >= unit_production_cost` under all market conditions; the engine never recommends selling below production cost.
- **Strict Evidence Standards**: Requires $N \ge 3$ verified, comparable market price observations (e.g., government e-portals, verified cooperatives, retail benchmarks) to unlock market-based ranges; falls back cleanly to a Cost-Only Baseline when evidence is sparse ($N < 3$).
- **Strict No-Fabrication Policy**: Zero synthetic competitor prices, simulated demand curves, or hallucinated margin targets.
- **Traceable Step-by-Step Explanation**: Every calculation outputs an ordered audit trail with formulas, input values, and mathematical transformations.
- **Five Information States**: Segregates `ARTISAN_PROVIDED`, `SOURCE_BACKED`, `AI_SUGGESTED`, `CALCULATED`, and `HUMAN_CONFIRMED`.
- **Artisan Price Sovereignty**: Fair price analysis outputs are advisory only; only the artisan can confirm and publish their final price.

---

## 6. Buyer–Artisan Semantic Matching Engine & RFQ Linkage (Phase 6)

The platform implements an institutional market linkage engine (`MATCHING_ENGINE_V1`):
- **Google `gemini-embedding-2`**: Configured with `output_dimensionality=768` for 768-dimensional normalized semantic representations of products and buyer requirements (`EmbeddingVector(dim=768)`). Zero deprecated model usage (`text-embedding-004` shut down Jan 14, 2026).
- **Two-Stage Hybrid Matching**:
  - *Stage 1*: Deterministic elimination against hard constraints (craft identity, capacity feasibility, strict MOQ ceiling, GI requirements).
  - *Stage 2*: 7-component multi-criteria scoring ($S_{\text{sem}}, S_{\text{craft}}, S_{\text{mat}}, S_{\text{cap}}, S_{\text{price}}, S_{\text{lead}}, B_{\text{prov}}$) with dynamic re-weighting for omitted optional criteria.
- **Match Score vs. Conversion Probability**: Score is strictly a multi-criteria compatibility metric ($0.0 \le S \le 1.0$), never a synthetic "likelihood to convert".
- **Transparent Scorecard & Explainability Matrix**: Factor breakdown sliders, positive justifications, honest limitations, and data sufficiency tags (`COMPLETE`, `PARTIAL_PROFILE`, `UNVERIFIED_DATA`).
- **Staged AI Requirement Understanding**: Free-text procurement briefs are parsed into structured suggestions, staged in `requirement_understandings`, and promoted only after explicit buyer human confirmation.
- **Commercial RFQ Linkage & Negotiation**:
  - Verifiable RFQ reference numbers (`RFQ-YYYYMMDD-XXXX`).
  - Negotiation state machine (`SENT` $\rightarrow$ `VIEWED` $\rightarrow$ `NEGOTIATION` $\rightarrow$ `ACCEPTED` / `DECLINED`).
  - Artisan counter-offer terms (unit price, lead time, notes) and buyer decision workflow.
  - Server-side party-to-transaction IDOR verification on all endpoints.

---

## 7. Demand Intelligence, Real Analytics & Offline-First PWA (Phase 7)

The platform implements statistical demand forecasting and offline-first PWA resilience:
- **Real Demand Signals Only**: Demand indicators are grounded strictly in real verified transactional evidence (`TIER_1_TRANSACTIONAL`: orders, tenders; `TIER_2_COMMERCIAL_INTENT`: RFQs, inquiries; `TIER_3_MACRO_INDICATOR`: export shipments). Page views, clicks, and social likes are strictly excluded from demand volume metrics. Zero fabricated trends or synthetic histories.
- **Strict Multi-Gate Forecast Eligibility**: $N \ge 12$ chronological observation periods is a mandatory minimum, combined with temporal gap validation ($<20\%$ missing data) and chronological continuity. Returns explicit states: `INSUFFICIENT_HISTORY`, `INSUFFICIENT_DATA_QUALITY`, or `FORECAST_UNAVAILABLE`.
- **Zero Future-Leakage Evaluation**: Strict chronological split (train $\rightarrow$ validation $\rightarrow$ test) using walk-forward cross-validation. Out-of-sample MAPE and RMSE metrics are computed strictly on held-out points. No random shuffling or future leakage.
- **Statistical Forecasting Models (`DEMAND_ENGINE_V1`)**: Classical Weighted Moving Average (WMA) and Additive Holt-Winters exponential smoothing with residual standard error prediction intervals. Forecasts are explicitly tagged as advisory projections (`information_state='FORECAST'`), never verified facts.
- **Offline-First PWA Architecture**:
  - Service Worker (`sw.js`) implementing `CacheFirst` for static app assets, `StaleWhileRevalidate` for craft catalogues, and `NetworkOnly` bypass for transactional APIs.
  - Client-side IndexedDB database (`sih26090_offline_db` via Dexie 4.x) storing local drafts and an append-only mutation queue.
  - Automatic background synchronization with UUIDv4 idempotency keys, re-authentication checks, and server-side RBAC/IDOR verification.
  - 3-way conflict detection based on `updated_at` timestamps, returning explicit `CONFLICT` states without silent overwrites.
  - Offline security: Zero sensitive PII, passwords, or government documents cached offline; complete IndexedDB purge on logout.

---

## 8. Admin Moderation, Governance & Provenance Auditing (Phase 8)

The platform implements an institutional-grade governance, moderation, and cryptographic provenance auditing layer:
- **Cryptographic Provenance Chain (`ProvenanceEvent`)**:
  - Implements an append-only, tamper-evident hash chain grounded in canonical deterministic JSON serialization (sorted keys, compact whitespace) and SHA-256 digests (`event_hash = sha256(canonical_json(payload) + prev_event_hash)`).
  - Explicit genesis event handling (`prev_event_hash=None`).
  - Active tamper detection algorithm verifying mathematical continuity across the chain, surfacing payload tampering and sequence breaks.
  - Granular entity timeline reconstruction tracking field-level provenance across products, crafts, users, verifications, and pricing runs.
- **Nine Distinct Information & Governance States**:
  - Segregates `ARTISAN_PROVIDED`, `SOURCE_BACKED`, `AI_SUGGESTED`, `CALCULATED`, `HUMAN_CONFIRMED`, `ADMIN_APPROVED`, `ADMIN_REJECTED`, `FLAGGED`, `SUPERSEDED`, and independently `AUTHORITY_VERIFIED`.
  - **Strict `AUTHORITY_VERIFIED` Guardrail**: Never granted automatically by admin approval, GI craft tags, or document uploads. Strictly requires explicit authoritative registry references (`authority_source`, `authoritative_registry_reference`, `evidence_url`, `verified_at`). Fixed legacy GI auto-promotion bug.
- **Critical Field Moderation Allowlist**:
  - Updates to critical fields (`title`, `price_inr`, `materials`, `craft_id`, `category_id`, `storytelling_description`, `technique`, `provenance_status`) automatically trigger re-moderation (`PENDING_APPROVAL`).
  - Non-critical operational changes (`stock_quantity`, `lead_time_days`, `dimensions`, `weight_grams`, `tags`) maintain `PUBLISHED` status, preventing administrative bottlenecks.
- **Automated Governance Review Signals**:
  - Rule-based detection generates neutral review signals: `PRICE_ANOMALY_REVIEW`, `MISSING_PROVENANCE`, `UNSUPPORTED_CLAIM`, `EXPIRED_EVIDENCE`, `DUPLICATE_SOURCE`, `STALE_MARKET_DATA`, `SAMPLE_EXPOSURE`.
  - Accusatory fraud/forgery labels are strictly prohibited; review signals remain objective triggers for administrative inspection.
  - Active signal deduplication preventing queue inflation for existing unresolved entity flags.
- **Unified Admin Governance Consoles**:
  - `/admin/governance`: Governance command center with factual metrics (pending flags, open reviews, resolved items - zero fabricated trust percentages) and real-time review signals feed.
  - `/admin/moderation`: Unified moderation queue with category/craft filtering, tabbed queues, and idempotent review decisions.
  - `/admin/provenance`: Cryptographic provenance timeline inspector with SHA-256 chain integrity verification.
  - `/admin/verification`: Credential review console enforcing authoritative registry validation for government/GI claims.
- **Security & Public PII Sanitization**:
  - Strict RBAC protecting all governance endpoints (`Role.ADMIN`); rejection of artisans and buyers with HTTP 403 Forbidden.
  - Server-side party-to-transaction IDOR verification and review action idempotency keys preventing replay collisions.
  - Public PII sanitization in provenance feeds (redacting phone numbers, emails, and full tax identifiers).

---

## 9. Production Deployment, Security Hardening & SIH Judge Evaluation Pack (Phase 9)

The platform is fully prepared, containerized, and security-hardened for production deployment and SIH evaluation:
- **Production Containerization**:
  - `backend/Dockerfile`: Multi-stage Python 3.11 container with non-root user (`appuser:10001`), serving via Uvicorn workers.
  - `frontend/Dockerfile`: Multi-stage Node.js 20 container leveraging Next.js `output: "standalone"` for a minimal container footprint.
  - `infrastructure/docker-compose.prod.yml`: Production orchestration for PostgreSQL (with `pgvector`), Redis 7, MinIO, FastAPI backend, and Next.js frontend.
- **Enterprise Security Hardening**:
  - **Defensive Security Headers**: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and production `Strict-Transport-Security`.
  - **Request Correlation & Telemetry**: Generates/propagates `X-Correlation-ID` across all requests and logs.
  - **DOS Protection**: Enforces 15MB request payload limit at middleware level.
  - **Global Error Sanitization**: Masks internal stack traces and SQL errors in production mode (`DEBUG=False`), returning audited correlation IDs.
  - **Production Secret Validation**: Rejects default/weak secrets and insecure CORS wildcards on startup when `APP_ENV="production"`.
- **SIH Judge Evaluation Pack**:
  - Complete 9-document suite in [`docs/`](file:///e:/docs/): master evaluation pack, 15-step interactive demo script, problem-solution mapping, technical architecture blueprint, AI capabilities & honest limitations charter, data provenance specification, security & privacy controls, deployment runbook, and testing report.
- **Verified Quality & Performance**:
  - 128 / 128 tests passing across all 9 phases (100% pass rate).
  - Next.js 14 production build verified (21 routes compiled cleanly).
  - Measured local engine execution: Fair price cost calculation: 0.0400 ms; Demand forecast: 0.0982 ms; Provenance SHA-256 hash: 24.3522 µs.




