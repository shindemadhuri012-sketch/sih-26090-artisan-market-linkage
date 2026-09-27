# SIH 26090: Database Schema & Entity Documentation
## Complete Relational & Vector Data Model (31 Implemented Entities)

---

## 1. Schema Summary

All 31 entities specified in the platform blueprints have been implemented as declarative SQLAlchemy 2.0 ORM models in `backend/app/models/` and verified with Alembic migrations:

| Entity Name | Table Name | Logical Domain | Primary Key | Key Indexes & Constraints |
|---|---|---|---|---|
| **Role** | `roles` | Auth & RBAC | Integer (Serial) | `unique(name)`, `idx_roles_name` |
| **User** | `users` | Identity | UUIDv4 (String 36) | `unique(phone)`, `unique(email)`, `idx_users_role` |
| **RefreshToken** | `refresh_tokens` | Session & Security | UUIDv4 (String 36) | `unique(token_hash)`, `idx_token_user` |
| **OTPCode** | `otp_codes` | Auth / Verification | UUIDv4 (String 36) | `idx_otp_identifier` |
| **AuditLog** | `audit_logs` | Security & Audit | UUIDv4 (String 36) | `idx_audit_entity(entity_type, entity_id)` |
| **Notification** | `notifications` | Messaging | UUIDv4 (String 36) | `idx_notifications_user(user_id, is_read)` |
| **DataSource** | `data_sources` | Provenance | UUIDv4 (String 36) | `unique(source_identifier)` |
| **DataImport** | `data_imports` | Provenance | UUIDv4 (String 36) | `idx_imports_source(data_source_id)` |
| **CraftCategory** | `craft_categories` | Master Directory | UUIDv4 (String 36) | `unique(name)`, `idx_parent_id (hierarchical tree)` |
| **Craft** | `crafts` | Master Directory | UUIDv4 (String 36) | `unique(gi_tag_number)`, `idx_crafts_normalized_name`, `idx_crafts_origin` |
| **ArtisanProfile** | `artisan_profiles` | Artisan Domain | UUIDv4 (String 36) | `unique(user_id)`, `unique(pehchan_id)`, `idx_artisan_district` |
| **ArtisanCraft** | `artisan_crafts` | Skill Association | UUIDv4 (String 36) | `unique(artisan_id, craft_id)`, `idx_skill_level` |
| **Verification** | `verifications` | KYC & Provenance | UUIDv4 (String 36) | `idx_verif_artisan(artisan_id, status)` |
| **CraftPassport** | `craft_passports` | Digital Provenance | UUIDv4 (String 36) | `unique(passport_uuid)` |
| **Product** | `products` | Catalogue | UUIDv4 (String 36) | `unique(sku)`, `idx_products_artisan`, `idx_products_craft`, `VECTOR(768)` |
| **ProductMedia** | `product_media` | Media Assets | UUIDv4 (String 36) | `idx_media_product(product_id)`, `idx_checksum` |
| **ProductAttributes**| `product_attributes`| Technical Specs | UUIDv4 (String 36) | `unique(product_id)` |
| **ProductCostBreakdown**| `product_cost_breakdowns`| Cost Structure | UUIDv4 (String 36) | `unique(product_id)`, `idx_cost_breakdowns_artisan_id` |
| **MarketPriceObservation**| `market_price_observations`| Real Evidence | UUIDv4 (String 36) | `idx_mkt_obs_craft_id`, `idx_mkt_obs_date` |
| **PriceAnalysis** | `price_analyses` | Fair Pricing | UUIDv4 (String 36) | `idx_price_product(product_id)`, `idx_price_analyses_artisan_id` |
| **AIProductAnalysis**| `ai_product_analyses`| AI Studio Staging | UUIDv4 (String 36) | `idx_ai_analyses_product_id`, `idx_ai_analyses_idempotency_key` |
| **AIProductSuggestion**| `ai_product_suggestions`| Staged Suggestions | UUIDv4 (String 36) | `idx_ai_suggestions_analysis_id`, `idx_ai_suggestions_status` |
| **BuyerProfile** | `buyer_profiles` | Buyer Domain | UUIDv4 (String 36) | `unique(user_id)` |
| **BuyerRequirement**| `buyer_requirements`| Procurement (RFQ) | UUIDv4 (String 36) | `idx_buyer_req_buyer`, `VECTOR(768)` |
| **RequirementUnderstanding**| `requirement_understandings`| RFQ AI Staging | UUIDv4 (String 36) | `idx_req_und_req_id`, `idx_req_und_buyer_id` |
| **Match** | `matches` | Matching Engine | UUIDv4 (String 36) | `idx_matches_req_rank(requirement_id, rank)` |
| **MatchExplanation**| `match_explanations`| Explainability | UUIDv4 (String 36) | `unique(match_id)` |
| **Enquiry** | `enquiries` | Negotiation | UUIDv4 (String 36) | `idx_enquiries_buyer_artisan` |
| **Order** | `orders` | Fulfillment | UUIDv4 (String 36) | `unique(enquiry_id)`, `unique(order_reference_number)` |
| **DemandObservation**|`demand_observations`| Real Analytics | UUIDv4 (String 36) | `idx_demand_craft_period(craft_id, period_start)`|
| **DemandForecast** | `demand_forecasts` | Demand Projection| UUIDv4 (String 36) | `idx_forecast_craft(craft_id)` |

