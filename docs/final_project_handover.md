# MASTER PROJECT HANDOVER & OPERATIONAL RUNBOOK
**SIH 26090 — Artisan Market Linkage & Smart Seller Matching**
**Document Version:** 1.0.0 — Final Project Handover
**Execution Date:** 2026-09-27
**Milestone:** Phase 10 Complete — Final Project Delivery

---

## 1. System Overview & Technology Stack

The platform is an enterprise-grade, offline-first digital marketplace and seller matching engine engineered to link traditional Indian artisans directly with institutional buyers, enforce fair-wage economic floors, and preserve cultural heritage with cryptographic provenance.

### Core Technology Stack
- **Backend Service:** FastAPI 0.115+ (Python 3.13), Pydantic v2 Settings & Models.
- **Relational & Vector Store:** PostgreSQL 16 with `pgvector` extension, SQLAlchemy 2.0 ORM.
- **Database Migrations:** Alembic (8 linear revisions, zero schema drift).
- **Frontend Client:** Next.js 14 (App Router, React 18, Tailwind CSS, Lucide icons).
- **Offline PWA Layer:** HTML5 Service Worker Cache API, Dexie.js (IndexedDB wrapper).
- **AI & Embedding Provider:** Google Gemini API (`gemini-1.5-flash` for vision, `gemini-embedding-2` for 768-dim embeddings) with deterministic local fallback mocks.
- **Containerization & Orchestration:** Docker multi-stage builds, Docker Compose.
- **Quality Assurance:** Pytest 9.1.1 (128 automated unit, integration, and security tests).

---

## 2. Directory Layout & Architecture Map

```
/
├── alembic/                # Database migration scripts (8 revisions)
├── data/                   # Ground-truth GI registries, craft benchmarks, taxonomies
├── docs/                   # Complete architectural, audit, and pilot documentation
├── frontend/               # Next.js 14 App Router web client and PWA
│   ├── public/             # PWA manifest, service worker, icons
│   └── src/                # React components, offline Dexie.js database, pages
├── src/                    # FastAPI backend application
│   ├── ai/                 # Gemini multimodal & embedding provider adapters
│   ├── analytics/          # Real demand observation & forecasting engine
│   ├── api/v1/             # REST API routers (auth, crafts, products, pricing, matching, etc.)
│   ├── core/               # Configuration, security, middleware, database session
│   ├── models/             # 37 SQLAlchemy declarative database entities
│   ├── pricing/            # Deterministic Fair Price Engine & explainability tree
│   └── services/           # Business logic, provenance chains, moderation
├── tests/                  # 38 pytest test suites (128 passing tests)
├── docker-compose.yml      # Multi-container production deployment manifest
├── Dockerfile.backend      # Multi-stage Python backend container image
├── Dockerfile.frontend     # Multi-stage Next.js standalone container image
└── README.md               # Primary project entrypoint and navigation index
```

---

## 3. Environment Configuration & Secret Management

Create a `.env` file in the project root based on the following template:

```ini
# ==========================================
# SERVER ENVIRONMENT & NETWORK
# ==========================================
PROJECT_NAME="Artisan Market Linkage & Smart Seller Matching"
ENVIRONMENT="production"
DEBUG=false
API_V1_PREFIX="/api/v1"
HOST="0.0.0.0"
PORT=8000

# ==========================================
# SECURITY & AUTHENTICATION
# ==========================================
# Mandatory: Generate with: openssl rand -hex 32
SECRET_KEY="replace_with_a_cryptographically_secure_random_string_in_production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="secure_postgres_password_here"
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_DB="artisan_db"
DATABASE_URL="postgresql+asyncpg://postgres:secure_postgres_password_here@localhost:5432/artisan_db"
DATABASE_URL_SYNC="postgresql+psycopg2://postgres:secure_postgres_password_here@localhost:5432/artisan_db"

# ==========================================
# ARTIFICIAL INTELLIGENCE & PROVIDERS
# ==========================================
# Gemini API Key for Multimodal Vision & Embeddings
GEMINI_API_KEY="AIzaSyYourValidGeminiApiKeyHere"
AI_STUDIO_VISION_MODEL="gemini-1.5-flash"
AI_EMBEDDING_MODEL="gemini-embedding-2"
AI_EMBEDDING_DIMENSIONS=768
AI_VOICE_PROVIDER="whisper"

# ==========================================
# RATE LIMITING & SECURITY HEADERS
# ==========================================
RATE_LIMIT_DEFAULT="60/minute"
RATE_LIMIT_AI="10/minute"
RATE_LIMIT_AUTH="5/minute"
ALLOWED_ORIGINS="http://localhost:3000,https://artisan-link.org"
```

