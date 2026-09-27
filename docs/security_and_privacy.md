# SIH 26090: SECURITY, PRIVACY & DEFENSIVE CONTROLS
## Production Security Architecture, Threat Mitigation & Data Privacy Controls

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. Authentication & Session Security

### 1.1 Password Hashing (Argon2id)
Passwords are encrypted using Argon2id in accordance with RFC 9106 guidelines:
- Memory Cost: $64\text{ MiB}$ (`65536` KiB)
- Time Cost: $3$ iterations
- Parallelism: $4$ threads
- Salt Length: $16$ bytes
- Hash Length: $32$ bytes

### 1.2 Short-Lived Access Tokens & Replay Defense
- Format: JSON Web Tokens (JWT) signed via HMAC-SHA256 (`HS256`).
- Expiry: 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=15`).
- Replay Resistance: Each token embeds a cryptographically random `jti` (JWT ID, 16 hex bytes) alongside `sub` and `role`.

### 1.3 Refresh Token Family Rotation & Reuse Detection
- Refresh tokens are cryptographically strong random strings (48 bytes URL-safe).
- Stored as SHA-256 digests in the `refresh_token_sessions` table.
- **Token Family Defense**: Every login initiates a `token_family`. When a token is refreshed, the existing session is revoked and a child token is issued.
- **Theft Detection**: If an expired or already-rotated token is presented, the system identifies token theft, issues a `TOKEN_REUSE_DETECTED` audit alert, and revokes **all** sessions across the entire token family.

---

## 2. Authorization, RBAC & IDOR Protections

### 2.1 Role-Based Access Control (RBAC)
FastAPI dependency guards strictly enforce role segregation:
- `require_roles(["artisan"])`: Protects product creation, pricing runs, and RFQ negotiation endpoints.
- `require_roles(["buyer"])`: Protects requirement creation, matching queries, and RFQ submission endpoints.
- `get_current_active_admin`: Protects moderation queues, verification decisions, governance flags, and system telemetry. Non-admin access receives `HTTP 403 Forbidden`.

### 2.2 Insecure Direct Object Reference (IDOR) Defense
Object-level ownership guards (`check_object_ownership`) verify that the authenticated user owns the accessed record:
- An artisan cannot mutate or inspect another artisan's draft products or private media.
- A buyer cannot access or tamper with RFQs between other organizations and artisans.

---

## 3. Network & Transport Security

### 3.1 Defensive Security Headers
Every API response injects defensive headers via HTTP middleware:
- `X-Content-Type-Options: nosniff`: Prevents MIME-sniffing attacks.
- `X-Frame-Options: DENY`: Defends against clickjacking.
- `X-XSS-Protection: 1; mode=block`: Enables browser cross-site scripting filters.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts referrer leakage.
- `Content-Security-Policy`: Restricts script and resource loading to authorized origins.
- `Strict-Transport-Security`: Enforces HTTPS (`max-age=31536000; includeSubDomains`) in production.

### 3.2 Request Sizing & DOS Prevention
- Requests exceeding 15MB (`MAX_REQUEST_BODY_SIZE_BYTES`) are terminated at the gateway with `HTTP 413 Request Entity Too Large`.

### 3.3 Production Error Sanitization
- Global exception handler catches all unhandled exceptions.
- In production (`DEBUG=False`), internal database traces, SQL queries, and code line numbers are masked. The client receives a generic JSON error containing an audited `correlation_id`.

---

## 4. File & Media Upload Security

Media uploads ([`backend/app/schemas/product.py`](file:///e:/backend/app/schemas/product.py)) enforce strict defensive constraints:
1. **MIME Type Allowlist**: Strictly permits `image/jpeg`, `image/png`, `image/webp`, `audio/mpeg`, `audio/wav`, `application/pdf`. Executable or script files (`.exe`, `.sh`, `.js`, `.py`) are rejected.
2. **File Size Limit**: Maximum $10\text{ MB}$ per asset.
3. **Path Traversal Defense**: Regex rejects filenames containing `..`, `/`, `\`, or `:`.
4. **Presigned Architecture**: Uploads go directly to S3/MinIO via presigned URLs, keeping application server bandwidth clear and credentials private.

---

## 5. Public PII Sanitization & Data Privacy

- **Public Provenance & Catalogue Feeds**: Redacts telephone numbers, email addresses, personal residence street addresses, and full tax identifiers. Only registered business names and craft districts are published.
- **Offline Storage Privacy**: The client-side PWA IndexedDB database stores only product drafts, craft references, and pending mutation items. Government identity documents (Pehchan cards, Aadhaar documents) are **never** cached in browser storage.
- **Logout Purge**: Logging out immediately purges local IndexedDB databases and session storage.
