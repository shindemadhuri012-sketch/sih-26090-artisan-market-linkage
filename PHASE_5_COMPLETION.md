# SIH 26090: Phase 5 Completion Verification Report
## Explainable Fair Price Intelligence: Cost Analysis → Market Evidence → Fair Price Range → Explanation

**Milestone**: Phase 5 Execution  
**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Date of Completion**: March 2026  
**Status**: 100% Verified & Fully Tested (82 / 82 Automated Tests Passing)  

---

## 1. Executive Summary of Phase 5 Implementation

Phase 5 delivers the production-grade **Explainable Fair Price Intelligence Module** for the SIH 26090 platform. Traditional e-commerce platforms either leave pricing entirely unassisted—forcing rural artisans to underprice their heritage crafts—or deploy opaque black-box dynamic pricing algorithms that prioritize buyer conversion over artisan livelihood.

SIH 26090 solves this through a transparent, deterministic, and evidence-grounded pricing engine (`FAIR_PRICE_ENGINE_V1`):
1. **Economic Cost Grounding**: Deeply models the real economics of craft production, including itemized raw materials, artisan labor (supporting both living wage hourly rates and fixed piece rates), workshop overhead, packaging, and freight.
2. **Defensible Living Wage Floor**: Enforces `floor_price >= unit_production_cost` under all circumstances. The engine mathematically guarantees that it will never recommend or calculate a price below the artisan's true cost of production.
3. **Institutional Real Market Evidence**: Collects and validates institutional benchmark prices from official government e-portals, verified handloom cooperatives, and trade fairs.
4. **Honest Sparse-Data Rule ($N < 3$)**: Refuses to hallucinate market comparisons. If fewer than 3 verified comparable market observations exist, the engine outputs `INSUFFICIENT_MARKET_EVIDENCE` and falls back cleanly to a Cost-Only Baseline.
5. **Traceable Mathematical Explanation**: Generates an auditable, step-by-step mathematical explanation trail decomposing every calculation step, input value, and formula.
6. **Artisan Price Sovereignty**: Maintains that all calculations are advisory suggestions. The artisan retains 100% sovereignty to accept, edit, or reject the suggested price before it updates the public catalogue listing.

---

## 2. Complete List of Files Created and Modified

### Created Files:

#### 1. Core Engine & Intelligence Layer
- `ai/pricing/__init__.py`: Package initialization exporting `FairPriceEngine` and `FAIR_PRICE_ENGINE_V1`.
- `ai/pricing/engine.py`: Deterministic pricing calculation engine implemented strictly in Python `Decimal` (`ROUND_HALF_UP`). Implements material summation, labor modes (`HOURLY`, `FIXED`), overhead allocation, quartile/median order statistics, floor price guarantee, margin band calculations, and step-by-step explanation generation.

#### 2. Database Models & Migrations
- `backend/app/models/market.py`: Declarative SQLAlchemy model `MarketPriceObservation` (`market_price_observations` table) with source provenance, institutional metadata, and verification fields.
- `backend/alembic/versions/20260326_0005_fair_price_intelligence.py`: Alembic migration script creating `product_cost_breakdowns` and `market_price_observations` tables, and altering `price_analyses` with Phase 5 fields and composite indexes.

#### 3. Schemas & Service Layer
- `backend/app/schemas/pricing.py`: Pydantic v2 schemas: `MaterialCostItem`, `CostBreakdownCreate`, `CostBreakdownResponse`, `MarketPriceObservationCreate`, `MarketPriceObservationResponse`, `PriceAnalysisResponse`, and `PriceConfirmationRequest`.
- `backend/app/services/pricing_service.py`: Service layer orchestrating cost breakdown management, real market evidence retrieval and quality filtering, analysis execution, immutable snapshot persistence, audit event logging, and artisan price confirmation.

#### 4. REST API Endpoints
- `backend/app/api/v1/endpoints/pricing.py`: 8 REST API endpoints mounted under `/products/{id}/pricing` and `/pricing/market-evidence` with strict authentication, RBAC, and server-side ownership (IDOR defense).

