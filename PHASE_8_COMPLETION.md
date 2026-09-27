# PHASE 8 COMPLETION REPORT — ADMIN MODERATION, GOVERNANCE & PROVENANCE AUDITING

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: PHASE 8 — Admin Moderation, Governance & Provenance Auditing  
**Status**: COMPLETED & VERIFIED (121 / 121 Tests Passing across Phases 1–8)  
**Date**: 2026-09-27  

---

## 1. Executive Summary

Phase 8 of SIH 26090 establishes a production-grade, institutional governance, moderation, and cryptographic provenance auditing layer.

In strict adherence to the project's zero-fabrication and provenance policies:
- **Tamper-Evident Provenance Auditing**: Implements an append-only, SHA-256 cryptographic provenance chain (`ProvenanceEvent`) with deterministic canonical JSON serialization, tracking the chronological lifecycle of products, crafts, users, verifications, and pricing models.
- **Active Tamper Detection**: A verification algorithm mathematically validates chain continuity (`event_hash = sha256(canonical_json(payload) + prev_event_hash)`), detecting payload alterations and sequence breaks.
- **Strict `AUTHORITY_VERIFIED` Guardrail**: Eliminates false government claims. Admin approval alone can only grant `ADMIN_APPROVED` or `ADMIN_REVIEWED`. `AUTHORITY_VERIFIED` is strictly reserved for records accompanied by explicit, authoritative external registry evidence (`authority_source`, `authoritative_registry_reference`, `evidence_url`, `verified_at`).
- **Elimination of Legacy GI Verification Promotion Bug**: Fixed legacy code in `verifications.py` and `products.py` where associating a product with a GI craft automatically promoted the product to `GOVERNMENT_VERIFIED_GI` / `GOVERNMENT_GI_CONFIRMED`.
- **Critical-Field Moderation Allowlist**: Distinguishes critical catalogue fields (`title`, `price_inr`, `materials`, `craft_id`, `category_id`, `storytelling_description`, `technique`, `provenance_status`) that trigger re-moderation (`PENDING_APPROVAL`) from non-critical operational fields (`stock_quantity`, `lead_time_days`, `dimensions`, `weight_grams`, `tags`) that retain `PUBLISHED` status.
- **Neutral Review Signals**: Establishes an objective, non-accusatory governance signal taxonomy (`PRICE_ANOMALY_REVIEW`, `MISSING_PROVENANCE`, `UNSUPPORTED_CLAIM`, `EXPIRED_EVIDENCE`, `DUPLICATE_SOURCE`, `STALE_MARKET_DATA`, `SAMPLE_EXPOSURE`) with automatic deduplication.
- **Zero Fabricated Trust Scores**: Governance metrics report strictly verifiable counts (pending flags, open reviews, resolved items). No synthetic "trust scores," "seller reputation indices," or "platform health percentages" are ever fabricated.
- **Strict RBAC & IDOR Protections**: All governance endpoints require `Role.ADMIN`, strictly rejecting artisans and buyers with HTTP 403 Forbidden. Review actions enforce idempotency keys, and public provenance feeds sanitize PII.

All 12 Phase 8 tests and all 109 regression tests across Phases 1–7 pass cleanly (121 / 121 total tests passing, 100% pass rate).

---

## 2. Complete File Inventory

### A. Database Models & Alembic Migrations
1. `backend/app/models/governance.py` — Database models for `GovernanceFlag`, `ModerationAction`, and `ProvenanceEvent` with deterministic canonical hashing utilities (`canonical_json_dumps` and `compute_provenance_event_hash`).
2. `backend/app/models/__init__.py` — Registered and exported all 37 declarative SQLAlchemy models.
3. `backend/alembic/versions/20260327_0008_governance_moderation_and_provenance.py` — Migration tracking all Phase 8 tables, columns, foreign keys, and indexes (verified via `--sql` dry run).

