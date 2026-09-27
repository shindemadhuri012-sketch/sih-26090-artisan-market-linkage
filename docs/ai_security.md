# AI Product Studio Security & IDOR Defense

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Authentication & Authorization

All AI Product Studio endpoints are strictly guarded:
- **Transport**: `Authorization: Bearer <access_token>`
- **Role Requirement**: Only users with the `artisan` role can initiate analyses, retrieve staged suggestions, or apply confirmed attributes.
- **Buyer Role**: Requests from buyers return `403 Forbidden`.

---

## 2. Server-Side IDOR Defense

Insecure Direct Object Reference (IDOR) attacks are defended against at the database query level:

```python
# Server-side verification before executing any operation:
product = await db.execute(select(Product).where(Product.id == product_id))
if str(product.artisan_id) != str(current_artisan.id):
    raise HTTPException(status_code=403, detail="Access denied: You do not own this product.")
```

### Protected Operation Boundaries:
1. **Analyze Trigger**: Artisan A cannot submit an image belonging to Artisan B's product listing.
2. **Analysis History**: Artisan A cannot inspect analysis runs or suggestions generated for Artisan B.
3. **Confirmation / Rejection**: Artisan A cannot confirm or reject suggestions for Artisan B's listing.
4. **Media Validation**: Target media asset must be an `IMAGE` and must belong directly to the specified `product_id`.

---

## 3. Credential & Data Protection

1. **Backend-Only AI Secrets**:
   - `GEMINI_API_KEY` is never transmitted to the client, included in HTML/JS bundles, or exposed in OpenAPI responses.
2. **Safe Logging**:
   - Error messages log status codes and sanitised error descriptions without printing API keys or authorization headers.
3. **Audit Trails**:
   - Every significant action generates an immutable record in `audit_logs`:
     - `AI_ANALYSIS_COMPLETED`
     - `AI_ATTRIBUTES_APPLIED_TO_PRODUCT`
     - `AI_ANALYSIS_REJECTED`