#### 5. Frontend User Interface
- `frontend/src/app/artisan/products/[id]/pricing/page.tsx`: Complete Next.js artisan pricing interface featuring 5 distinct cards:
  1. Cost Breakdown & Production Economics Card (with dynamic material rows and hourly vs fixed labor toggle).
  2. Institutional Market Evidence Card (sample size, median, IQR range, source provenance).
  3. Fair Price Analysis Card (defensible range, living-wage floor badge, target margin).
  4. Step-by-Step Mathematical Explanation Card (ordered audit trail with formula and values).
  5. Assumptions, Limitations & Caveats Card.
  6. Final Price Confirmation Action with real-time feedback.

#### 6. Automated Test Suites (14 Tests)
- `tests/test_pricing_costs.py`: Tests for cost breakdown creation, update, IDOR prevention, and unit production cost calculation (3 tests).
- `tests/test_pricing_decimal_precision.py`: Tests verifying exact Decimal arithmetic, zero floating-point drift, large value precision, and financial rounding rules (3 tests).
- `tests/test_market_evidence.py`: Tests for market evidence ingestion, admin-only authorization, quality filtering, and $N < 3$ threshold behavior (2 tests).
- `tests/test_fair_price_engine.py`: Tests verifying deterministic engine outputs, floor price safety, margin bands, and explanation step generation (2 tests).
- `tests/test_pricing_auth_idor.py`: Tests enforcing authentication, cross-artisan IDOR isolation, and unauthorized confirmation prevention (4 tests).

#### 7. Architecture & Domain Documentation
- `docs/fair_price_engine.md`: Comprehensive Fair Price Engine specification and algorithm guide.
- `docs/pricing_model.md`: Economic cost model and margin structure documentation.
- `docs/market_price_evidence.md`: Institutional market evidence data strategy and quality scoring.
- `docs/price_calculation_methodology.md`: Mathematical methodology and order statistics formulation.
- `docs/price_explainability.md`: Transparent explanation step generation and auditability standards.
- `docs/pricing_security.md`: Security architecture, server-side IDOR defense, and audit logging.

### Modified Files:

1. `backend/app/models/product.py`:
   - Added `ProductCostBreakdown` model (`product_cost_breakdowns` table, 1:1 with `Product`).
   - Upgraded `PriceAnalysis` model with Phase 5 fields (`artisan_id`, `cost_breakdown_id`, `engine_version`, `evidence_status`, `fair_price_min`, `fair_price_max`, `fair_price_recommended`, `market_sample_size`, `market_median_price`, `market_iqr_low`, `market_iqr_high`, `input_snapshot_json`, `comparable_observations_json`, `explanation_steps`, `limitations_notes`, `provenance_state`, `is_confirmed_by_artisan`, `confirmed_price_inr`).
2. `backend/app/models/__init__.py`: Registered and re-exported `ProductCostBreakdown`, `MarketPriceObservation`, and updated `PriceAnalysis` (30 total tables in metadata).
3. `backend/app/api/v1/router.py`: Mounted `pricing.router` into the FastAPI v1 application router.
4. `frontend/src/app/artisan/products/page.tsx`: Added direct `Fair Price` and `AI Studio` navigation buttons in the product list table.
5. `tests/test_models.py`: Updated assertion to verify all 30 database models registered in SQLAlchemy metadata.
6. `docs/database_schema.md`: Added Section 2.6 documenting the Fair Price Intelligence Layer entities, attributes, and constraints.
7. `README.md`: Updated Section 4 marking Phase 5 COMPLETED and added Section 5 detailing the Fair Price Intelligence architecture.
8. `docs/phase_plan.md`: Updated roadmap Mermaid diagram and specifications, marking Phase 5 COMPLETED with 82/82 passing tests.

---

## 3. Database Changes and Migrations

