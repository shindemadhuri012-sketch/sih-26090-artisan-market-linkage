# SIH 26090: Repository Structure & Monorepo Organization
## Professional Modular Architecture for Production Deployment

---

## 1. Directory Tree & Subsystem Mapping

```
sih-26090-artisan-market-linkage/
├── backend/                       # Python 3.11+ FastAPI async application layer
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/     # Feature-specific route handlers (health, etc.)
│   │   │       └── router.py      # Central API v1 router aggregator
│   │   ├── core/                  # Application configuration, DB engine, telemetry
│   │   │   ├── config.py          # Pydantic v2 Settings (environment validation)
│   │   │   ├── database.py        # SQLAlchemy 2.0 Async/Sync engine & session factories
│   │   │   └── telemetry.py       # Structured logging & logging configuration
│   │   ├── models/                # Declarative SQLAlchemy 2.0 ORM models (23 entities)
│   │   │   ├── custom_types.py    # Dialect-aware pgvector Vector(768) abstraction
│   │   │   ├── base.py            # Base declarative class, TimestampMixin, ProvenanceMixin
│   │   │   ├── auth.py            # User, Role, AuditLog, Notification
│   │   │   ├── provenance.py      # DataSource, DataImport
│   │   │   ├── craft.py           # CraftCategory, Craft, CraftPassport
│   │   │   ├── artisan.py         # ArtisanProfile, Verification
│   │   │   ├── product.py         # Product, ProductMedia, ProductAttributes, PriceAnalysis
│   │   │   ├── buyer.py           # BuyerProfile, BuyerRequirement, Match, MatchExplanation
│   │   │   ├── market.py          # Enquiry, Order, DemandObservation, DemandForecast
│   │   │   └── __init__.py        # Re-export of all 23 entities
│   │   ├── schemas/               # Pydantic v2 DTOs (Request & Response validation)
│   │   │   └── health.py          # Diagnostic probe response schemas
│   │   ├── services/              # Pure domain business logic services
│   │   └── main.py                # FastAPI application entrypoint & middleware
│   ├── alembic/                   # Database schema versioning & migration scripts
│   │   ├── versions/              # Migration versions (e.g., 20260326_0001_initial_schema.py)
│   │   ├── env.py                 # Alembic environment migration runner
│   │   └── script.py.mako         # Migration generation template
│   ├── alembic.ini                # Alembic CLI configuration
│   ├── requirements.txt           # Backend framework & database dependencies
│   └── README.md
├── frontend/                      # Next.js 14+ App Router, React 19, TypeScript PWA
│   ├── src/
│   │   └── app/
│   │       ├── layout.tsx         # Root HTML layout with responsive meta tags
│   │       └── page.tsx           # Health and architectural placeholder page
│   ├── next.config.ts             # Image optimization & security headers configuration
│   ├── tsconfig.json              # Strict TypeScript compiler options
│   ├── package.json               # Frontend dependencies & scripts
│   └── README.md
├── ai/                            # Decoupled AI inference pipelines & adapters
│   ├── common/                    # Shared AI client adapters & retry logic
│   ├── embeddings/                # 768-dim vector embedding generators
│   ├── matching/                  # Multi-stage explainable matching pipeline
│   ├── vision/                    # Product photograph feature extraction
│   ├── voice/                     # Indic voice transcription (ASR) & audio handling
│   ├── pricing/                   # Fair-price cost-plus-margin calculation
│   ├── forecasting/               # Real-data demand intelligence & cold-start detector
│   └── README.md
├── data/                          # Data layer maintaining raw immutability & provenance
│   ├── raw/                       # Immutable raw source files (GI registry, ODOP)
│   ├── processed/                 # Validated, deduplicated JSON seed datasets
│   ├── manifests/                 # Ingestion execution receipts with SHA-256 checksums
│   └── README.md
├── scripts/                       # Engineering utilities & data pipelines
│   └── ingestion/                 # Reusable data source ingestion architecture
│       ├── common/                # Base adapter, validator, deduplicator, manifest manager
│       ├── gi/                    # Indian GI Registry ingestion adapter
│       ├── odop/                  # Government ODOP catalogue ingestion adapter
│       └── run_ingestion.py       # Master CLI pipeline runner
├── tests/                         # Deterministic automated test suite
│   ├── test_api_health.py         # FastAPI startup & liveness probes
│   ├── test_config.py             # Environment configuration & CORS parsing
│   ├── test_models.py             # Schema metadata, foreign keys & SQLite execution
│   ├── test_provenance.py         # Provenance headers & demo data segregation
│   ├── test_ingestion_validation.py # Data validation & anomaly detection
│   └── test_deduplication.py      # Natural key duplicate filtering
├── infrastructure/                # Container configurations for local services
│   └── docker-compose.yml         # Postgres+pgvector, Redis, MinIO orchestration
├── docs/                          # Architectural specifications & technical blueprints
├── .env.example                   # Safe environment variables template
├── .gitignore                     # Git tracking exclusions
├── README.md                      # Project introduction & setup instructions
├── PHASE_0_COMPLETION.md          # Phase 0 architectural blueprint sign-off
└── PHASE_1_COMPLETION.md          # Phase 1 foundation & data ingestion sign-off
```

---

## 2. Boundary Principles

1. **Strict Decoupling**: The backend exposes purely async REST APIs and does not serve frontend HTML templates. The frontend is a standalone Next.js application deployable to Vercel.
2. **AI Layer Isolation**: Model inference code in `ai/` is decoupled from backend web controllers. If an AI service fails, backend business logic gracefully degrades to standard category fallbacks.
3. **Raw Data Immutability**: No script or developer may alter files in `data/raw/`. Processed seeds in `data/processed/` are reproducibly derived from raw inputs.
