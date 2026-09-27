# SIH 26090: Cloud Deployment & Operational Strategy
## Production Topology, CI/CD Pipeline, Observability & Low-Bandwidth Infrastructure

---

## 1. Production Deployment Topology

The platform separates compute, storage, edge networking, and database layers to guarantee high availability, independent cost scaling, and reliable global delivery:

```mermaid
flowchart TB
    subgraph EdgeFrontend ["Edge Layer (Vercel)"]
        VercelCDN["Vercel Global Edge Network"]
        NextFrontend["Next.js 14+ PWA Engine\n(Edge Functions + Serverless SSR)"]
    end

    subgraph BackendCluster ["Backend Compute (Railway / Container Engine)"]
        FastAPIContainer["FastAPI Docker Container\n(Uvicorn Multi-Worker / Python 3.11)"]
        AlembicRunner["Alembic Migration Job"]
    end

    subgraph DataServices ["Managed Data Infrastructure"]
        PostgresDB[("Managed PostgreSQL 16+ with pgvector\n(Neon / Supabase / AWS RDS)")]
        RedisCache[("Upstash / Managed Redis\n(Rate Limiting & Session Store)")]
        CloudflareR2[("Cloudflare R2 Object Storage\n(Zero Egress Fees for Images/Audio)")]
    end

    subgraph ExternalAI ["Inference Providers"]
        GeminiFlash["Google Gemini 1.5/2.0 Flash API\n(Multimodal Vision & Storytelling)"]
        WhisperASR["Indic Whisper / Bhashini API\n(Indic Voice Transcription)"]
    end

    VercelCDN --> NextFrontend
    NextFrontend -->|REST API Calls over TLS| FastAPIContainer
    NextFrontend -->|Direct Asset Download| CloudflareR2
    
    AlembicRunner --> PostgresDB
    FastAPIContainer --> PostgresDB
    FastAPIContainer --> RedisCache
    FastAPIContainer --> CloudflareR2
    
    FastAPIContainer --> GeminiFlash
    FastAPIContainer --> WhisperASR
```

### 1.1 Service Separation Rationale
- **Frontend on Vercel**: Delivers ultra-fast global edge distribution for static bundles, instant asset caching, and automatic PWA service worker delivery without putting compute load on the backend.
- **Backend on Containerized Linux**: Keeps heavy Python dependencies (`sqlalchemy`, `pgvector`, `pydantic`, `fastapi`, `pillow`, `scipy`) isolated in a reproducible Docker image deployable to Railway, Render, or AWS ECS.
- **Object Storage on Cloudflare R2**: Provides S3-compatible object storage with **zero egress bandwidth fees**, critical for serving high-resolution handicraft images and audio recordings cost-effectively.

---

## 2. CI/CD Automation Pipeline (GitHub Actions)

The deployment pipeline is fully automated using GitHub Actions workflows in `.github/workflows/`:

```mermaid
flowchart LR
    Push[Git Push / PR] --> LintTest["1. Lint & Test\n- Frontend: eslint + vitest\n- Backend: ruff + pytest\n- Schema: Alembic dry-run"]
    LintTest --> BuildDocker["2. Container Build\n- Multi-stage Docker build\n- Security scan (Trivy)"]
    BuildDocker --> Staging["3. Staging Deploy\n- Preview URL (Vercel)\n- Staging API deploy"]
    Staging --> E2ETest["4. Integration E2E\n- Playwright critical paths"]
    E2ETest --> ProdDeploy["5. Production Release\n- Vercel Prod + Railway Live"]
```

### Workflow Specifications
1. **`frontend-ci.yml`**:
   - Executes `npm run lint` and `npm run type-check`.
   - Runs Vitest unit tests for offline IndexedDB sync and component state.
   - Deploys preview environments to Vercel on Pull Requests.
2. **`backend-ci.yml`**:
   - Executes `ruff check .` and `mypy app/`.
   - Runs `pytest` against an ephemeral test PostgreSQL instance with `pgvector`.
   - Validates that database migrations apply cleanly (`alembic upgrade head`).
