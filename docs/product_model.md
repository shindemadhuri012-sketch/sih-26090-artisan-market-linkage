# Product Data Model & Commercial Parameters

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Overview
The product model represents artisanal handloom and handicraft items created by registered artisans. Unlike standard commodities, handmade crafts feature finite batch production, high craftsmanship value, customizable orders, and strict provenance integrity.

---

## 2. Decoupling Inventory vs Production Capacity

A fundamental architectural principle of SIH 26090 is the strict separation of **finished inventory stock** from **sustainable monthly production capacity**:

1. **`stock_quantity` (Finished Inventory)**:
   - Represents ready-to-ship inventory currently physically available in the artisan's workshop or cooperative godown.
   - Used for immediate retail procurement.
2. **`monthly_production_capacity` (Sustainable Capacity)**:
   - Represents the realistic, sustainable monthly output of the artisan or their family unit/cluster without compromising quality or fair working hours.
   - Crucial for matching institutional buyers, corporate gifting orders, and export consolidators.
3. **`min_order_quantity` (MOQ)**:
   - Minimum batch size acceptable for a procurement contract (defaults to 1 for retail listings).
4. **`lead_time_days`**:
   - Number of business days required to fabricate and dispatch an order when fulfilling from production capacity rather than on-hand stock.

---

## 3. Product Entity Schema (`products`)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Canonical UUID identifier |
| `artisan_id` | UUID | FK -> `artisan_profiles.id`, Not Null | Owner artisan profile |
| `craft_id` | UUID | FK -> `crafts.id`, Not Null | Associated master craft |
| `category_id` | UUID | FK -> `craft_categories.id`, Nullable | Associated master category |
| `sku` | String(64) | Unique, Indexed, Not Null | Formatted unique SKU (e.g. `PRD-A1B2`) |
| `title` | String(255) | Not Null | Artisan product listing title |
| `storytelling_description` | Text | Not Null | Narrative describing motifs, cultural background, loom work |
| `price_inr` | Numeric(12, 2) | Not Null, >= 0 | Selling price declared by artisan in INR |
| `currency` | String(3) | Default "INR" | Currency standard (INR only) |
| `stock_quantity` | Integer | Default 1, >= 0 | Ready-to-ship stock |
| `monthly_production_capacity`| Integer | Default 10, >= 0 | Sustainable monthly production |
| `min_order_quantity` | Integer | Default 1, >= 1 | Minimum order quantity |
| `lead_time_days` | Integer | Default 7, >= 0 | Production turnaround lead time |
| `availability_status` | String(50) | Default "AVAILABLE" | `AVAILABLE`, `MADE_TO_ORDER`, `OUT_OF_STOCK` |
| `region` | String(100) | Nullable | Cluster or regional origin |
| `materials` | JSONB / ARRAY | Default `[]` | List of authentic materials used |
| `primary_color` | String(50) | Nullable | Primary aesthetic color |
| `dimensions` | String(100) | Nullable | Physical dimensions (e.g. "5.5m x 1.15m") |
| `weight_grams` | Integer | Nullable, >= 0 | Net weight in grams |
| `technique` | String(150) | Nullable | Craftsmanship technique |
| `style` | String(100) | Nullable | Style (Traditional, Contemporary, Folk) |
| `tags` | JSONB / ARRAY | Default `[]` | Keyword tags for indexing |
| `is_customizable` | Boolean | Default False | Accepts custom motifs/sizes |
| `status` | String(50) | Default "DRAFT" | `DRAFT`, `PENDING_REVIEW`, `PUBLISHED`, `REJECTED` |
| `provenance_status` | String(50) | Default "ARTISAN_DECLARED" | Provenance tracking level |
| `ai_metadata` | JSONB | Default Contract | Placeholder schema for future Phase 4 AI modules |
| `admin_feedback` | Text | Nullable | Feedback notes from administrative moderation |
| `moderated_by` | UUID | FK -> `users.id`, Nullable | Administrator who adjudicated listing |
| `moderated_at` | DateTime (UTC)| Nullable | Timestamp of moderation review |

---

## 4. Lifecycle State Machine

```
[ New Listing ] ──> DRAFT
                      │
                      │  POST /api/v1/products/{id}/submit
                      ▼
               PENDING_REVIEW
                │          │
 (Admin APPROVE)│          │ (Admin REJECT or REQUEST_CORRECTION)
                ▼          ▼
            PUBLISHED   REJECTED / DRAFT
                │
 (Artisan Edit) │
                ▼
              DRAFT (Re-moderation policy)
```

1. **DRAFT**: Listing is private to the artisan. Editable at any time.
2. **PENDING_REVIEW**: Submitted for administrative moderation. Frozen for editing. Visible in admin queue.
3. **PUBLISHED**: Approved by administrator. Visible in public catalogue (`GET /api/v1/products`).
4. **REJECTED**: Rejected by administrator with detailed feedback. Can be amended and re-submitted.
5. **Re-moderation Policy**: If an artisan edits a currently `PUBLISHED` product, the backend automatically transitions its status back to `DRAFT` to prevent unauthorized post-approval modifications.
