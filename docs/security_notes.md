# SIH 26090: Security Notes & Hardening Guidelines
## Threat Modeling, OWASP Top 10 Mitigation, Cryptographic Controls & Operational Best Practices

---

## 1. Threat Modeling & OWASP Top 10 Alignments

| OWASP Vulnerability | Risk Scenario in Artisan Platform | Architectural Countermeasure |
|---|---|---|
| **A01: Broken Access Control** | Artisan attempts to edit another artisan's profile or submit someone else's craft passport (IDOR). | RBAC dependencies (`require_roles`) combined with object-level checks (`check_object_ownership`). Strict `current_user.id` binding on `/me` endpoints. |
| **A02: Cryptographic Failures** | Weak password hashing or plaintext session tokens intercepted in transit or data breach. | Argon2id hashing (3 iterations, 64 MiB RAM, 4 threads). SHA-256 one-way hashing for stored refresh tokens. Strict HTTPS in production. |
| **A03: Injection** | SQL injection via phone number or craft search parameters. | Async SQLAlchemy 2.0 parameterized queries exclusively. No raw string SQL interpolation. |
| **A04: Insecure Design** | Replay of stolen refresh tokens across sessions. | Refresh token rotation with token family tracking. Immediate family revocation upon reuse detection. |
| **A05: Security Misconfiguration** | Verbose database tracebacks exposed to public consumers. | Centralized FastAPI error handlers that scrub internal stack traces in non-development modes. |
| **A06: Vulnerable Components** | Outdated or compromised third-party packages. | Strict pip dependency pinning in `pyproject.toml` and lock files. Automated CVE audits. |
| **A07: Identification Failures** | Credential stuffing, brute-forcing passwords or OTP codes. | Rate limiting on OTP challenges (3 max attempts), short token TTLs (15 min access, 5 min OTP). |
| **A08: Software & Data Integrity** | Counterfeit craft certificates or fake GI tags uploaded. | Cryptographic SHA-256 provenance hashes; admin review workflow before `VERIFIED` status is granted. |
| **A09: Logging & Monitoring** | Unauthorized administrative actions taken without accountability. | Immutable `audit_logs` table tracking user ID, IP address, user agent, timestamp, and before/after payloads. |
| **A10: SSRF** | Artisan provides malicious document URL triggering internal network scan. | Document URLs validated strictly against HTTPS protocols and verified cloud storage domains. |

---

## 2. Token Security & Storage

### 2.1 Access Tokens
- Short-lived JWTs (15-minute expiration).
- Include `jti` claim to allow token blacklisting in critical revocation events.
- Signed with `HS256` or `RS256` using high-entropy `SECRET_KEY` (minimum 32 bytes).

### 2.2 Refresh Tokens
- Cryptographically random 48-byte URL-safe strings generated via `secrets.token_urlsafe(48)`.
- Never stored in plaintext: only the SHA-256 hash is recorded in `refresh_token_sessions`.
- Rotated upon every refresh call.
- Replay/reuse detection invalidates the entire `token_family` instantly.

---

## 3. Privacy & PII Protection

To protect rural artisans against predatory solicitation, harassment, or financial exploitation:
1. **Public Profile Sanitization**: `GET /api/v1/artisans/{id}/public` omits phone numbers, street addresses, pincodes, and Pehchan IDs.
2. **Passport QR Code Scan**: `GET /api/v1/public/passports/{public_id}` exposes only public craft heritage, GI status, and verified artisan title.
3. **Internal Log Hygiene**: Passwords, OTP codes, and refresh tokens are strictly omitted from standard logger statements (`telemetry.py` and `audit_service.py`).

---

## 4. Production Deployment Hardening Checklist

When deploying to staging or production:
- [ ] Set `APP_ENV=production` and `DEBUG=False` in environment configuration.
- [ ] Configure `SECRET_KEY` via secure secret manager (e.g. AWS Secrets Manager or HashiCorp Vault), never hardcoded in source control.
- [ ] Set secure cookie flags: `HttpOnly=True`, `Secure=True`, `SameSite=Lax`.
- [ ] Configure PostgreSQL with SSL encryption enforced (`sslmode=require`).
- [ ] Configure CORS with explicit production frontend origins (`ALLOWED_HOSTS`).
- [ ] Enable reverse-proxy rate limiting (e.g. Nginx or Cloudflare) for `/api/v1/auth/otp/*` and `/api/v1/auth/login`.