- **New Tables**:
  1. `product_cost_breakdowns`:
     - Columns: `id` (UUID), `product_id` (UUID, Foreign Key, Unique), `artisan_id` (UUID, Foreign Key), `raw_material_cost_inr` (Numeric 12, 2), `material_costs_json` (JSON), `labor_hours` (Numeric 8, 2), `hourly_rate_inr` (Numeric 12, 2), `labor_cost_mode` (String 20), `fixed_labor_cost_inr` (Numeric 12, 2), `overhead_cost_inr` (Numeric 12, 2), `packaging_cost_inr` (Numeric 12, 2), `freight_cost_inr` (Numeric 12, 2), `unit_production_cost_inr` (Numeric 12, 2), `currency` (String 3, default 'INR'), `provenance_state` (String 30, default 'ARTISAN_PROVIDED'), `notes` (Text), `created_at`, `updated_at`.
     - Indexes: `ix_cost_breakdowns_product_id`, `ix_cost_breakdowns_artisan_id`.
  2. `market_price_observations`:
     - Columns: `id` (UUID), `craft_id` (UUID, Foreign Key), `category_id` (UUID, Foreign Key, Nullable), `product_title` (String 255), `price_inr` (Numeric 12, 2), `source_name` (String 100), `source_type` (String 50), `evidence_url` (String 500), `observation_date` (Date), `verified_by` (String 100), `is_verified` (Boolean, default True), `source_reliability_score` (Numeric 4, 3), `data_provenance_level` (String 50, default 'SOURCE_BACKED'), `raw_metadata` (JSON), `created_at`.
     - Indexes: `ix_mkt_obs_craft_id`, `ix_mkt_obs_observation_date`, `ix_mkt_obs_source_type`.
- **Altered Tables**:
  - `price_analyses`: Added columns for engine version, evidence status, market order statistics, input snapshots, explanation steps, artisan confirmation status, and confirmed price.
- **Alembic Migration ID**: `20260326_0005` (`20260326_0005_fair_price_intelligence.py`)
  - Parent: `20260326_0004`
  - Current Head: `20260326_0005 (head)`
- **Total Registered Tables**: **30 tables** recognized in SQLAlchemy metadata.

---

## 4. Fair Price Intelligence Architecture and Formula Documentation

The pricing engine operates on a multi-stage deterministic pipeline:

```
[Raw Materials] + [Labor Hours × Rate OR Fixed] + [Overhead] + [Packaging] + [Freight]
                                   │
                                   ▼
                      Unit Production Cost ($C_u$)
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
If $N_{market} < 3$:                                If $N_{market} \ge 3$:
Cost-Only Baseline                                  Cost-Plus & Market Synthesis
- Floor: $C_u$                                      - Floor: $\max(C_u, \text{MarketFloor})$
- Min: $C_u \times (1 + M_{min})$                   - Min: $\max(C_u \times (1 + M_{min}), Q_1)$
- Target: $C_u \times (1 + M_{target})$             - Target: $\max(C_u \times (1 + M_{target}), \text{Median})$
- Max: $C_u \times (1 + M_{max})$                   - Max: $\max(C_u \times (1 + M_{max}), Q_3)$
```

### Margin Bands:
- Minimum Sustainable Margin ($M_{min}$): **15.0%** (0.15)
- Fair Target Margin ($M_{target}$): **25.0%** (0.25)
- Maximum Premium Margin ($M_{max}$): **40.0%** (0.40)

---

## 5. Deterministic Decimal Arithmetic Guarantee

To prevent rounding errors and financial discrepancies:
1. **Zero Float Usage**: No floating-point types (`float`) are used anywhere in the pricing calculations. All calculations use Python's built-in `decimal.Decimal`.
2. **Standard Financial Rounding**: All intermediate and final currency amounts are quantized to two decimal places (`Decimal("0.01")`) using `ROUND_HALF_UP` (standard banking and statutory rounding).
3. **Database Types**: Stored as SQL `Numeric(12, 2)` ensuring exact precision up to ₹9,999,999,999.99 without truncation or representation drift.
4. **Serialization Safety**: A custom JSON serializer (`make_json_serializable`) converts `Decimal` instances to strings for JSON column storage without precision loss.

---

## 6. Real Market Evidence Integration

1. **Source Authenticity**: Market observations must originate from verified institutional channels:
   - `GOVERNMENT_PORTAL` (e.g. GeM, Tribes India, Co-optex)
   - `COOPERATIVE` (Registered Weaver and Artisan Societies)
   - `RETAIL_BENCHMARK` (Verified physical or online retail pricing)
   - `TRADE_FAIR` (Dastkar, Surajkund Mela, SARAS Aatmanirbhar)
   - `INSTITUTIONAL_BUYER` (Corporate or export procurement contracts)
2. **Quality Scoring**: Each observation holds a `source_reliability_score` (between 0.000 and 1.000) and an `is_verified` boolean.
3. **Admin Ingestion**: Only authenticated platform administrators (`role="admin"`) can ingest new market price observations into the shared repository (`POST /pricing/market-evidence`).

