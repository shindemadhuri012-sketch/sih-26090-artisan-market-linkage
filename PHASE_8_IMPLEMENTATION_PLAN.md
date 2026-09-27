# PHASE 8 IMPLEMENTATION PLAN — ADMIN MODERATION, GOVERNANCE & PROVENANCE AUDITING

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: PHASE 8 — Admin Moderation, Governance & Provenance Auditing  
**Scope**: Step-by-Step Execution Sequence (Pending User Approval)  
**Date**: 2026-09-27  

---

## 1. Overview & Execution Pre-Conditions

Execution will strictly commence only after user review and explicit approval of this plan. No production code has been modified during planning.

### Pre-Condition Checklist:
- [x] Phase 7 completed and verified (111 / 111 tests passing, 0 failures, 0 regressions).
- [x] Current Alembic head verified at `20260327_0007_demand_intelligence_and_sync.py`.
- [x] Zero-fabrication and strict data integrity policies enforced.
- [x] Architectural plan authored: `docs/phase_8_governance_moderation_plan.md`.

---

## 2. Step-by-Step Implementation Sequence

### Step 1: Database Models & Alembic Migration
1. **Create Model Module** `backend/app/models/governance.py`:
   - Declare `GovernanceFlag` with indexes on `(entity_type, entity_id)`, `severity`, and `status`.
   - Declare `ModerationAction` with foreign key to `users.id`, tracking status transitions, reasons, and feedback.
   - Declare `ProvenanceEvent` with hash-chaining fields (`event_hash`, `previous_event_hash`, `sequence_number`).
2. **Register Entities in Central Registry** `backend/app/models/__init__.py`:
   - Export `GovernanceFlag`, `ModerationAction`, and `ProvenanceEvent` (bringing model count from 34 to 37).
3. **Generate & Apply Alembic Migration**:
   - File: `backend/alembic/versions/20260327_0008_governance_moderation_and_provenance.py`
   - Revision ID: `20260327_0008`
   - Down Revision: `20260327_0007`
   - Execute dry-run `alembic upgrade head --sql` to verify DDL syntax.

### Step 2: Core Provenance & Governance Services
1. **Provenance Event Service** `backend/app/services/provenance_service.py`:
   - `record_provenance_event()`: Computes field-level JSON diffs, fetches latest chain hash for the entity, calculates SHA-256 event hash, and commits immutable row.
   - `verify_provenance_chain()`: Validates cryptographic hash continuity for an entity from root genesis to latest event.
   - `get_entity_timeline()`: Reconstructs chronological audit evolution of all mutable fields.
2. **Governance Flagging Service** `backend/app/services/governance_service.py`:
   - Automated anomaly detection checks (missing provenance, price outliers, expired evidence).
   - `raise_flag()`: Creates structured, neutral review signals.
   - `resolve_flag()`: Records moderator resolution decision and explanation.
   - `get_governance_dashboard_metrics()`: Aggregates real, factual counts without synthetic scoring.
3. **Unified Moderation Service** `backend/app/services/moderation_service.py`:
   - `list_moderation_queue()`: Queries submissions across products, artisan profiles, and craft passports.
   - `process_moderation_decision()`: Applies state transition, records `ModerationAction`, emits `ProvenanceEvent`, and updates user-facing feedback.
   - Decouples admin approval from government certification, ensuring `ADMIN_REVIEWED` is never conflated with `AUTHORITY_VERIFIED`.

### Step 3: Pydantic v2 Schemas
1. **Governance & Moderation Schemas** `backend/app/schemas/governance.py`:
   - `GovernanceFlagCreate`, `GovernanceFlagResponse`, `GovernanceFlagResolveRequest`.
   - `ModerationActionCreate`, `ModerationActionResponse`, `ModerationQueueItemResponse`.
   - `ProvenanceEventResponse`, `ProvenanceTimelineResponse`, `ProvenanceChainVerifyResponse`.
   - `GovernanceDashboardResponse`.

### Step 4: REST API Endpoints & Routing
1. **Create Endpoints Module** `backend/app/api/v1/endpoints/governance.py`:
   - `GET /api/v1/governance/dashboard` — Factual governance metrics.
   - `GET /api/v1/governance/flags` — Paginated review signals.
   - `POST /api/v1/governance/flags/{flag_id}/resolve` — Flag resolution.
   - `GET /api/v1/governance/provenance/timeline/{entity_type}/{entity_id}` — Field change timeline.
   - `GET /api/v1/governance/provenance/verify-chain/{entity_type}/{entity_id}` — Tamper verification.
2. **Create Endpoints Module** `backend/app/api/v1/endpoints/moderation.py`:
   - `GET /api/v1/moderation/queue` — Multi-entity moderation backlog.
   - `POST /api/v1/moderation/review` — Multi-entity review action.
3. **Mount in API Router** `backend/app/api/v1/router.py`:
   - Register `/governance` and `/moderation` routers under `/api/v1`.

### Step 5: Frontend Governance & Moderation Interfaces
1. **Governance Command Center** `frontend/src/app/admin/governance/page.tsx`:
   - Factual dashboard displaying pending workloads, open flags by severity, and unreviewed AI suggestions.
2. **Unified Moderation Console** `frontend/src/app/admin/moderation/page.tsx`:
   - Tabbed queue for Products, Artisan Profiles, and Craft Passports.
   - Side-by-side inspection of artisan data, AI suggestions, and uploaded verification documents.
   - Review action form (Approve, Request Changes, Reject) with feedback inputs.
3. **Provenance Timeline & Tamper Inspector** `frontend/src/app/admin/provenance/page.tsx`:
   - Entity search by UUID.
   - Interactive before/after field diff timeline.
   - One-click cryptographic hash chain verification.
4. **Verification Review Console** `frontend/src/app/admin/verification/page.tsx`:
   - Document inspection with explicit distinction between `ADMIN_REVIEWED` and `AUTHORITY_VERIFIED`.

### Step 6: Comprehensive Verification Test Suite
Implement targeted test modules:
1. `tests/test_governance_states.py` — State non-equivalence tests (`AI_SUGGESTED != HUMAN_CONFIRMED`, `ADMIN_APPROVED != AUTHORITY_VERIFIED`).
2. `tests/test_moderation_workflows.py` — Multi-entity queue, state transitions, moderator feedback.
3. `tests/test_provenance_audit_chain.py` — Field diffs, SHA-256 hash chaining, simulated tamper detection.
4. `tests/test_governance_flags.py` — Anomaly detection, neutral flag raising, resolution lifecycles.
5. `tests/test_governance_rbac_idor.py` — RBAC enforcement, unauthorized access rejection, public PII stripping.
6. **Full Regression Suite**: Run all 111+ tests across Phases 1–8 to guarantee 100% pass rate.

### Step 7: Documentation & Completion Report
1. Update `docs/database_schema.md` (Add Section 2.9 for Governance, Moderation & Provenance Auditing Layer).
2. Update `README.md` (Mark Phase 8 COMPLETED).
3. Author `PHASE_8_COMPLETION.md`.
4. Stop execution immediately and report to user.
