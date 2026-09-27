# Product Media Security & Storage Architecture

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Overview
Artisan product digitization requires high-fidelity media assets: high-resolution craft photographs, audio voice notes in local dialects, and official GI certificates or quality inspection documents.

---

## 2. Media Schema (`product_media`)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Unique media asset identifier |
| `product_id` | UUID | FK -> `products.id`, Not Null | Linked product listing |
| `media_type` | String(50) | Not Null | `IMAGE`, `AUDIO_VOICE_NOTE`, `DOCUMENT` |
| `url` | String(500) | Not Null | Public HTTPS storage URL |
| `thumbnail_url` | String(500) | Nullable | Scaled preview thumbnail URL |
| `storage_key` | String(255) | Nullable | Object storage bucket path (e.g. S3/MinIO) |
| `original_filename` | String(255) | Not Null | Uploaded filename |
| `file_size_bytes` | Integer | Not Null, <= 10MB | File size in bytes |
| `mime_type` | String(50) | Not Null | Validated MIME type |
| `checksum_sha256` | String(64) | Nullable | SHA-256 hash for asset integrity |
| `width` | Integer | Nullable | Image width in pixels |
| `height` | Integer | Nullable | Image height in pixels |
| `sort_order` | Integer | Default 0 | Display sequence index |
| `alt_text` | String(255) | Nullable | Accessible screen-reader description |
| `is_primary` | Boolean | Default False | Cover asset for catalogue cards |
| `created_at` | DateTime (UTC) | Not Null | Upload timestamp |

---

## 3. Media Security & Validation Rules

1. **MIME Type Whitelisting**:
   - Allowed: `image/jpeg`, `image/png`, `image/webp`, `audio/mpeg`, `audio/wav`, `audio/ogg`, `application/pdf`.
   - Disallowed: Any executable format (`application/x-executable`, `application/x-msdos-program`), scripts (`text/html`, `application/javascript`), or shell binaries.
   - Rejection status: `422 Unprocessable Entity`.
2. **File Size Enforcement**:
   - Maximum size allowed: `10,485,760` bytes (10 Megabytes).
   - Enforced by Pydantic validator (`le=10485760`).
3. **Filename & Path Traversal Sanitization**:
   - File names are validated against regex `[\/\\:\*\?\"<>\|]` and forbidden substring `..`.
   - Prevents directory traversal attacks (`../../etc/passwd`).
4. **Server-Side Ownership (IDOR Defense)**:
   - When an artisan requests `POST /api/v1/products/{id}/media` or `DELETE /api/v1/products/{id}/media/{media_id}`, the backend joins `Product` with `ArtisanProfile` to verify that `current_user.id == artisan.user_id`.
   - Cross-artisan tampering returns `403 Forbidden`.
