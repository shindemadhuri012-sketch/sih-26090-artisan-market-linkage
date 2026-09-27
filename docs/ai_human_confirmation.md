# AI Human Confirmation Workflow & Staging Layer

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Staging vs. Canonical Separation

A core security and data integrity guarantee is that **AI analysis alone does NOT touch canonical Product records**.

```
[ AI Vision Engine ]
        │
        ▼ (Write to Staging Layer)
[ ai_product_analyses / ai_product_suggestions ]
        │
        │ (Artisan Review: Accept / Edit / Reject)
        ▼
[ Confirmation Endpoint: POST .../confirm ]
   - apply_to_product = True
        │
        ▼ (Write Confirmed Fields Only)
[ Canonical Product: products ]
```

---

## 2. Decision Types & State Machine

For each suggested field, the artisan has three options:

1. **`ACCEPT`**:
   - `status`: Transitions to `HUMAN_CONFIRMED`
   - `human_confirmed`: Set to `True`
   - `confirmed_value`: Equal to `suggested_value`
2. **`EDIT`**:
   - `status`: Transitions to `HUMAN_CONFIRMED`
   - `human_confirmed`: Set to `True`
   - `confirmed_value`: Set to artisan's `custom_value`
   - `suggested_value`: Retained without alteration
3. **`REJECT`**:
   - `status`: Transitions to `REJECTED`
   - `human_confirmed`: Set to `False`
   - `confirmed_value`: Set to `None`
   - The field is **not** written to the canonical product record.

---

## 3. Canonical Product Update Rules

When `apply_to_product = True`:
- Only fields with `status == "HUMAN_CONFIRMED"` are copied to the corresponding columns in `products` (e.g. `title`, `storytelling_description`, `materials`, `technique`, `primary_color`, `dimensions`, `style`, `tags`).
- `Product.ai_metadata` is updated to record:
  - `human_confirmed: true`
  - `model_name`: Provider model used
  - `confirmed_at`: UTC timestamp
  - `confirmed_fields`: Array of attribute names confirmed by the artisan

---

## 4. Re-Moderation Policy

If the target product was already in `PUBLISHED` status:
- Applying confirmed AI attributes automatically reverts `Product.status` back to `DRAFT`.
- The artisan must re-submit the listing for administrative review (`POST /api/v1/products/{id}/submit`).
- **Security Rationale**: Prevents post-moderation bait-and-switch modifications where an approved listing is altered via automated AI tools without administrative oversight.
