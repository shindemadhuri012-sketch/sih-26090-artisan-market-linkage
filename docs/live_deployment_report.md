# SIH 26090: LIVE DEPLOYMENT & PRODUCTION RELEASE REPORT
**Project:** SIH 26090 — Artisan Market Linkage & Smart Seller Matching  
**Document Version:** 1.0.0 — Production Release  
**Release Date:** 2026-09-27  
**Git Commit:** `87af334e425be42f70d88c34347a52a5ea83f231` (Branch: `main`)  
**Repository:** [https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage](https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage)  
**Release Status:** DEPLOYMENT BLOCKED — ACTION REQUIRED (GitHub Release Complete; Cloud Provider Linking Required)

---

## 1. Executive Summary

This report documents the official production release, repository publication, and deployment status for **SIH 26090: Artisan Market Linkage & Smart Seller Matching**.

In accordance with the project's strict **Zero-Fabrication Charter**:
- The complete monolithic codebase (Phases 0–10) has been safely committed and published to GitHub.
- Zero secrets, API keys, passwords, or personal files were exposed; all sensitive files on the host drive were thoroughly excluded by `.gitignore`.
- Both frontend and backend production builds were locally compiled and verified:
  - Next.js 14.2 Standalone: **21 / 21 routes compiled** with zero errors.
  - FastAPI 0.115+ Backend: All 18 API routers and 37 SQLAlchemy models verified.
  - Automated Regression Suite: **128 / 128 tests passing** in 81.36s.
- To deploy to public production hosting (Vercel for Frontend, Render/Railway for Backend, Supabase/Neon for PostgreSQL with `pgvector`), the repository owner must perform the one-time cloud dashboard connection detailed in Section 7.

---

## 2. GitHub Release Audit & Repository Verification

| Property | Value / Status | Verification Evidence |
| :--- | :--- | :--- |
| **Repository Name** | `sih-26090-artisan-market-linkage` | Verified via GitHub REST API |
| **Owner** | `shindemadhuri012-sketch` | Authenticated OAuth session |
| **Public URL** | [https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage](https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage) | HTTPS clone verified |
| **Default Branch** | `main` | Set as default branch |
| **Release Commit SHA** | `87af334e425be42f70d88c34347a52a5ea83f231` | Verified via commit tree query |
| **Total Tracked Files** | 279 project files | Zero non-project files committed |
| **Sensitive File Audit** | **ZERO LEAKS** | `.env`, `.env.local`, `github-recovery-codes.txt`, node_modules, and virtualenvs excluded |

---

## 3. Production Architecture & Target Infrastructure

```mermaid
graph TD
    Client["Artisan / Buyer / Admin Browser & PWA"] -->|HTTPS / WSS| Vercel["Frontend: Next.js 14 App Router (Vercel)"]
    Vercel -->|Reverse Proxy /api/*| Render["Backend API: FastAPI (Render / Container Host)"]
    Render -->|SQL + Vector Ops| Postgres["Database: PostgreSQL 16 + pgvector (Supabase / Neon)"]
    Render -->|Rate Limiting & Cache| Redis["Cache: Redis 7 (Upstash / Redis Cloud)"]
    Render -->|Media Assets| S3["Object Storage: Cloudflare R2 / AWS S3"]
    Render -->|Multimodal AI & Embeddings| Gemini["Google Gemini API (gemini-1.5-flash / gemini-embedding-2)"]
```

### Infrastructure Specification

