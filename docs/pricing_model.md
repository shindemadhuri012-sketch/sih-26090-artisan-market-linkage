# Pricing Domain Models & Database Schema

SIH 26090 — Phase 5 Domain Architecture

---

## 1. Entity Relationship Overview

The pricing subsystem links craft products, cost breakdowns, market observations, and historical analyses:

```
+---------------------+         1 : 1         +---------------------------+
|       Product       | --------------------> |   ProductCostBreakdown    |
+---------------------+                       +---------------------------+
          | 1                                               | 1
          |                                                 |
          | 1 : N                                           | 1 : N
          v                                                 v
+---------------------+                       +---------------------------+
|    PriceAnalysis    | <-------------------- |       PriceAnalysis       |
+---------------------+                       +---------------------------+

+---------------------+         1 : N         +---------------------------+
|        Craft        | --------------------> |  MarketPriceObservation   |
+---------------------+                       +---------------------------+
```

---

## 2. Table Schemas

### `product_cost_breakdowns`
Stores the structured cost parameters provided by the artisan:
- `id` (UUID, PK)
- `product_id` (FK `products.id`, UNIQUE, CASCADE)
- `artisan_id` (FK `artisan_profiles.id`, CASCADE)
- `materials` (JSON list of items: name, quantity, unit, unit_cost_inr, total_cost_inr, source_type, source_reference)
- `total_material_cost` (Numeric(12, 2))
- `labor_calculation_method` (String: `HOURLY_RATE` or `TOTAL_STATED`)
- `labor_hours` (Numeric(6, 2), nullable)
- `hourly_labor_rate` (Numeric(8, 2), nullable)
- `total_labor_cost` (Numeric(12, 2))
- `packaging_cost` (Numeric(10, 2))
- `transport_cost` (Numeric(10, 2))
- `overhead_cost` (Numeric(10, 2))
- `overhead_allocation_basis` (String: `PER_PRODUCT`, `PER_BATCH`, `MONTHLY_ALLOCATION`, `DOCUMENTED_PERCENTAGE`)
- `other_costs` (Numeric(10, 2))
- `other_costs_description` (Text, nullable)
- `batch_quantity` (Integer, default 1)
- `currency` (String(3), default `INR`)
- `current_selling_price` (Numeric(10, 2), nullable)
- `desired_margin_percentage` (Numeric(5, 2), default 25.00)
- `total_production_cost` (Numeric(12, 2))
- `cost_baseline_unit_cost` (Numeric(12, 2))
- `cost_baseline_recommended_price` (Numeric(12, 2))
- `provenance_status` (String(40), default `ARTISAN_PROVIDED`)
- `created_at`, `updated_at` (DateTime with timezone)

### `market_price_observations`
Stores source-backed, documented retail/wholesale prices:
- `id` (UUID, PK)
- `craft_id` (FK `crafts.id`, CASCADE)
- `craft_category_id` (FK `craft_categories.id`, SET NULL, nullable)
- `product_title` (String(255), nullable)
- `observed_price` (Numeric(10, 2), non-negative)
- `currency` (String(3), default `INR`)
- `source_name` (String(255))
- `source_url` (Text, nullable)
- `source_type` (String(50): `GOVERNMENT`, `OFFICIAL_REGISTRY`, `OFFICIAL_MARKETPLACE`, `VERIFIED_ARTISAN`, `AUTHORIZED_SOURCE`, `OTHER_DOCUMENTED_SOURCE`)
- `geography_state` (String(100), nullable)
- `region` (String(100), nullable)
- `observation_date` (DateTime with timezone)
- `retrieval_timestamp` (DateTime with timezone)
- `original_source_id` (String(100), nullable)
- `license_or_usage_info` (Text, nullable)
- `attributes_json` (JSON)
- `comparability_tags` (JSON list)
- `evidence_quality_status` (String(30): `HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT`)
- `verification_status` (String(30): `DOCUMENTED`, `VERIFIED`, `PENDING_REVIEW`, `REJECTED`)
- `data_provenance_level` (String(50), default `SOURCE_BACKED`)
- `is_sample_or_demo` (Boolean, default False)
- `ingestion_batch_id` (String(64), nullable)
- `created_at` (DateTime with timezone)

### `price_analyses` (Upgraded in Phase 5)
Append-only historical record of every executed pricing analysis:
- `id` (UUID, PK)
- `product_id` (FK `products.id`, CASCADE)
- `artisan_id` (FK `artisan_profiles.id`, CASCADE, nullable)
- `cost_breakdown_id` (FK `product_cost_breakdowns.id`, SET NULL, nullable)
- `engine_version` (String(50), default `FAIR_PRICE_ENGINE_V1`)
- `currency` (String(3), default `INR`)
- `raw_material_cost` (Numeric(10, 2))
- `labor_hours` (Numeric(6, 2))
- `skill_level_hourly_rate` (Numeric(8, 2))
- `consumables_overhead_cost` (Numeric(10, 2))
- `packaging_logistics_cost` (Numeric(10, 2))
- `calculated_total_cost` (Numeric(10, 2))
- `fair_margin_percentage` (Numeric(5, 2))
- `recommended_floor_price` (Numeric(10, 2))
- `recommended_fair_retail_price` (Numeric(10, 2))
- `fair_price_min` (Numeric(10, 2), nullable)
- `fair_price_max` (Numeric(10, 2), nullable)
- `fair_price_recommended` (Numeric(10, 2), nullable)
- `evidence_status` (String(50): `SUFFICIENT_MARKET_EVIDENCE`, `INSUFFICIENT_MARKET_EVIDENCE`, `COST_ONLY_BASELINE`, `NOT_COMPARABLE`)
- `market_sample_size` (Integer, default 0)
- `market_median_price` (Numeric(10, 2), nullable)
- `market_min_price` (Numeric(10, 2), nullable)
- `market_max_price` (Numeric(10, 2), nullable)
- `market_iqr_low` (Numeric(10, 2), nullable)
- `market_iqr_high` (Numeric(10, 2), nullable)
- `input_snapshot_json` (JSON)
- `comparable_observations_json` (JSON)
- `explanation_steps` (JSON)
- `limitations_notes` (JSON)
- `provenance_state` (String(50), default `CALCULATED`)
- `is_confirmed_by_artisan` (Boolean, default False)
- `confirmed_price_inr` (Numeric(10, 2), nullable)
- `artisan_notes` (Text, nullable)
- `created_at`, `updated_at` (DateTime with timezone)
