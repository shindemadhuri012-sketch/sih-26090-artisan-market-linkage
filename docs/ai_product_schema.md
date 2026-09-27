# AI Product Studio Schemas & Data Contract

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Database Schema Specification

### 1.1 `AIProductAnalysis` (`ai_product_analyses`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID (String 36) | Primary Key | Canonical UUID identifier |
| `product_id` | UUID (String 36) | FK -> `products.id` (CASCADE), Indexed | Linked product listing |
| `media_id` | UUID (String 36) | FK -> `product_media.id` (SET NULL), Indexed | Analyzed image media asset |
| `media_checksum` | String(64) | Nullable | SHA-256 digest of analyzed image |
| `provider` | String(50) | Not Null | Provider name (`google`, `mock`, `none`) |
| `model_name` | String(100) | Not Null | Exact model identifier (e.g. `gemini-1.5-flash`) |
| `model_version` | String(50) | Nullable | Model release version if available |
| `prompt_version` | String(50) | Default `"product_vision_v1"` | Versioned prompt template used |
| `idempotency_key` | String(128) | Indexed, Nullable | SHA-256 hash preventing duplicate analysis runs |
| `status` | String(30) | Indexed, Not Null | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `REJECTED`, `CONFIRMED` |
| `error_message` | Text | Nullable | Safe error explanation on failure |
| `processing_duration_ms`| Integer | Nullable | Wall-clock inference execution duration |
| `input_parameters` | JSON | Default `{}` | Input metadata (media URL, MIME type) |
| `raw_response` | JSON | Nullable | Raw model response payload |
| `created_at` | DateTime (UTC) | Indexed, Not Null | Job initiation timestamp |
| `completed_at` | DateTime (UTC) | Nullable | Job completion timestamp |

### 1.2 `AIProductSuggestion` (`ai_product_suggestions`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID (String 36) | Primary Key | Suggestion record identifier |
| `analysis_id` | UUID (String 36) | FK -> `ai_product_analyses.id` (CASCADE), Indexed | Parent analysis run |
| `product_id` | UUID (String 36) | FK -> `products.id` (CASCADE), Indexed | Target product |
| `field_name` | String(100) | Indexed, Not Null | Catalogue field name (e.g. `title`, `materials`) |
| `suggested_value` | JSON | Nullable | Original AI-inferred value (immutable audit record) |
| `confidence` | Float | Nullable | Calibrated probability or `null`. Never synthetic. |
| `source_type` | String(50) | Default `"AI_SUGGESTED"` | Provenance state (`AI_SUGGESTED`, `HUMAN_CONFIRMED`, `REJECTED`) |
| `human_confirmed` | Boolean | Default `False` | Whether artisan has verified this field |
| `confirmed_value` | JSON | Nullable | Artisan accepted or edited value |
| `status` | String(30) | Indexed, Not Null | `AI_SUGGESTED`, `HUMAN_CONFIRMED`, `REJECTED` |
| `artisan_notes` | Text | Nullable | Notes or edits supplied by the artisan |
| `reviewed_by` | UUID (String 36) | FK -> `users.id` (SET NULL), Nullable | Reviewing artisan user ID |
| `reviewed_at` | DateTime (UTC) | Nullable | Timestamp of human review decision |
| `created_at` | DateTime (UTC) | Not Null | Suggestion creation timestamp |

---

## 2. Pydantic API Schemas

### 2.1 Analysis Trigger Request (`AIAnalyzeRequest`)
```json
{
  "media_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "force_reanalyze": false,
  "provider_override": null
}
```

### 2.2 Field Confirmation Request (`AIConfirmRequest`)
```json
{
  "confirmations": [
    {
      "field_name": "materials",
      "action": "ACCEPT"
    },
    {
      "field_name": "title",
      "action": "EDIT",
      "custom_value": "Handloom Chanderi Cotton Silk Saree",
      "notes": "Refined title with traditional cluster designation"
    },
    {
      "field_name": "technique",
      "action": "REJECT",
      "notes": "Loom was frame loom not pit loom"
    }
  ],
  "apply_to_product": true
}
```