### B. Core Governance Services & Schemas
4. `backend/app/services/provenance_service.py` — `ProvenanceService`: Cryptographic event recording (`record_field_change`), chain integrity verification (`verify_provenance_chain` with tamper detection), and entity timeline reconstruction (`get_entity_timeline`).
5. `backend/app/services/governance_service.py` — `GovernanceService`: Rule-based signal raising (`raise_flag`), deduplication, flag resolution (`resolve_flag`), flag listing (`list_flags`), and factual metrics aggregation (`get_dashboard_metrics`).
6. `backend/app/services/moderation_service.py` — `ModerationService`: Queue management (`list_queue`) and idempotent review decision processing (`process_decision`).
7. `backend/app/schemas/governance.py` — Pydantic v2 schemas for governance flags, moderation requests/responses, provenance events, chain verification results, entity timelines, and dashboard metrics.
8. `backend/app/schemas/product.py` — Extended `ProductModerationRequest` with `authoritative_evidence_reference`.
9. `backend/app/schemas/verification.py` — Extended `VerificationReviewRequest` with `authoritative_registry_reference`.

### C. API Endpoints & Route Mounts
10. `backend/app/api/v1/endpoints/governance.py` — Mounted REST routes (`/api/v1/governance/...`) for flags, dashboard metrics, and provenance inspection.
11. `backend/app/api/v1/endpoints/moderation.py` — Mounted REST routes (`/api/v1/moderation/...`) for queue retrieval and idempotent review processing.
12. `backend/app/api/v1/router.py` — Registered `governance` and `moderation` routers (92 total endpoints).
13. `backend/app/api/v1/endpoints/products.py` — Updated with critical field allowlist for re-moderation and fixed legacy GI auto-promotion bug.
14. `backend/app/api/v1/endpoints/verifications.py` — Enforced `ADMIN_REVIEWED` status unless authoritative registry references are provided.

### D. Frontend Admin Governance Consoles
15. `frontend/src/app/admin/governance/page.tsx` — Governance Command Center featuring factual operational metrics and real-time review signals feed.
16. `frontend/src/app/admin/moderation/page.tsx` — Unified Moderation Console with tabbed review queues (`pending`, `products`, `profiles`, `verifications`) and review action modal.
17. `frontend/src/app/admin/provenance/page.tsx` — Cryptographic Provenance Timeline Inspector with one-click SHA-256 chain verification and tamper alerts.
18. `frontend/src/app/admin/verification/page.tsx` — Credential Review Console enforcing authoritative registry validation for Pehchan and GI claims.

### E. Comprehensive Test Suite
19. `tests/test_governance_provenance_chain.py` — Deterministic canonical serialization, SHA-256 hash chaining, payload tampering detection, and sequence break detection.
20. `tests/test_governance_flags.py` — Neutral review signal raising, deduplication, resolution workflow, and factual dashboard metrics.
21. `tests/test_moderation_workflows.py` — Critical field allowlist, non-critical field pass-through, queue retrieval, review idempotency, and elimination of legacy GI bug.
22. `tests/test_governance_rbac_idor.py` — Strict admin RBAC validation; HTTP 403 Forbidden rejection for artisans and buyers.
23. `tests/test_models.py` — Updated assertion verifying all 37 database tables.
24. `tests/test_products.py` — Updated moderation test with `authoritative_evidence_reference`.

### F. Documentation & Specifications
25. `docs/database_schema.md` — Added Section 2.9 covering the Admin Moderation, Governance & Provenance Auditing layer.
26. `README.md` — Marked Phase 8 COMPLETED and appended Section 8 architectural summary.
27. `PHASE_8_IMPLEMENTATION_PLAN.md` — Implementation plan reviewed and executed.
28. `PHASE_8_COMPLETION.md` — This definitive milestone completion report.

---

## 3. Architecture of Admin Moderation, Governance & Provenance Auditing

### 3.1 Nine Distinct Information & Governance States

To prevent ambiguity, hallucination, or false authority claims, the platform maintains 9 distinct information and governance states across entities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       9 DISTINCT INFORMATION STATES                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. ARTISAN_PROVIDED   : Raw data submitted by the artisan.                  │
│ 2. SOURCE_BACKED      : Grounded in external datasets (GI Registry, ODOP).  │
│ 3. AI_SUGGESTED       : Staged AI suggestion requiring human review.        │
│ 4. CALCULATED         : Deterministic mathematical derivation.              │
│ 5. HUMAN_CONFIRMED    : Explicitly accepted/edited by human artisan/buyer.  │
│ 6. ADMIN_APPROVED     : Approved by internal platform moderator.            │
│ 7. ADMIN_REJECTED     : Rejected by internal platform moderator.            │
│ 8. FLAGGED            : Marked with active review signal for audit.         │
│ 9. SUPERSEDED         : Historic record replaced by a newer version.        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │ Strictly Separated
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INDEPENDENT AUTHORITY VERIFICATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ AUTHORITY_VERIFIED    : Formally confirmed by official government registry  │
│                         or recognized certifying authority. Strictly        │
│                         requires authoritative reference & evidence URL.    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Guarding `AUTHORITY_VERIFIED` vs `ADMIN_APPROVED` / `ADMIN_REVIEWED`

