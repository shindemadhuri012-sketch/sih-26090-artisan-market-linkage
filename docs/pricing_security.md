# Pricing Security & IDOR Defense

SIH 26090 — Security Architecture & Data Protection

---

## 1. Authentication & Role Boundaries

All pricing endpoints require authenticated JSON Web Tokens (JWT) signed with HMAC-SHA256:
- **Artisan Role Required**: Cost updates, price analysis executions, and price confirmation actions strictly require the `artisan` role (`require_roles(["artisan"])`). Buyers, unauthenticated guests, and unverified users receive HTTP 401 or HTTP 403.
- **Admin Role Required**: Market price evidence ingestion is restricted to administrators (`require_roles(["admin"])`).

---

## 2. Server-Side IDOR Defense

To prevent Insecure Direct Object References (IDOR):
- Every pricing endpoint validates product ownership using `verify_artisan_product_ownership(db, product_id, current_user.id)`:
  ```python
  if product.artisan_id != artisan.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Forbidden: You do not own this product listing."
      )
  ```
- Cross-artisan read, modification, analysis trigger, and confirmation attempts are completely blocked and tested via automated test suites (`tests/test_pricing_auth_idor.py`).

---

## 3. Injection Prevention & Financial Integrity

- **No Dynamic Formula Execution**: Formula expressions are hardcoded in `FairPriceEngine` (`FAIR_PRICE_ENGINE_V1`). The frontend cannot submit arbitrary formulas or executable code to the backend.
- **Strict Pydantic Validation**:
  - Non-negative validation on costs and prices (`ge=0`).
  - Strict batch quantity validation (`ge=1`).
  - Allowed labor method enumeration (`HOURLY_RATE`, `TOTAL_STATED`).
  - Allowed allocation basis enumeration.
- **Audit Logging**: All cost updates, price analysis runs, and price confirmation actions are recorded in `audit_logs` with timestamps, actor IDs, and before/after payloads.