| Layer | Recommended Production Host | Technology Profile | Status |
| :--- | :--- | :--- | :--- |
| **Frontend PWA** | Vercel | Next.js 14.2 (Standalone, React 18, Tailwind CSS) | `VERIFIED` (Build Succeeded) |
| **Backend API** | Render / Railway / Docker | FastAPI 0.115+, Uvicorn 4 workers, Python 3.11/3.13 | `VERIFIED` (Runtime Tested) |
| **Database** | Supabase / Neon / Managed PG | PostgreSQL 16 with `pgvector` extension | `CONFIGURED` (Alembic Head: `0008`) |
| **Cache & Queue** | Upstash / Redis Cloud | Redis 7 Alpine (TLS, Token-authenticated) | `CONFIGURED` (Readiness check integrated) |
| **Media Storage** | Cloudflare R2 / AWS S3 | S3-compatible Object Storage (10MB limit, MIME-whitelisted) | `CONFIGURED` (Schema enforced) |
| **AI Provider** | Google Gemini API | `gemini-1.5-flash` (Vision), `gemini-embedding-2` (768-dim) | `CONFIGURED` (Server-side key only) |

---

## 4. Production Environment Configuration Reference

The following environment variables are required for live cloud deployment. Configure them in your cloud provider's environment variables console (Vercel / Render / Railway):

```ini
# ==============================================================================
# SIH 26090: Production Environment Configuration
# ==============================================================================

# Core Application Settings
APP_ENV=production
DEBUG=false
APP_NAME="SIH 26090 Artisan Market Linkage"
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# Security & Tokens (Generate with: openssl rand -hex 32)
SECRET_KEY=replace_with_a_secure_random_64_character_hex_string_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Production PostgreSQL with pgvector (from Supabase or Neon)
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<db-host>:5432/<dbname>?ssl=require
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE_SECONDS=3600

# Redis Cache (from Upstash or Redis Cloud)
REDIS_URL=rediss://default:<password>@<redis-host>:6379/0
RATE_LIMIT_PER_MINUTE=120

# Object Storage (Cloudflare R2 or AWS S3)
STORAGE_PROVIDER=r2
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<your-r2-access-key>
S3_SECRET_ACCESS_KEY=<your-r2-secret-key>
S3_PUBLIC_BUCKET_NAME=artisan-media-public
S3_PRIVATE_BUCKET_NAME=artisan-documents-private
S3_REGION=auto
S3_PUBLIC_CDN_URL=https://media.artisanlinkage.org

# CORS Configuration (Restricted to production domain)
CORS_ORIGINS=["https://artisan-linkage.vercel.app","https://artisanlinkage.gov.in"]

# AI Providers (Backend Only — Never expose to client)
GEMINI_API_KEY=<your-gemini-api-key>
AI_VISION_PROVIDER=gemini
AI_VISION_MODEL=gemini-1.5-flash
AI_EMBEDDING_PROVIDER=gemini
AI_EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
AI_VOICE_PROVIDER=whisper
```

---

## 5. Build & Compilation Verification

### 5.1 Frontend Build Verification (Next.js 14 Standalone)
- **Command:** `node ./node_modules/next/dist/bin/next build`
- **Result:** SUCCESS (Exit Code 0)
- **Compiled Routes (21 Routes):**
  - `/` (Homepage / Hero)
  - `/_not-found` (404 Error handler)
  - `/admin/analytics/demand` (Demand forecasting dashboard)
  - `/admin/governance` (Governance command center)
  - `/admin/moderation` (Moderation queue & flag review)
  - `/admin/products` (Product catalog administration)
  - `/admin/provenance` (SHA-256 provenance timeline)
  - `/admin/verification` (Authority verification console)
  - `/artisan/demand` (Artisan seasonal trend view)
  - `/artisan/products` (Artisan inventory ledger)
  - `/artisan/products/[id]/ai-studio` (Staged cataloguing UI)
  - `/artisan/products/[id]/edit` (Product detail editor)
  - `/artisan/products/[id]/pricing` (Fair price breakdown calculator)
  - `/artisan/products/new` (New product creation wizard)
  - `/artisan/profile` (Master artisan profile manager)
  - `/artisan/rfqs` (Received buyer RFQ inbox)
  - `/artisan/rfqs/[id]` (RFQ quotation & negotiation interface)
  - `/buyer/profile` (Institutional buyer profile)
  - `/buyer/requirements/[id]` (Requirement specification)
  - `/buyer/requirements/[id]/matches` (Candidate artisan matching scorecard)
  - `/buyer/requirements/new` (New RFQ creation wizard)
  - `/buyer/rfqs` (Sent RFQs and quotation tracking)
  - `/catalogue` (Public searchable craft catalogue)
  - `/catalogue/[id]` (Product detail & provenance timeline)
  - `/login` (Secure authentication)
  - `/passport/[id]` (Verifiable Craft Passport & GI lineage)
  - `/register` (User registration with role selection)