---

## 2. Phase 3 Data Architecture Enhancements

### 2.1 Category Tree Hierarchy (`craft_categories`)
- Added `parent_id` foreign key referencing `craft_categories.id` (`ondelete="SET NULL"`).
- Enables arbitrary nested subcategories (e.g. Textiles -> Brocades -> Extra-Weft Zari).

### 2.2 Artisan-Craft Skill Association (`artisan_crafts`)
- Many-to-many linkage between `ArtisanProfile` and `Craft`.
- Attributes: `skill_level` (`APPRENTICE`, `JOURNEYMAN`, `MASTER_CRAFTSMAN`, `NATIONAL_AWARD_WINNER`), `years_of_experience`, `is_primary`, `technique`, `evidence_url`, `status`.
- Unique constraint: `(artisan_id, craft_id)` prevents duplicate linkages.

### 2.3 Decoupled Product Commercial Parameters (`products`)
- `stock_quantity`: Immediate on-hand ready inventory.
- `monthly_production_capacity`: Sustainable monthly production capacity for institutional matchmaking.
- `min_order_quantity`: Minimum batch requirement.
- `lead_time_days`: Production fulfillment turnaround time.
- `sku`: Unique identifier format (`PRD-{HEX4}`).
- `ai_metadata`: Reserved JSONB schema for future Phase 4/5 multimodal AI recommendations.

### 2.4 Product Media Assets (`product_media`)
- `storage_key`: Object storage pointer (MinIO/S3).
- `checksum_sha256`: SHA-256 digest ensuring byte-level integrity.
- MIME type restriction: Validated against approved image/audio/document types. Max 10MB file size limit.

### 2.5 AI Product Studio Staging Layer (`ai_product_analyses`, `ai_product_suggestions`)
- `ai_product_analyses`: Staged record of multimodal vision inference runs with immutable input provenance (`media_id`, `media_checksum`), provider/model identifiers, versioned prompts, status lifecycle, and execution timings.
- `ai_product_suggestions`: Fine-grained field-level suggestions (`title`, `materials`, `technique`, etc.) holding original AI predictions, uncalibrated confidence scores, artisan confirmation states (`AI_SUGGESTED`, `HUMAN_CONFIRMED`, `REJECTED`), and preserved confirmed values.
- Staging-to-Canonical isolation: AI predictions remain strictly quarantined until the artisan explicitly accepts or edits them via `/confirm`.

### 2.6 Fair Price Intelligence Layer (`product_cost_breakdowns`, `market_price_observations`, `price_analyses`)
- `product_cost_breakdowns`: 1:1 relationship with `Product` storing granular production economics:
  - Material costs list (`material_costs_json`: item name, unit, quantity, unit price, source provenance).
  - Raw material total, labor hours, artisan hourly rate, or fixed labor cost (`labor_cost_mode`: `HOURLY` or `FIXED`).
  - Overhead, packaging, freight, and calculated unit production cost.
  - All monetary values stored with exact Python `Decimal` / SQL `Numeric(12, 2)` precision.
  - Provenance state: `ARTISAN_PROVIDED`.