---

## 4. Database Setup & Initialization Runbook

### Step 1: Initialize Database Schema via Alembic
Ensure PostgreSQL 16 is running with the `pgvector` extension enabled, then run:

```powershell
# Execute all 8 linear migrations to reach head
alembic upgrade head

# Verify migration status
alembic current
# Expected output: 20260327_0008 (head)
```

### Step 2: Seed Authoritative Base Data
Seed official craft taxonomies, GI gazette records, and material price benchmarks:

```powershell
# Seed GI registry and craft categories
python scripts/seed_taxonomies.py

# Seed empirical material price benchmarks
python scripts/seed_market_evidence.py

# (Optional for SIH Judge Demonstrations)
python scripts/seed_demo_data.py
```

---

## 5. Local Development & Operational Runbooks

### Runbook A: Starting the Backend API Server
```powershell
# 1. Activate Python virtual environment
.venv\Scripts\Activate.ps1

# 2. Start Uvicorn ASGI server with hot reloading
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Check health and liveness
curl http://127.0.0.1:8000/api/v1/health
# Expected JSON: {"status": "healthy", "database": "connected", "version": "1.0.0"}
```

### Runbook B: Starting the Frontend Web & PWA Client
```powershell
# 1. Enter frontend directory
cd frontend

# 2. Install dependencies (if not cached)
npm install

# 3. Start development server
npm run dev

# 4. Access client at: http://localhost:3000
```

### Runbook C: Production Container Deployment
```powershell
# Build and launch all services with Docker Compose
docker-compose up --build -d

# Check running containers
docker-compose ps

# Tail backend production logs
docker-compose logs -f backend
```

---

## 6. Maintenance & Disaster Recovery Runbooks

### Runbook D: Database Backup and Restore
```powershell
# Automated backup
pg_dump -U postgres -h localhost -d artisan_db -F c -b -v -f "backups/artisan_db_$(Get-Date -Format 'yyyyMMdd_HHmmss').dump"

# Database restore
pg_restore -U postgres -h localhost -d artisan_db -v -c "backups/target_backup.dump"
```

### Runbook E: AI Provider Failover Protocol
1. **Primary Provider:** `Google Gemini API` (`gemini-1.5-flash`, `gemini-embedding-2`).
2. **Quota Exceeded / Network Outage:** The backend provider adapter in `src/ai/gemini_provider.py` automatically catches HTTP 429 and 503 errors.
3. **Graceful Fallback:** When Gemini is unreachable, the system gracefully reverts to local deterministic vector calculations and returns `SERVICE_DEGRADED` status without crashing API endpoints.

### Runbook F: Offline Sync Conflict Resolution
1. Client mutations queued in IndexedDB are replayed with `client_updated_at` timestamps and document version vectors.
2. In the event of conflicting concurrent edits, the backend detects version divergence in `src/api/v1/sync.py`.
3. The latest authoritative artisan edit takes precedence, while the divergent snapshot is archived to the `audit_logs` table for manual review.

---

## 7. Sign-Off & Project Handover Certification

The **SIH 26090** software platform has achieved complete feature completion, 100% test pass status (128/128 tests), and is fully prepared for demonstration and production deployment. All source code, migrations, test suites, and documentation are preserved in the repository.