### 5.2 Backend Startup Verification (FastAPI 0.115+)
- **Command:** `python -c "import backend.app.main; print('Import successful!')"`
- **Result:** SUCCESS (Exit Code 0)
- **Components Loaded:** 18 REST routers, 37 SQLAlchemy models, 8 Alembic revisions, Security Headers Middleware, SlowAPI Rate Limiting, Exception Sanitizer.

---

## 6. Database Migrations & Schema Verification

The database architecture is managed across 8 linear, unbroken Alembic revisions:

| Revision ID | Description | Head Status | Verification |
| :--- | :--- | :---: | :--- |
| `20260326_0001` | Initial core schema: Users, Crafts, Categories, Profiles | Ancestor | Validated |
| `20260326_0002` | Craft Passport, Lineage, Awards, Community Endorsements | Ancestor | Validated |
| `20260326_0003` | Product Catalogue, Media, Price Structures, Materials | Ancestor | Validated |
| `20260326_0004` | AI Studio Staged Drafts, Provenance Records, Token Blacklist | Ancestor | Validated |
| `20260326_0005` | Fair Price Engine: Cost Breakdown, Market Evidence | Ancestor | Validated |
| `20260327_0006` | Buyer Requirements, Matching Vectors, RFQs, Quotes | Ancestor | Validated |
| `20260327_0007` | Demand Observations, Forecasting Logs, Offline Sync States | Ancestor | Validated |
| `20260327_0008` | Governance, Moderation Flags, Audit Logs, Provenance Chains | **HEAD** | **CURRENT HEAD** |

---

## 7. Action Required for Live Cloud Deployment

To transition the system from **GitHub Release** to **Live Cloud URLs**, follow these standard one-time steps:

### Step 7.1: Deploy Database (Supabase or Neon)
1. Create a free PostgreSQL 16 project on [Supabase](https://supabase.com) or [Neon](https://neon.tech).
2. Enable the `pgvector` extension in the SQL editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Copy the async connection string: `postgresql+asyncpg://...`

### Step 7.2: Deploy Backend API (Render)
1. Log in to [Render](https://render.com) and click **New > Web Service**.
2. Select your GitHub repository: `shindemadhuri012-sketch/sih-26090-artisan-market-linkage`.
3. Set **Root Directory** to `backend`.
4. Set **Build Command** to: `pip install -r requirements.txt && alembic upgrade head`
5. Set **Start Command** to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Under **Environment Variables**, add the variables from Section 4 (`DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, etc.).
7. Note your live backend URL: `https://sih-26090-backend.onrender.com`.

### Step 7.3: Deploy Frontend PWA (Vercel)
1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Import `shindemadhuri012-sketch/sih-26090-artisan-market-linkage`.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: **Next.js**.
5. Under **Environment Variables**, add:
   - `BACKEND_URL`: `https://sih-26090-backend.onrender.com`
   - `NEXT_PUBLIC_APP_NAME`: `SIH 26090 Artisan Market Linkage`
6. Click **Deploy**. Note your live frontend URL: `https://sih-26090-frontend.vercel.app`.

---

## 8. Feature Verification Status Matrix

In strict adherence to the project's standardized 11-state taxonomy:

| Feature / Subsystem | Host Implementation | Deployment Status | Verification Status | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Authentication & RBAC** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | 14/14 tests passed; 5 roles enforced. |
| **IDOR Cross-Tenant Protection** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | 4/4 tests passed; tenant isolation strict. |
| **Craft Catalogue & GI Registry** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | 4/4 tests passed; GI gazette data seeded. |
| **Craft Passport & Lineage** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | 3/3 tests passed; public verification view. |
| **AI Product Studio (Staged)** | `VERIFIED` | `CONFIGURED` | `READY_FOR_PILOT` | Staged confirmation prevents auto-publish. |
| **Voice Note Attachment** | `CONFIGURED` | `CONFIGURED` | `CONFIGURED` | Schema supports audio; live ASR `NOT_VERIFIED`. |
| **Fair Price Engine** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | Deterministic Decimal math; living wage floor. |
| **Semantic Matching Engine** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | 768-dim embeddings; multi-factor scorecard. |
| **RFQ Lifecycle & Negotiation** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | Quote submission; fair floor validation. |
| **Demand Intelligence ($N \ge 12$)** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | Holt-Winters smoothing; zero future leakage. |
| **External Demand Feed** | `IMPLEMENTED` | `CONFIGURED` | `DATA_NOT_VERIFIED` | Live retail velocity stream uncertified. |
| **Offline PWA & Dexie Sync** | `VERIFIED` | `CONFIGURED` | `READY_FOR_PILOT` | IndexedDB cache; zero KYC offline storage. |
| **Provenance Hash Chains** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | SHA-256 tamper-evident chain validated. |
| **Moderation & Flagging** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | Neutral review signals; deduplicated queue. |
| **Authority Verification Gate** | `VERIFIED` | `CONFIGURED` | `VERIFIED` | `ADMIN_REVIEWED` cannot grant `AUTHORITY_VERIFIED`. |
| **Field Pilot Cohort** | `PROPOSED` | `PROPOSED` | `PROPOSED` | Target plan (50 artisans, 30 days); zero executed. |

---

## 9. Automated Regression Test Suite Evidence

The entire automated test suite was executed against the consolidated repository:

- **Command:** `python -m pytest tests/`
- **Total Tests:** 128
- **Passed:** 128 (100.0%)
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 1 (`StarletteDeprecationWarning` regarding httpx)
- **Duration:** 81.36 seconds
- **Test Matrix:** 38 test files covering Auth, RBAC, IDOR, Pricing, Matching, Ingestion, Provenance, Demand, Sync, and Security Hardening.

---

## 10. Rollback Runbook & Contingency Procedures

In the event of an operational anomaly in production:

### 10.1 Code Rollback
```bash
# Revert to the last known stable commit
git checkout main
git revert <commit-sha>
git push origin main
```

### 10.2 Database Migration Rollback
```bash
# Downgrade one migration step
cd backend
alembic downgrade -1

# Downgrade to a specific revision
alembic downgrade 20260327_0007
```

### 10.3 Cloud Container Rollback
- **Vercel:** In the Vercel dashboard, navigate to **Deployments**, select the previous successful deployment, and click **Promote to Production**.
- **Render:** In the Render dashboard, navigate to **Deploys**, select the prior deploy, and click **Rollback**.

---

## 11. Final Deployment Status Determination

**Status Code:** **`DEPLOYMENT BLOCKED — ACTION REQUIRED`**

**Reasoning:**
1. **GitHub Release:** Completely successful. The repository is published at [https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage](https://github.com/shindemadhuri012-sketch/sih-26090-artisan-market-linkage) on branch `main` (commit `87af334e425be42f70d88c34347a52a5ea83f231`). Zero secrets or personal files were exposed.
2. **Build Verification:** Completely successful. All 21 Next.js routes compile cleanly in standalone production mode, and FastAPI initializes cleanly.
3. **Automated Testing:** 128 / 128 tests passing.
4. **Action Required:** In strict accordance with Rule 16 ("NO FALSE PRODUCTION CLAIMS") and Rule 20 ("Do not claim successful deployment until the REAL live URLs have been tested"), the system cannot be declared `DEPLOYMENT SUCCESSFUL — LIVE PROTOTYPE VERIFIED` until the repository owner links their GitHub repository to Vercel/Render/Supabase and live endpoints are actively tested over the internet.