- `market_price_observations`: Real institutional market price evidence collected from verified external sources:
  - Linked to `craft_id` and optional `category_id`.
  - Verification fields: `price_inr`, `source_name`, `source_type` (`GOVERNMENT_PORTAL`, `RETAIL_BENCHMARK`, `COOPERATIVE`, `TRADE_FAIR`, `INSTITUTIONAL_BUYER`), `evidence_url`, `observation_date`, `verified_by`.
  - Quality metrics: `is_verified`, `source_reliability_score`, `data_provenance_level` (`SOURCE_BACKED`).
  - Indexed on `(craft_id, observation_date)` and `source_type`.
- `price_analyses`: Immutable, versioned pricing analyses generated by `FAIR_PRICE_ENGINE_V1`:
  - Foreign keys to `product_id`, `artisan_id`, and `cost_breakdown_id`.
  - Floor price guarantee: `fair_price_min >= unit_production_cost` (living wage protection).
  - Defensible range: `fair_price_min`, `fair_price_max`, `fair_price_recommended`.
  - Market evidence evaluation: `evidence_status` (`SUFFICIENT_MARKET_EVIDENCE` or `INSUFFICIENT_MARKET_EVIDENCE` when $N < 3$), `market_sample_size`, `market_median_price`, `market_iqr_low`, `market_iqr_high`.
  - Audit trail: `input_snapshot_json` (frozen cost & market inputs), `comparable_observations_json`, `explanation_steps` (ordered traceable calculation steps), `limitations_notes`.
  - Confirmation status: `is_confirmed_by_artisan`, `confirmed_price_inr`, `confirmed_at`.
  - Information state: `CALCULATED` $\rightarrow$ `HUMAN_CONFIRMED`.

### 2.7 Buyer–Artisan Matching & RFQ Linkage Layer (`buyer_requirements`, `requirement_understandings`, `matches`, `match_explanations`, `enquiries`)
- `buyer_requirements`: Structured buyer procurement briefs / requests for quotation (RFQs):
  - Target craft, category, quantity, target unit price, maximum budget, deadline date.
  - Institutional parameters: GI certification requirement, desired materials/techniques/motifs, region, acceptable MOQ, lead time, packaging, quality specifications.
  - Semantic vector embedding: `EmbeddingVector(dim=768)` generated via `gemini-embedding-2` with dimension output configured to 768.
  - Embedding tracking: `embedding_model_version` (`gemini-embedding-2`), preventing cross-model vector collisions.
  - Provenance: `USER_DECLARED` / `HUMAN_CONFIRMED`.
- `requirement_understandings`: Isolated staging layer for AI-assisted requirement extraction:
  - Stores raw brief text, extracted structured attributes (`extracted_fields_json`), provider/model metadata (`gemini-2.5-flash`), versioned prompt (`rfq_understanding_v1`), execution latency.
  - Real uncalibrated confidence scores (`confidence_scores_json`) or `None` if uncalibrated. Zero fabricated percentages.
  - Confirmation status: `SUGGESTED` $\rightarrow$ `CONFIRMED` / `REJECTED`, `is_confirmed_by_buyer`, `confirmed_fields_json`, `confirmed_at`.
  - Guarantees AI extractions never silently alter canonical requirements without explicit buyer confirmation.
- `matches`: Candidate rankings generated by `MATCHING_ENGINE_V1` using two-stage hybrid matching:
  - Stage 1: Hard constraint filtering (craft category/craft match, capacity check, MOQ boundary).
  - Stage 2: 7-component scoring ($S_{sem}, S_{craft}, S_{mat}, S_{tech}, S_{cap}, S_{price}, S_{lead}, B_{prov}$).
  - Composite match score ($0.0 \le S \le 1.0$) with dynamic re-weighting when optional constraints are unspecified.
  - Strict classification: Stored and displayed as "MATCH SCORE", never "purchase probability" or "conversion likelihood".
  - Data sufficiency tracking: `data_sufficiency_state` (`COMPLETE`, `PARTIAL_PROFILE`, `UNVERIFIED_DATA`).
  - Candidate lifecycle: `status` (`ACTIVE`, `RFQ_SENT`, `ACCEPTED`, `DECLINED`), `is_dismissed_by_buyer`.