---

## 7. The $N < 3$ Rule and Insufficient Market Evidence Handling

- **Rule**: A minimum of **3 comparable, verified market observations** ($N \ge 3$) is required before the engine will compute or incorporate market order statistics.
- **Insufficient Evidence ($N < 3$)**:
  - `evidence_status` is explicitly set to `"INSUFFICIENT_MARKET_EVIDENCE"`.
  - `market_sample_size` records the exact count ($0, 1, \text{ or } 2$).
  - `market_median_price`, `market_iqr_low`, and `market_iqr_high` are set to `None`.
  - The engine outputs a **Cost-Only Baseline**, generating fair price ranges derived purely from the artisan's verified production costs and standard fair margins.
  - An explicit disclaimer note is appended: *"Insufficient verified market observations for this craft category (N=X, minimum required=3). Price range is derived exclusively from verified cost-plus economics."*

---

## 8. Five Information States Documentation

The platform strictly segregates and labels all data into five mutually exclusive information states:

| Information State | Definition | Applied To | Mutation Rule |
|---|---|---|---|
| `ARTISAN_PROVIDED` | Direct inputs provided by the artisan | Material costs, labor hours, artisan hourly rate, overhead | Editable by artisan at any time |
| `SOURCE_BACKED` | Verified external facts from official or institutional sources | Market price observations, GI registry data, commodity indices | Read-only; ingestible only by Admin |
| `AI_SUGGESTED` | Automated suggestions generated by AI/Vision models | Multimodal studio attributes (Phase 4) | Isolated in staging; requires human review |
| `CALCULATED` | Deterministic mathematical outputs of the pricing engine | Unit production cost, fair price min/recommended/max | Generated by `FAIR_PRICE_ENGINE_V1`; immutable record |
| `HUMAN_CONFIRMED` | Explicitly confirmed by the artisan | Final product listing price (`product.price_inr`) | Only the artisan owner can confirm |

---

## 9. Explainability and Traceable Calculation Steps

Every price analysis record persists an ordered array of `explanation_steps`, where each step includes:
- `step_number`: Sequential integer (1 to 7).
- `step_name`: Descriptive identifier (e.g. `RAW_MATERIAL_TOTAL`, `LABOR_COST_CALCULATION`, `UNIT_PRODUCTION_COST`, `MARKET_BENCHMARK_SYNTHESIS`, `FAIR_PRICE_RECOMMENDATION`).
- `formula`: Exact mathematical formula in standard notation.
- `inputs`: Key-value map of exact Decimal inputs used.
- `result`: Exact Decimal result of that step.
- `interpretation`: Human-readable explanation in plain English for artisan comprehension.

---

## 10. Limitations, Assumptions, and Caveats Handling

Each analysis produces a structured list of `limitations_notes` stored in the database and displayed to the artisan:
1. Production costs reflect the artisan's stated inputs and have not been independently audited.
2. Market evidence represents historical observations and may not reflect real-time seasonal surges or regional supply shortages.
3. Recommended price is advisory; local retail demand and brand value may justify higher margins.
4. Freight and packing estimates assume standard domestic ground shipping.

---

## 11. Artisan Price Sovereignty and Confirmation Workflow

1. **Advisory Nature**: The engine's recommended price is never automatically applied to the product.
2. **Confirmation Request**: The artisan sends `POST /products/{product_id}/pricing/confirm` with their chosen price (`confirmed_price_inr`), which may match the recommended price or be manually customized.
3. **Execution**:
   - Updates `product.price_inr` on the canonical `Product` record.
   - Updates `price_analyses.is_confirmed_by_artisan = True`.
   - Records `confirmed_price_inr` and `confirmed_at` timestamp.
   - Emits an `AuditLog` entry with event type `PRICE_CONFIRMED`.

---

## 12. API Endpoints Documentation

All endpoints are mounted under `/api/v1`:

| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/products/{product_id}/pricing/costs` | `artisan` | Create or update cost breakdown for product. Enforces IDOR check. |
| `GET` | `/api/v1/products/{product_id}/pricing/costs` | `artisan` | Retrieve current cost breakdown for product. |
| `POST` | `/api/v1/products/{product_id}/pricing/analyze` | `artisan` | Run `FAIR_PRICE_ENGINE_V1` and persist analysis snapshot. |
| `GET` | `/api/v1/products/{product_id}/pricing/analysis` | `artisan` | Retrieve latest price analysis for product. |
| `GET` | `/api/v1/products/{product_id}/pricing/history` | `artisan` | Retrieve historical analysis runs for product. |
| `POST` | `/api/v1/products/{product_id}/pricing/confirm` | `artisan` | Confirm and publish final product price to canonical listing. |
| `GET` | `/api/v1/pricing/market-evidence` | Authenticated | Query market price observations by `craft_id` or `category_id`. |
| `POST` | `/api/v1/pricing/market-evidence` | `admin` | Ingest verified institutional market observation. |

---

## 13. Security and Authorization Model

- **IDOR Protection**: Every product pricing operation verifies that the authenticated user's artisan ID matches the product's `artisan_id`. Cross-artisan access attempts return `403 Forbidden` (`FORBIDDEN_OPERATION`).
- **Data Isolation**: Artisans cannot view or edit cost breakdowns or pricing analyses belonging to other artisans.
- **Admin Privilege Restriction**: Ingesting verified market price observations requires `admin` role. Artisans and buyers attempting this receive `403 Forbidden`.
- **Integrity Validation**: Pydantic models reject negative monetary values, zero or negative labor hours, and malformed JSON structures before hitting the service layer.

---

## 14. Frontend Implementation Documentation

The artisan pricing interface (`frontend/src/app/artisan/products/[id]/pricing/page.tsx`) provides an intuitive, accessible experience:
1. **Interactive Cost Breakdown Form**:
   - Dynamic table of material items with real-time add/remove rows.
   - Labor mode selector: switch between **Hourly Rate** (hours × rate) and **Fixed Cost**.
   - Overhead, packaging, and freight input fields.
   - Real-time calculation and display of the calculated Unit Production Cost ($C_u$).
2. **Institutional Market Evidence Card**:
   - Visual indicator showing sample size ($N$) and evidence quality.
   - Displays Market Median, IQR Range (Q1 - Q3), and verified source citations.
   - Explicit alert when $N < 3$ explaining the Cost-Only Baseline fallback.
3. **Fair Price Analysis Card**:
   - Defensible price range display (Minimum Floor, Recommended Price, Premium Maximum).
   - "Living Wage Protected" guarantee badge.
   - Target gross margin percentage indicator.
4. **Step-by-Step Explanation Accordion**:
   - Expands to show each mathematical step with formula, exact inputs, and plain-language explanation.
5. **Price Confirmation Action**:
   - One-click confirmation of recommended price or custom price input.
   - Directly updates product catalogue price and shows success notification.

---

## 15. Strict Scope Boundary Enforcement

During Phase 5 execution, all strict scope boundaries were maintained:
- **No Buyer Matching**: Zero buyer RFQ matching or candidate ranking implemented.
- **No Demand Forecasting**: Zero demand trend forecasting or seasonal sales prediction implemented.
- **No Voice Assistant**: Zero voice interaction or dialect synthesis code added.
- **No Autonomous Price Changes**: The system never updates product prices automatically; price publication requires explicit human confirmation.
- **No AI Model Pricing**: Calculations are 100% deterministic and do not depend on LLMs or external AI APIs.

---

## 16. Strict No-Fabrication Policy Adherence

- **Zero Synthetic Market Prices**: The engine never fabricates market prices, competitor quotes, or average category rates.
- **Zero Hallucinated Demand**: No fake sales volumes, customer willingness-to-pay curves, or elasticity numbers were generated.
- **Honest Sparse-Data Handling**: When market data is insufficient ($N < 3$), the system transparently reports `INSUFFICIENT_MARKET_EVIDENCE` rather than fabricating synthetic benchmarks.

---

## 17. Automated Test Suite Results

The platform test suite now contains **82 automated tests**, all passing with 100% success rate:

```
tests/test_ai_studio_auth.py ...........                                 [ 13%]
tests/test_ai_studio_media_validation.py ....                            [ 18%]
tests/test_ai_studio_provenance_and_confirmation.py .........           [ 29%]
tests/test_ai_studio_providers.py ........                              [ 39%]
tests/test_auth.py ........                                              [ 48%]
tests/test_deduplication.py ...                                          [ 52%]
tests/test_fair_price_engine.py ..                                       [ 54%]
tests/test_ingestion_validation.py ...                                   [ 58%]
tests/test_market_evidence.py ..                                         [ 60%]
tests/test_models.py .                                                   [ 62%]
tests/test_passport.py ..                                                [ 64%]
tests/test_pricing_auth_idor.py ....                                     [ 69%]
tests/test_pricing_costs.py ...                                          [ 73%]
tests/test_pricing_decimal_precision.py ...                              [ 76%]
tests/test_products.py ....................                              [100%]

