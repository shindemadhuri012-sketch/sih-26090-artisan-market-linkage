# SIH 26090: Phase 1 Technical Engineering Notes
## Implementation Observations, Environment Verification & Next Phase Prerequisites

---

## 1. Environment & Toolchain Diagnostics

During the execution of Phase 1 in the host environment (Windows x64):
- **Python**: Installed version is `Python 3.13.7`.
- **Installed Frameworks**: `FastAPI 0.136.3`, `Pydantic 2.12.5`, `pydantic-settings 2.13.1`, `SQLAlchemy 2.0.48`, `alembic 1.20.0`, `pgvector 0.5.0`, `psycopg 3.3.6`, `asyncpg 0.31.0`, `aiosqlite 0.22.1`, `pytest 9.1.1`.
- **Node.js**: `node` executable is not currently registered in the system environment PATH. A complete standard Next.js 14+ / TypeScript project scaffold was created (`package.json`, `tsconfig.json`, `next.config.ts`, `src/app/layout.tsx`, `src/app/page.tsx`).
- **PostgreSQL / pgvector Service**: PostgreSQL service is not active as a background Windows service on localhost. 
  - *Mitigation & Verification*: All 23 SQLAlchemy models and migrations were verified via Alembic offline SQL generation (`alembic upgrade --sql`) and in-memory test execution (`tests/test_models.py`), successfully generating and verifying all 23 tables, foreign keys, and indexes.

---

## 2. Dialect-Aware pgvector Architecture

To ensure high portability between local testing environments and managed cloud PostgreSQL databases:
- The platform uses a custom SQLAlchemy TypeDecorator (`EmbeddingVector(dim=768)`).
- On PostgreSQL, the type automatically activates native `pgvector.sqlalchemy.Vector(768)`.
- On non-PostgreSQL dialects (SQLite for fast local unit testing), the type falls back to JSON text serialization, preventing dialect errors while preserving complete data structure validity.

---

## 3. Real Data Ingestion Validation Outcomes

The reusable ingestion pipeline (`scripts/ingestion/run_ingestion.py`) was executed and verified:
- **GI Registry Ingestion**: 12 authentic registered handicraft GI tags from the official IP India registry ingested, validated (100% pass), and hashed.
- **ODOP Catalogue Ingestion**: 10 official district-to-craft records from DPIIT / Invest India ingested, validated (100% pass), and hashed.
- **Audit Manifests**: Two cryptographically signed receipts generated in `data/manifests/`.
- **Processed Seeds**: Two normalized datasets generated in `data/processed/` ready for automated database seeding in Phase 2.

---

## 4. Test Suite Execution Summary

The initial automated test suite was executed via `pytest`:
- **Total Tests Executed**: 16
- **Total Tests Passed**: 16 (100% pass rate)
- **Total Tests Failed**: 0
- **Suites Verified**:
  - `tests/test_api_health.py` (FastAPI app factory & liveness probe)
  - `tests/test_config.py` (Pydantic v2 settings loading & CORS parser)
  - `tests/test_deduplication.py` (Deterministic duplicate resolution)
  - `tests/test_ingestion_validation.py` (Field checks, geography checks, failure modes)
  - `tests/test_models.py` (Metadata registration & in-memory SQLite schema creation)
  - `tests/test_provenance.py` (Provenance headers & demo data segregation)
