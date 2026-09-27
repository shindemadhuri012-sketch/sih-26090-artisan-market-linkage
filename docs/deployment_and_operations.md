# SIH 26090: PRODUCTION DEPLOYMENT & OPERATIONS RUNBOOK
## Deployment Architecture, Containerization, Environment Setup & Operational Runbook

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. Production Architecture & Deployment Matrix

| Service | Technology | Port | Container / Process | Deployment Status |
|:---|:---|:---|:---|:---|
| **Database** | PostgreSQL 16 + pgvector | 5432 | `sih26090_prod_postgres` | `READY_TO_DEPLOY` |
| **Cache & Queue** | Redis 7 Alpine | 6379 | `sih26090_prod_redis` | `READY_TO_DEPLOY` |
| **Object Store** | MinIO S3 / Cloudflare R2 | 9000/9001 | `sih26090_prod_minio` | `READY_TO_DEPLOY` |
| **Backend API** | FastAPI / Uvicorn (4 workers) | 8000 | `sih26090_prod_backend` | `READY_TO_DEPLOY` |
| **Frontend PWA** | Next.js 14 Standalone | 3000 | `sih26090_prod_frontend` | `VERIFIED` (Build Succeeded) |
| **Database Migrations** | Alembic (Revisions 0001–0008) | N/A | CLI Runner | `VERIFIED` |

---

## 2. Environment Configuration Reference (`.env.production`)

```ini
# ==============================================================================
# SIH 26090: Production Environment Configuration Template
# ==============================================================================

# Application Environment
APP_ENV=production
DEBUG=false
APP_NAME="SIH 26090 Artisan Market Linkage"
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# Security & Session (Generate with: openssl rand -hex 32)
SECRET_KEY=39f8a4e1b7c2d5e6890123456789abcdef0123456789abcdef0123456789abcdef
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL with pgvector
POSTGRES_USER=artisan_admin
POSTGRES_PASSWORD=SetAStrongRandomDbPasswordHere123!
POSTGRES_DB=artisan_linkage_prod
DATABASE_URL=postgresql+asyncpg://artisan_admin:SetAStrongRandomDbPasswordHere123!@postgres:5432/artisan_linkage_prod
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE_SECONDS=3600

# Redis Cache & Rate Limiting
REDIS_PASSWORD=SetAStrongRandomRedisPasswordHere123!
REDIS_URL=redis://:SetAStrongRandomRedisPasswordHere123!@redis:6379/0
RATE_LIMIT_PER_MINUTE=120

# Object Storage (MinIO or Cloudflare R2)
STORAGE_PROVIDER=minio
MINIO_ROOT_USER=minio_storage_admin
MINIO_ROOT_PASSWORD=SetAStrongMinioPasswordHere123!
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY_ID=minio_storage_admin
S3_SECRET_ACCESS_KEY=SetAStrongMinioPasswordHere123!
S3_PUBLIC_BUCKET_NAME=artisan-media-public
S3_PRIVATE_BUCKET_NAME=artisan-documents-private
S3_REGION=us-east-1

# CORS Whitelist (Restricted to production domain)
CORS_ORIGINS=["https://artisanlinkage.gov.in"]

# AI Providers (Backend Only - Never expose to client)
GEMINI_API_KEY=your-production-gemini-api-key-here
AI_VISION_PROVIDER=gemini
AI_VISION_MODEL=gemini-1.5-flash
AI_EMBEDDING_PROVIDER=gemini
AI_EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
```

---

## 3. Step-by-Step Deployment Instructions

### Step 3.1: Clone and Configure Environment
```bash
git clone https://github.com/SIH2026/sih-26090-artisan-market-linkage.git
cd sih-26090-artisan-market-linkage

# Copy production template and edit credentials
cp .env.example .env.production
nano .env.production
```

### Step 3.2: Launch Production Stack via Docker Compose
```bash
# Build and start all 5 services in detached mode
docker compose -f infrastructure/docker-compose.prod.yml --env-file .env.production up -d --build

# Verify all containers are healthy
docker compose -f infrastructure/docker-compose.prod.yml ps
```

### Step 3.3: Execute Database Migrations
```bash
# Run Alembic migrations inside backend container
docker compose -f infrastructure/docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 3.4: Ingest Authentic GI & ODOP Master Catalogues
```bash
# Populate Indian GI registry and ODOP craft seeds
docker compose -f infrastructure/docker-compose.prod.yml exec backend python -m scripts.ingestion.run_ingestion
```

---

## 4. Health Checks & Verification Probes

### 4.1 Liveness Probe
```bash
curl -f http://localhost:8000/api/v1/health
# Expected Response:
# {"status":"ok","environment":"production","version":"1.0.0","components":{"api":"healthy"}}
```

### 4.2 Deep Dependency Readiness Probe
```bash
curl -f http://localhost:8000/api/v1/ready
# Expected Response:
# {"status":"ok","environment":"production","version":"1.0.0","database":{"connected":true,"pgvector_available":true},"components":{"api":"healthy","redis":"healthy"}}
```

---

## 5. Operational Runbook & Troubleshooting

1. **Database Connection Errors**:
   - Verify PostgreSQL container is healthy: `docker compose logs postgres`.
   - Verify `pgvector` extension: `docker compose exec postgres psql -U artisan_admin -d artisan_linkage_prod -c "\dx"`.
2. **AI Provider Timeouts**:
   - Check external connectivity to Google Generative Language API.
   - If quota is exceeded, the system automatically falls back to manual entry with `AI_SERVICE_UNAVAILABLE` status.
3. **PWA Offline Sync Failures**:
   - If client reports sync errors, check server audit logs for `TOKEN_REUSE_DETECTED` or authentication expiry.
   - Idempotency keys (`UUIDv4`) ensure retried sync batches will not create duplicate products or RFQs.