3. **`production-cd.yml`**:
   - Triggers on tag release or merge into `main`.
   - Builds and tags the backend Docker container.
   - Executes automated database migrations before traffic routing.
   - Promotes the Vercel frontend deployment to production.

---

## 3. Environment Variable Specification

A comprehensive template is maintained in `.env.example`:

```bash
# ==============================================================================
# SIH 26090: Environment Configuration
# ==============================================================================

# Core Application Settings
ENVIRONMENT=production                    # local, staging, production
DEBUG=false
PROJECT_NAME="SIH 26090 Artisan Market Linkage"
API_V1_STR=/api/v1
SECRET_KEY=generate-a-strong-random-64-character-hex-string-for-jwt

# Database (PostgreSQL + pgvector)
DATABASE_URL=postgresql+asyncpg://postgres:securepassword@db.example.com:5432/artisan_linkage
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (Caching & Rate Limiting)
REDIS_URL=rediss://default:token@redis.example.com:6379

# Object Storage (Cloudflare R2 / AWS S3)
STORAGE_PROVIDER=r2                       # r2, s3, minio
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
S3_PUBLIC_BUCKET_NAME=artisan-media-public
S3_PRIVATE_BUCKET_NAME=artisan-documents-private
S3_PUBLIC_CDN_URL=https://media.artisanlinkage.in

# AI Inference APIs
GEMINI_API_KEY=your-gemini-api-key
BHASHINI_API_KEY=your-bhashini-api-key    # For Indic Voice transcription
TEXT_EMBEDDING_PROVIDER=gemini            # gemini, huggingface, local

# SMS & Communication Gateway
SMS_GATEWAY_PROVIDER=mock                 # mock, twilio, gupshup
SMS_API_KEY=your-sms-api-key

# Client Origins for CORS
ALLOWED_ORIGINS=["https://artisanlinkage.in","https://admin.artisanlinkage.in"]
```

---

## 4. Observability, Health Checks & System Monitoring

### 4.1 Health & Readiness Probes
The backend exposes standardized endpoints for cloud load balancers and orchestrators:
- **`GET /api/v1/health`**: Quick liveness probe returning HTTP 200 if the FastAPI event loop is responsive.
- **`GET /api/v1/ready`**: Deep readiness probe verifying:
  1. PostgreSQL database connectivity and `pgvector` extension state.
  2. Redis cache reachability and latency.
  3. Object storage read/write accessibility.
  4. AI provider API health status.

### 4.2 Structured Telemetry & Tracing
- **Structured JSON Logging**: Every log line outputs correlation IDs (`request_id`, `trace_id`, `user_id`, `client_ip`) for centralized ingestion by Datadog, Grafana Loki, or CloudWatch.
- **Metrics Tracked**:
  - `http_request_duration_seconds`: API endpoint latency histograms.
  - `ai_inference_duration_seconds`: Latency tracking for Vision and Voice pipelines.
  - `matching_pipeline_duration_seconds`: Multi-stage matching execution time.
  - `active_db_connections`: Connection pool saturation metrics.
  - `offline_sync_sync_count`: Volume of client drafts synced from IndexedDB.
- **Error Tracking**: Integrated with Sentry for real-time frontend and backend unhandled exception tracking with source-map resolution.

---

## 5. Low-Bandwidth Infrastructure Optimizations

To deliver smooth performance in rural handloom clusters:
1. **Next.js Asset Optimization**: Next.js automatically converts uploaded product images to modern WebP and AVIF formats, serving responsive `srcset` resolutions tailored to low-resolution mobile screens.
2. **Workbox Stale-While-Revalidate**: Static UI assets and common craft categories are served directly from the local browser cache without waiting for round-trip edge network validation.
3. **Data Compression**: Gzip/Brotli compression enabled on all JSON API responses, minimizing cellular payload sizes by up to 75%.