- `match_explanations`: Granular factor-level explainability cards linked 1:1 with `Match`:
  - Structured lists: `positive_reasons` (transparent strengths), `limitations` (clear trade-offs/mismatches), `unmatched_fields`, `missing_fields`.
  - Specific domain justifications: `capacity_justification`, `price_justification`, `provenance_justification`.
  - Traceable, deterministic justification text generated from actual mathematical scores and profile evidence.
- `enquiries` (Extended for RFQ Linkage): Commercial negotiation and communication thread:
  - Unique human-readable RFQ identifier: `rfq_reference_number` (format `RFQ-YYYYMMDD-XXXX`).
  - Linkage: Foreign key `match_id` referencing the origin match scorecard.
  - Negotiation state machine: `SENT` $\rightarrow$ `VIEWED` $\rightarrow$ `NEGOTIATION` $\rightarrow$ `ACCEPTED` / `DECLINED` / `CANCELLED`.
  - Counter-offer capabilities: `counter_unit_price_inr`, `counter_lead_time_days`, `counter_notes`.
### 2.8 Demand Intelligence, Analytics & Offline Sync Layer (`demand_observations`, `demand_forecast_runs`, `demand_forecast_points`, `sync_operations`)
- `demand_observations`: Granular institutional demand signals and historical commercial indicators:
  - Polymorphic foreign keys: `craft_id`, `craft_category_id`, and optional `product_id`.
  - Signal categorization: `signal_tier` (`TIER_1_TRANSACTIONAL`, `TIER_2_COMMERCIAL_INTENT`, `TIER_3_MACRO_INDICATOR`), `observation_type` (`ORDER`, `RFQ_SUBMISSION`, `MARKET_TENDER`, `EXHIBITION_SALE`, `EXPORT_SHIPMENT`, `INQUIRY`).
  - Empirical metrics: `unit_volume` (integer units demanded), `monetary_volume_inr` (exact Decimal value), `time_period_start`, `time_period_end`, `period_type` (`MONTHLY`, `QUARTERLY`, `ANNUAL`).
  - Spatial resolution: `geography_state`, `geography_district`.
  - Data hygiene: `data_quality_status` (`VALIDATED`, `PROVISIONAL`, `FLAGGED_OUTLIER`), `ingestion_batch_id`.
  - Provenance: Inherits `ProvenanceMixin` (`VERIFIED_EXTERNAL_SOURCE` or `SAMPLE_RECORD` with explicit `is_sample_or_demo` flag).
- `demand_forecast_runs`: Versioned execution runs generated by `DEMAND_ENGINE_V1`:
  - Target dimensions: `craft_id` and optional `geography_state`.
  - Engine lineage: `model_name` (`WEIGHTED_MOVING_AVERAGE`, `ADDITIVE_HOLT_WINTERS`), `model_version` (`DEMAND_ENGINE_V1`).
  - Temporal boundaries: `training_start_date`, `training_end_date`, `validation_start_date`, `validation_end_date`, `test_start_date`, `test_end_date` enforcing strict zero-leakage chronological evaluation.
  - Rigorous metrics: `observation_count` (enforcing $N \ge 12$ multi-gate eligibility), `validation_mape`, `validation_rmse` computed strictly on held-out validation points.
  - Transparent metadata: `status` (`ELIGIBLE`, `INSUFFICIENT_HISTORY`, `INSUFFICIENT_DATA_QUALITY`), `limitations_notes`, `parameters_json`.
- `demand_forecast_points`: Time-series projection horizons linked 1:1 to parent run:
  - Point indexing: `forecast_period_month`, `forecast_period_year`.
  - Projections: `projected_demand_index` (relative index), `projected_unit_volume` (integer units).
  - Statistical intervals: `uncertainty_lower`, `uncertainty_upper` (residual standard error prediction intervals).
  - Provenance & semantics: Marked strictly with `information_state='FORECAST'` and `data_sufficiency_status`.
- `sync_operations`: Server-side idempotency registry for offline PWA synchronization:
  - Idempotency & mutation keys: `idempotency_key` (unique index), `client_mutation_id`.
  - User scoping & audit: `user_id` (foreign key to `users.id`), `entity_type` (`PRODUCT`, `RFQ_RESPONSE`, `PROFILE`), `entity_id`, `operation_type` (`CREATE`, `UPDATE`, `DELETE`).