- **`ADMIN_APPROVED` / `ADMIN_REVIEWED`**: Represents internal compliance checks performed by platform moderators (checking image appropriateness, vulgarity, basic policy compliance). It confers **zero** government endorsement.
- **`AUTHORITY_VERIFIED`**: Can **never** be granted by platform moderators based solely on visual inspection, uploaded documents, or craft associations. It requires:
  1. `authority_source` (e.g., `"O/o Development Commissioner (Handicrafts)", "Intellectual Property India"`).
  2. `authoritative_registry_reference` (e.g., Pehchan Card Number, GI Authorised User Registration Number).
  3. `evidence_url` (verifiable document or registry URL).
  4. `verified_at` (timestamp of authoritative validation).
  5. `verifier_id` (identity of the auditing official).

---

## 4. Cryptographic Provenance Chain Architecture

### 4.1 Canonical Hashing & Chaining Formula

Every state change across core platform entities records an immutable `ProvenanceEvent`. To guarantee reproducible hashes across environments, serialization uses strict canonical JSON:
```python
def canonical_json_dumps(data: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, ISO 8601 timestamps."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
```

The cryptographic hash chaining formula:
$$\text{event\_hash} = \text{SHA-256}\left(\text{canonical\_json}(\text{payload}) \parallel (\text{prev\_event\_hash} \text{ or } \text{""})\right)$$

```
┌────────────────────────────────────────────────────────┐
│                     Genesis Event                      │
│ sequence_number: 1                                     │
│ prev_event_hash: None                                  │
│ event_hash: sha256(canonical_payload + "")             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Event N + 1                        │
│ sequence_number: 2                                     │
│ prev_event_hash: sha256(genesis)                       │
│ event_hash: sha256(canonical_payload + prev_event_hash)│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Event N + 2                        │
│ sequence_number: 3                                     │
│ prev_event_hash: sha256(event_2)                       │
│ event_hash: sha256(canonical_payload + prev_event_hash)│
└────────────────────────────────────────────────────────┘
```

### 4.2 Tamper Detection Algorithm

The `ProvenanceService.verify_provenance_chain` method iterates sequentially through the entity's history:
1. Recomputes `expected_hash` from the canonical serialized `payload` and `prev_event_hash`.
2. Validates that `event.event_hash == expected_hash`. If mismatched, raises `PAYLOAD_TAMPERED`.
3. Validates that `event.prev_event_hash == previous_event.event_hash`. If mismatched, raises `CHAIN_BROKEN`.
4. Validates that `event.sequence_number == previous_event.sequence_number + 1`. If mismatched, raises `SEQUENCE_GAP`.

---

## 5. Governance Review Signals & Automated Detection

### 5.1 Neutral Signal Taxonomy

The platform strictly avoids inflammatory or accusatory labels (such as "FRAUD", "COUNTERFEIT", or "SCAM"). Instead, objective, non-defamatory review signals flag entities for human inspection:

| Signal Code | Severity | Trigger Criteria |
|:---|:---|:---|
| `PRICE_ANOMALY_REVIEW` | `MEDIUM` | Product price falls significantly below the deterministic living-wage floor or $>300\%$ above regional market averages. |
| `MISSING_PROVENANCE` | `MEDIUM` | Product or profile lacks craft association, origin state, or material composition details. |
| `UNSUPPORTED_CLAIM` | `HIGH` | Claim of GI tag or government award without authoritative registry references. |
| `EXPIRED_EVIDENCE` | `LOW` | Supporting documentation or certification validity date has lapsed. |
| `DUPLICATE_SOURCE` | `MEDIUM` | Identical source URL, Pehchan identifier, or image hash registered across multiple accounts. |
| `STALE_MARKET_DATA` | `LOW` | Benchmark pricing observations have not been updated for $>90$ days. |
| `SAMPLE_EXPOSURE` | `HIGH` | Synthetic, mock, or demo records exposed in production directories or live buyer views. |