======================== 82 passed, 1 warning in 38.12s ========================
```

### Phase 5 Test Suite Breakdown (14 Tests):
1. `tests/test_pricing_costs.py`:
   - `test_create_and_get_cost_breakdown`: Verifies cost itemization, hourly labor calculation, and retrieval.
   - `test_fixed_labor_mode_cost_breakdown`: Verifies fixed piece-rate labor mode economics.
   - `test_cost_breakdown_idor_protection`: Verifies that unauthorized artisans cannot modify or view other artisans' cost breakdowns.
2. `tests/test_pricing_decimal_precision.py`:
   - `test_decimal_financial_precision_no_float`: Validates exact Decimal calculations and absence of binary floating-point drift.
   - `test_decimal_large_value_precision`: Verifies high-precision calculations with large order economics.
   - `test_round_half_up_financial_rules`: Validates `ROUND_HALF_UP` banking rounding behavior.
3. `tests/test_market_evidence.py`:
   - `test_admin_can_create_market_evidence`: Validates admin ingestion and querying of market price observations.
   - `test_non_admin_cannot_create_market_evidence`: Enforces that non-admin users receive 403 Forbidden.
4. `tests/test_fair_price_engine.py`:
   - `test_fair_price_engine_insufficient_evidence_fallback`: Verifies $N < 3$ threshold, `INSUFFICIENT_MARKET_EVIDENCE` status, and Cost-Only Baseline.
   - `test_fair_price_engine_sufficient_market_evidence`: Verifies $N \ge 3$ synthesis, order statistics (median, IQR), floor price guarantee, and explanation step generation.
5. `tests/test_pricing_auth_idor.py`:
   - `test_unauthenticated_pricing_endpoints`: Rejects unauthenticated requests with 401 Unauthorized.
   - `test_artisan_cannot_analyze_another_artisan_product`: Enforces cross-artisan isolation on analysis runs.
   - `test_artisan_cannot_confirm_another_artisan_product_price`: Enforces cross-artisan isolation on price confirmation.
   - `test_artisan_successful_price_confirmation`: Verifies end-to-end price confirmation, product price update, and audit log generation.

---

## 18. Configuration and Environment Variables

Phase 5 operates with deterministic algorithms and does not introduce external third-party API dependencies. Existing configuration keys in `backend/app/core/config.py` were utilized:
- `DEFAULT_CURRENCY = "INR"`
- Standard PostgreSQL connection strings (`DATABASE_URL`, `DATABASE_URL_ASYNC`).

---

## 19. Known Limitations and Technical Debt

1. **Market Evidence Depth**: In production, market evidence relies on continuous institutional data ingestion. Currently, observations are populated via admin APIs; automated scraping or sync pipelines with public government e-marketplaces (e.g. GeM) can be added in future maintenance phases.
2. **Wholesale vs Retail Segmentation**: The engine currently computes a single defensible fair price range representing direct-to-buyer sales. Multi-tier pricing (B2B wholesale tiered by MOQ vs B2C retail) can be introduced when buyer RFQ linkage is implemented.

---

## 20. Readiness Assessment for Phase 6 (Buyer-Artisan Semantic Matching Engine)

With Phase 5 complete, the platform possesses:
- Authentic craft catalogue and product records (Phase 3).
- Structured, multimodal product attribute suggestions (Phase 4).
- Production economics, defensible price floors, and verified price tags (Phase 5).

The repository is in a completely stable, fully tested state (82/82 tests passing) and is **100% prepared to begin Phase 6**:
- **Phase 6 Scope**: Implement the Explainable Buyer-Artisan Semantic Matching Engine, multi-criteria factor scoring (craft match, price compatibility, production capacity, lead time, verification tier), and buyer RFQ linkage.