### 2.9 Admin Moderation, Governance & Provenance Auditing Layer (`governance_flags`, `moderation_actions`, `provenance_events`)
- `governance_flags`: Neutral administrative review signals for data quality, missing provenance, and policy anomalies:
  - Scoping: `entity_type` (`Product`, `ArtisanProfile`, `CraftPassport`, `MarketPriceObservation`), `entity_id`.
  - Signal taxonomy: `flag_type` (`MISSING_PROVENANCE`, `PRICE_ANOMALY_REVIEW`, `UNSUPPORTED_CLAIM`, `EXPIRED_EVIDENCE`, `DUPLICATE_SOURCE`, `STALE_MARKET_DATA`, `SAMPLE_EXPOSURE`).
  - Triage attributes: `severity` (`LOW`, `MEDIUM`, `HIGH`), `status` (`OPEN`, `UNDER_INVESTIGATION`, `RESOLVED_VALIDATED`, `RESOLVED_CORRECTED`, `RESOLVED_ACTIONED`, `DISMISSED`).
  - Context & resolution: `details_json` (contextual values), `resolution_notes`, `resolved_by_user_id`, `resolved_at`.
- `moderation_actions`: Audited administrative review decisions across multi-entity backlogs:
  - Target entity: `entity_type` (`Product`, `ArtisanProfile`, `CraftPassport`, `Verification`, `ProductMedia`), `entity_id`.
  - State machine: `previous_status`, `new_status`, `decision` (`APPROVE`, `REJECT`, `REQUEST_CHANGES`, `SUSPEND`, `RESTORE`).
  - Rationale & transparency: `reason_category` (`QUALITY_DEFICIENCY`, `AUTHENTICITY_VERIFIED`, `INCORRECT_ATTRIBUTES`, `POLICY_VIOLATION`, `OTHER`), `moderator_notes` (private), `feedback_to_user` (actionable public feedback), `evidence_reference` (official gazette/registry ID).
  - Idempotency: `idempotency_key` (unique index) preventing duplicate submissions.
- `provenance_events`: Append-only, tamper-evident historical ledger tracking field-level provenance changes:
  - Granular target: `entity_type`, `entity_id`, `field_name`.
  - Value diffs: `previous_value_json`, `new_value_json`.
  - Information state: `provenance_state` (`ARTISAN_PROVIDED`, `SOURCE_BACKED`, `AI_SUGGESTED`, `CALCULATED`, `HUMAN_CONFIRMED`, `ADMIN_APPROVED`, `ADMIN_REJECTED`, `FLAGGED`, `SUPERSEDED`, `AUTHORITY_VERIFIED`).
  - Actor & lineage: `actor_user_id`, `actor_role`, `change_reason`, `source_id`, `source_url`, `evidence_reference`, `ai_model_version`, `prompt_version`, `human_confirmation_status`.
  - Cryptographic verification: `event_hash` (SHA-256 canonical hash), `previous_event_hash` (hash chaining), `sequence_number` (monotonic counter).

---

## 3. pgvector Vector Embedding Abstraction

For entities requiring semantic similarity matching (`products.embedding` and `buyer_requirements.embedding`), the platform implements a dialect-aware custom type (`EmbeddingVector(dim=768)`):
- **On PostgreSQL**: Renders as native `VECTOR(768)` via `pgvector.sqlalchemy.Vector`.
- **On SQLite**: Serializes vectors as JSON strings to ensure that local unit tests, CI test pipelines, and developer environments run deterministically without hard dependencies on a local PostgreSQL instance.

---

## 4. Provenance & Sample Data Segregation

Every model inheriting `ProvenanceMixin` (`crafts`, `craft_passports`, `artisan_profiles`, `products`, `buyer_profiles`, `demand_observations`) incorporates:
- `is_sample_or_demo: boolean NOT NULL DEFAULT false`
- `data_provenance_level: string NOT NULL DEFAULT 'VERIFIED_EXTERNAL_SOURCE'`
- `provenance_metadata: JSON NULLABLE` (stores `source_id`, `source_url`, `manifest_id`, and `license`).
