# SIH 26090: TESTING, VALIDATION & BENCHMARK REPORT
## Comprehensive Quality Assurance, Test Coverage & Performance Report

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. Test Suite Summary & Pass Rate

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
collected 128 items

tests\test_ai_studio_auth.py ..                                          [  1%]
tests\test_ai_studio_media_validation.py .                               [  2%]
tests\test_ai_studio_provenance_and_confirmation.py ...                  [  4%]
tests\test_ai_studio_providers.py ..                                     [  6%]
tests\test_api_health.py ..                                              [  7%]
tests\test_auth.py ..............                                        [ 18%]
tests\test_buyer_requirements.py ...                                     [ 21%]
tests\test_config.py ..                                                  [ 22%]
tests\test_crafts.py ....                                                [ 25%]
tests\test_deduplication.py ...                                          [ 28%]
tests\test_demand_forecasting.py .....                                   [ 32%]
tests\test_demand_observations.py ...                                    [ 34%]
tests\test_demand_trends.py ...                                          [ 36%]
tests\test_embeddings.py ...                                             [ 39%]
tests\test_fair_price_engine.py ..                                       [ 40%]
tests\test_governance_flags.py ..                                        [ 42%]
tests\test_governance_provenance_chain.py ....                           [ 45%]
tests\test_governance_rbac_idor.py .                                     [ 46%]
tests\test_ingestion_validation.py .....                                 [ 50%]
tests\test_market_evidence.py ..                                         [ 51%]
tests\test_matching_engine.py ....                                       [ 54%]
tests\test_models.py ..                                                  [ 56%]
tests\test_moderation_workflows.py ...                                   [ 58%]
tests\test_offline_sync.py ...                                           [ 60%]
tests\test_passports_and_verifications.py ...                            [ 63%]
tests\test_pricing_auth_idor.py ....                                     [ 66%]
tests\test_pricing_costs.py ...                                          [ 68%]
tests\test_pricing_decimal_precision.py ...                              [ 71%]
tests\test_product_authorization.py ...                                  [ 73%]
tests\test_product_media.py ...                                          [ 75%]
tests\test_product_provenance.py ...                                     [ 78%]
tests\test_production_security_hardening.py .......                      [ 83%]
tests\test_products.py ....                                              [ 86%]
tests\test_profiles.py ..                                                [ 88%]
tests\test_provenance.py ..                                              [ 89%]
tests\test_rbac.py ........                                              [ 96%]
tests\test_requirement_understanding.py ..                               [ 97%]
tests\test_rfq_enquiry_lifecycle.py ...                                  [100%]

================== 128 passed, 1 warning in 83.70s (0:01:23) ==================
```

| Metric | Result |
|:---|:---|
| **Total Test Items** | **128** |
| **Passed** | **128 (100.0%)** |
| **Failed** | **0** |
| **Skipped** | **0** |
| **Warnings** | **1** (FastAPI TestClient deprecation warning) |
| **Regressions** | **0** |

---

## 2. Test Breakdown by Phase

1. **Phase 1: Database, Models & Real Data Ingestion** (12 tests)
   - Verified 37 declarative SQLAlchemy tables, deduplication hashing, and GI/ODOP ingestion manifests.
2. **Phase 2: Authentication, RBAC & Craft Passport** (27 tests)
   - Tested Argon2id password verification, JWT issuance, refresh token family rotation, replay revocation, and Craft Passport hierarchy.
3. **Phase 3: Craft Catalogue & Product Foundation** (17 tests)
   - Tested catalogue browsing, product CRUD, media attachment validation, and ownership IDOR defenses.
4. **Phase 4: AI Product Studio** (8 tests)
   - Tested multimodal vision analysis staging, suggestion review isolation, and artisan human confirmation gates.
5. **Phase 5: Explainable Fair Price Intelligence** (14 tests)
   - Tested pure Python Decimal arithmetic, living-wage floor guarantees, $N \ge 3$ market evidence thresholds, and step-by-step mathematical explanations.
6. **Phase 6: Buyer–Artisan Semantic Matching** (12 tests)
   - Tested `gemini-embedding-2` 768-dim vector embeddings, hard constraint elimination, 7-factor scoring, and RFQ negotiation lifecycles.
7. **Phase 7: Demand Intelligence & Offline Sync** (14 tests)
   - Tested demand observation aggregation, empirical trends, multi-gate eligibility ($N \ge 12$), walk-forward validation (zero leakage), and PWA IndexedDB batch sync with idempotency.
8. **Phase 8: Admin Moderation, Governance & Provenance Auditing** (17 tests)
   - Tested canonical JSON serialization, SHA-256 hash chaining, tamper detection, neutral review signals, and critical-field moderation allowlists.
9. **Phase 9: Production Security Hardening & Readiness** (7 tests)
   - Tested security headers injection, correlation ID propagation, production secret enforcement, deep readiness probe, and AI failure safe degradation.

---

## 3. Frontend Production Build Verification

- **Command**: `next build`
- **Configuration**: [`frontend/next.config.mjs`](file:///e:/frontend/next.config.mjs) (`output: "standalone"`)
- **Compilation Result**: **SUCCESS (Exit Code 0)**
- **Routes Compiled**: **21 static and dynamic pages** (including `/catalogue`, `/artisan/*`, `/buyer/*`, `/admin/*`).

---

## 4. Empirical Performance Benchmarks
*(Measured on Development/Host Environment — Not presented as a Cloud SLA)*

| Benchmark Workload | Iterations / Sample Size | Measured Execution Time |
|:---|:---|:---|
| **Fair Price Cost Calculation (`FAIR_PRICE_ENGINE_V1`)** | 100 consecutive runs | **0.0400 ms** per run |
| **Demand Forecasting Run (12m WMA, `DEMAND_ENGINE_V1`)** | 100 consecutive runs | **0.0982 ms** per run |
| **Provenance Hash Computation (SHA-256 + Canonical JSON)** | 500 consecutive events | **24.3522 µs** per event |
| **Full Test Suite Execution (All 9 Phases)** | 128 tests | **83.70 s** total execution |
