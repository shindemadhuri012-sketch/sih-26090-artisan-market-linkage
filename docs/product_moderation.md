# Administrative Product Moderation & Compliance Workflow

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Moderation Purpose
To preserve platform authenticity, prevent fraudulent listings, protect buyers, and ensure genuine compliance with Geographical Indications (GI), all artisanal product listings must pass administrative moderation before appearing in the public catalogue.

---

## 2. Moderation Workflow & State Transitions

```
[ Artisan: DRAFT ] 
        │
        │ POST /api/v1/products/{id}/submit
        ▼
[ PENDING_REVIEW ] ──(Admin Queue: GET /api/v1/products/admin/pending)
        │
        ├── Decision: APPROVE
        │     └──> Product Status: PUBLISHED
        │     └──> If craft has GI: provenance_status = GOVERNMENT_GI_CONFIRMED
        │     └──> Listing immediately visible on Public Catalogue
        │
        ├── Decision: REJECT
        │     └──> Product Status: REJECTED
        │     └──> Admin feedback recorded in `admin_feedback`
        │     └──> Artisan notified to review rejection reasons
        │
        └── Decision: REQUEST_CORRECTION
              └──> Product Status: DRAFT
              └──> Admin guidance recorded in `admin_feedback`
              └──> Artisan edits listing and re-submits
```

---

## 3. Re-Moderation Policy

If an artisan modifies a product that is already in `PUBLISHED` status:
1. The backend automatically resets the product's status to `DRAFT`.
2. The artisan must re-submit the listing via `POST /api/v1/products/{id}/submit`.
3. An administrator must re-approve the listing before it reappears on the public catalogue.
4. **Security Rationale**: Prevents "bait-and-switch" attacks where a seller receives approval for an authentic GI saree and subsequently modifies the description or material composition to mass-produced polyester.

---

## 4. Comprehensive Audit Trail

Every lifecycle event records an immutable entry in the `audit_logs` table via `record_audit_event`:
- `PRODUCT_CREATED`: When artisan saves initial draft.
- `PRODUCT_UPDATED`: When artisan amends details.
- `PRODUCT_DELETED`: When artisan or admin deletes listing.
- `PRODUCT_SUBMITTED_FOR_REVIEW`: When artisan submits product.
- `PRODUCT_MODERATION_APPROVE`: Administrator approval with actor UUID and timestamp.
- `PRODUCT_MODERATION_REJECT`: Administrator rejection with reason.
- `PRODUCT_MODERATION_REQUEST_CORRECTION`: Administrator correction request with notes.
- `PRODUCT_MEDIA_ADDED` / `PRODUCT_MEDIA_DELETED`: Media attachment audit.