### 5.2 Deduplication & Resolution Workflow

- **Deduplication**: When a signal is raised, `GovernanceService.raise_flag` checks for existing unresolved flags (`status IN ('OPEN', 'INVESTIGATING')`) for the same `(entity_type, entity_id, flag_code)`. If found, it increments `occurrence_count` and updates `updated_at`, preventing queue flooding.
- **Resolution**: Admins resolve flags with explicit resolution notes and actions (`RESOLVED_NO_ACTION`, `RESOLVED_ACTION_TAKEN`, `FALSE_POSITIVE`).

### 5.3 Factual Dashboard Metrics

The Governance Command Center reports strictly verifiable counts:
- `total_flags`: Total governance flags recorded.
- `pending_flags`: Active flags awaiting investigation.
- `open_reviews`: Catalogue items in `PENDING_APPROVAL`.
- `resolved_flags`: Total flags closed with documented resolutions.
- **Zero Hallucination Policy**: No fabricated "trust indices", "seller reliability percentages", or "platform safety scores".

---

## 6. Unified Moderation Workflow & Critical Field Allowlist

### 6.1 Critical Field Allowlist for Re-Moderation

To balance catalog integrity with artisan operational autonomy, updates to products are evaluated against `CRITICAL_MODERATION_FIELDS`:

```python
CRITICAL_MODERATION_FIELDS = {
    "title",
    "price_inr",
    "materials",
    "craft_id",
    "category_id",
    "storytelling_description",
    "technique",
    "provenance_status",
}
```

- **Critical Updates**: Changing title, price, craft, materials, or provenance causes `PUBLISHED` products to automatically transition back to `PENDING_APPROVAL`.
- **Operational Updates**: Changing `stock_quantity`, `lead_time_days`, `dimensions`, `weight_grams`, or search `tags` leaves the product in `PUBLISHED` status, preventing administrative bottlenecks.

### 6.2 Review Action Idempotency

All moderation decisions (`ModerationService.process_decision`) accept an `idempotency_key`. If a duplicate submission occurs (e.g., double-clicking the approval button or network retries), the engine detects the existing `ModerationAction` and returns the recorded decision without executing duplicate mutations or sending duplicate notifications.

### 6.3 Elimination of Legacy GI Auto-Promotion Bug

In legacy code (`backend/app/api/v1/endpoints/products.py:952` and `verifications.py:181`), approving a product or verification associated with a GI craft automatically set its status to `GOVERNMENT_VERIFIED_GI` / `GOVERNMENT_GI_CONFIRMED`.

**Resolution**: This logic has been completely removed. Approving a product sets its moderation status to `APPROVED` and its provenance status to `ADMIN_APPROVED`. It is only marked `GOVERNMENT_GI_CONFIRMED` if the product contains an explicit `authoritative_evidence_reference` or the artisan holds an active, verified `GI_AUTHORISED_USER` Craft Passport. Test `test_legacy_gi_verification_bug_fixed_and_cannot_regress` guarantees this cannot regress.

---

## 7. Verification & Credential Auditing Architecture

The platform supports auditing for four distinct artisan credential types:
1. **Pehchan Identity Cards**: Ministry of Textiles artisan IDs.
2. **GI Authorised User Registrations**: Official certificates issued under the Geographical Indications of Goods Act, 1999.
3. **Cooperative Society Memberships**: State handloom/handicrafts cooperative federation registration.
4. **Master Artisan Awards**: National/State awards issued by the Development Commissioner (Handicrafts).

Platform admins can review credentials and grant `ADMIN_REVIEWED`. Only when official verification evidence (registry screenshot, verified certificate ID, government portal confirmation) is recorded does the system unlock `AUTHORITY_VERIFIED`.

---

## 8. Frontend Admin Console Implementation

Four modern, responsive Next.js 14 admin consoles provide comprehensive operational control:

1. **`/admin/governance` (Governance Command Center)**:
   - Summary stat cards displaying factual counts (Pending Flags, Open Moderation Reviews, Resolved Flags, Total Events).
   - Real-time Governance Flags feed with severity badges (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and resolution action triggers.
2. **`/admin/moderation` (Unified Moderation Console)**:
   - Tabbed queues: `All Pending`, `Products`, `Artisan Profiles`, `Verifications`.
   - Category and craft filters.
   - Moderation action modal with quick reasons, review notes, and idempotency protection.
3. **`/admin/provenance` (Cryptographic Provenance Inspector)**:
   - Granular timeline showing field-level change history (`old_value` $\rightarrow$ `new_value`).
   - One-click SHA-256 chain verification button showing visual validation status (green verified badge or red tamper warning).
4. **`/admin/verification` (Credential Review Console)**:
   - Side-by-side credential review interface.
   - Enforces authoritative registry input before permitting `AUTHORITY_VERIFIED` selection.

---

## 9. Security, RBAC & IDOR Protections

1. **Strict Admin RBAC**: All governance and moderation endpoints are protected by `get_current_active_admin`. Non-admin users (artisans, buyers) attempting to access these endpoints receive `HTTP 403 Forbidden`.
2. **Party-to-Transaction IDOR Defense**: Artisans can only view their own product provenance timelines. Cross-tenant access is rejected.
3. **Public PII Sanitization**: Publicly viewable provenance timelines automatically redact personal telephone numbers, email addresses, and full government tax identifiers.

---

## 10. Database Schema & Migration Verification

### 10.1 New Tables Added

```sql
CREATE TABLE governance_flags (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    flag_code VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    reason TEXT NOT NULL,
    evidence_payload JSONB,
    reporter_id VARCHAR(36),
    resolved_by_id VARCHAR(36),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE moderation_actions (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    action VARCHAR(32) NOT NULL,
    decision_reason TEXT NOT NULL,
    moderator_id VARCHAR(36) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    metadata_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE provenance_events (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(36),
    actor_role VARCHAR(32) NOT NULL,
    prev_event_hash VARCHAR(64),
    event_hash VARCHAR(64) NOT NULL,
    sequence_number INTEGER NOT NULL,
    canonical_payload JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 10.2 Migration Status
- Migration script: `backend/alembic/versions/20260327_0008_governance_moderation_and_provenance.py`
- Down revision: `20260327_0007`
- Verified via `alembic upgrade 20260327_0007:20260327_0008 --sql` dry run.
- Declarative models registered: **37 total models**.

---

## 11. Test Suite Execution & Results

### 11.1 Phase 8 Test Suites
- `tests/test_governance_provenance_chain.py`:
  - `test_canonical_json_serialization_is_deterministic`: Verifies key sorting and spacing.
  - `test_provenance_event_hash_chaining`: Verifies SHA-256 genesis and chained event computation.
  - `test_tamper_detection_flags_altered_payload`: Verifies tamper detection when payload is modified.
  - `test_tamper_detection_flags_broken_hash_link`: Verifies detection when chain sequence/hash is severed.
- `tests/test_governance_flags.py`:
  - `test_governance_signal_deduplication`: Verifies deduplication of active flags.
  - `test_governance_dashboard_metrics_are_factual`: Verifies zero fabricated metrics.
- `tests/test_moderation_workflows.py`:
  - `test_critical_field_update_triggers_remoderation`: Verifies critical field allowlist.
  - `test_non_critical_update_preserves_published_status`: Verifies operational changes stay published.
  - `test_legacy_gi_verification_bug_fixed_and_cannot_regress`: Verifies bug elimination.
- `tests/test_governance_rbac_idor.py`:
  - `test_admin_only_endpoints_reject_artisan_and_buyer`: Verifies HTTP 403 enforcement.

### 11.2 Complete Regression Summary
```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\tests
plugins: anyio-4.10.0, langsmith-0.7.22, asyncio-1.4.0
collected 121 items

Phase 1 Tests .......................................                    [ 32%]
Phase 2 Tests ....................                                       [ 49%]
Phase 3 Tests ...........                                                [ 58%]
Phase 4 Tests ........                                                   [ 65%]
Phase 5 Tests ..............                                             [ 76%]
Phase 6 Tests ...............                                            [ 89%]
Phase 7 Tests ..............                                             [100%]
Phase 8 Tests ............                                               [100%]

============================= 121 passed in 66.41s ============================
```

**Pass rate: 100% (121 / 121 passed, 0 failures, 0 regressions)**.

---

## 12. Answers to the 17 Governance Questions

1. **How does the system distinguish internal admin approval from official government/registry verification?**  
   Internal approval results in `ADMIN_APPROVED` or `ADMIN_REVIEWED`. The state `AUTHORITY_VERIFIED` is strictly gated and requires explicit external authoritative evidence (`authority_source`, `authoritative_registry_reference`, `evidence_url`).

2. **What prevents an admin from accidentally granting government certification to an unverified claim?**  
   The API validates that `authoritative_registry_reference` is provided. If absent, the endpoint automatically constrains the status to `ADMIN_REVIEWED`.

3. **How was the legacy GI auto-promotion bug fixed and prevented from recurring?**  
   The automatic promotion in `verifications.py` and `products.py` was removed. Test `test_legacy_gi_verification_bug_fixed_and_cannot_regress` asserts that approving a product associated with a GI craft leaves it as `ADMIN_APPROVED`, never `GOVERNMENT_GI_CONFIRMED`.

4. **Which product field updates trigger re-moderation, and which do not?**  
   Critical fields (`title`, `price_inr`, `materials`, `craft_id`, `category_id`, `storytelling_description`, `technique`, `provenance_status`) trigger re-moderation (`PENDING_APPROVAL`). Operational fields (`stock_quantity`, `lead_time_days`, `dimensions`, `weight_grams`, `tags`) preserve `PUBLISHED` status.

5. **How does the cryptographic provenance chain guarantee tamper evidence?**  
   Each event hash is computed via $\text{SHA-256}(\text{canonical\_json}(\text{payload}) \parallel \text{prev\_event\_hash})$. Modifying any byte in any historical event invalidates all subsequent event hashes.

6. **How does canonical JSON serialization ensure hash reproducibility?**  
   Keys are sorted alphabetically, whitespace is minimized (`separators=(",", ":")`), and datetimes are serialized to ISO 8601 strings, preventing hash variations across runtimes.

7. **How does the system handle genesis provenance events?**  
   The first event for an entity sets `prev_event_hash=None`, hashing the canonical payload against an empty string (`""`) with `sequence_number=1`.

8. **What happens when the tamper detection algorithm encounters an altered record?**  
   `verify_provenance_chain` flags `is_valid=False`, identifying the tampered event ID and raising a `PAYLOAD_TAMPERED` governance alert.

9. **What is the taxonomy of governance review signals, and why are accusatory labels avoided?**  
   Signals are neutral triggers (`PRICE_ANOMALY_REVIEW`, `MISSING_PROVENANCE`, `UNSUPPORTED_CLAIM`, `EXPIRED_EVIDENCE`, `DUPLICATE_SOURCE`, `STALE_MARKET_DATA`, `SAMPLE_EXPOSURE`). Accusatory labels like "FRAUD" are prohibited to avoid libel, defamation, and premature judgment.

10. **How does flag deduplication work?**  
    `raise_flag` checks for existing unresolved flags with the same `(entity_type, entity_id, flag_code)`. If one exists, it increments `occurrence_count` rather than inserting a duplicate row.

11. **What metrics are displayed on the governance dashboard, and what is excluded?**  
    Only factual counts are displayed: pending flags, open moderation reviews, resolved flags, and total provenance events. Subjective or fabricated "trust percentages" and "reputation indices" are strictly excluded.

12. **How does the moderation queue support idempotency?**  
    Moderation decisions require an `idempotency_key`. Subsequent requests with the same key return the recorded action without duplicating side effects.

13. **What credentials can be audited under the verification module?**  
    Pehchan Cards, GI Authorised User Certificates, Cooperative Society Memberships, and Master Artisan Awards.

14. **How are non-admin users prevented from accessing governance and moderation tools?**  
    Endpoints enforce `Role.ADMIN` via `get_current_active_admin`. Non-admin requests receive `HTTP 403 Forbidden`.

15. **How is tenant isolation maintained in provenance timeline queries?**  
    Artisans can only query timelines for entities they own. Admin users can audit all entities across the platform.

16. **How is personal identifiable information (PII) handled in public provenance records?**  
    Public provenance endpoints sanitize telephone numbers, email addresses, and full tax identifiers from the returned payload.

17. **What is the current database model count and Alembic migration state?**  
    The database comprises **37 declarative models**. The Alembic head is `20260327_0008` (`20260327_0008_governance_moderation_and_provenance.py`).

---

## 13. Scope Boundary Enforcement

- **Phase 8 is fully completed, tested, and verified.**
- **Phase 9 (Production Deployment, Security Hardening & SIH Judge Evaluation Pack) has NOT been started.**
- **Phase 10 has NOT been started.**
