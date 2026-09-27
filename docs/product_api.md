# Product & Catalogue API Reference

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Authentication & Security
- **Bearer Token**: All artisan and admin endpoints require an `Authorization: Bearer <access_token>` header.
- **IDOR Defense**: All operations targeting artisan-owned products (`PUT`, `DELETE`, `submit`, `media`) verify that the product's `artisan_id` strictly matches the authenticated user's artisan profile. Unauthorized operations return `403 Forbidden`.
- **Public API Privacy**: Public catalogue endpoints (`GET /api/v1/products`, `GET /api/v1/products/{id}`) strictly withhold private artisan PII (phone number, Pehchan ID, email, street address).

---

## 2. Artisan Product Management Endpoints

### 2.1 Create Product Listing
- **Endpoint**: `POST /api/v1/products`
- **Role**: `artisan`
- **Status Code**: `201 Created`
- **Request Body (`ProductCreate`)**:
```json
{
  "craft_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "category_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
  "title": "Chanderi Handloom Cotton Silk Saree",
  "storytelling_description": "Hand-woven on a traditional pit loom using mulberry silk and gold zari motifs.",
  "price_inr": 4850.00,
  "currency": "INR",
  "stock_quantity": 4,
  "monthly_production_capacity": 15,
  "min_order_quantity": 1,
  "lead_time_days": 12,
  "availability_status": "AVAILABLE",
  "region": "Chanderi, Madhya Pradesh",
  "materials": ["Mulberry Silk", "Cotton Yarn", "Zari"],
  "primary_color": "Maroon",
  "dimensions": "5.5m x 1.15m",
  "weight_grams": 450,
  "technique": "Pit Loom Extra-Weft Zari Weave",
  "style": "Traditional Heritage",
  "tags": ["saree", "chanderi", "handloom", "festive"],
  "is_customizable": true
}
```

### 2.2 List My Products
- **Endpoint**: `GET /api/v1/artisans/me/products`
- **Role**: `artisan`
- **Query Params**: `page` (default 1), `page_size` (default 20)
- **Response**: Array of `ProductResponse` objects across all lifecycle states.

### 2.3 Update Product Listing
- **Endpoint**: `PUT /api/v1/products/{product_id}`
- **Role**: `artisan` (Owner only; IDOR protected)
- **Status Code**: `200 OK`
- **Re-moderation Rule**: Modifying a published product resets its status to `DRAFT`.

### 2.4 Delete Product Listing
- **Endpoint**: `DELETE /api/v1/products/{product_id}`
- **Role**: `artisan` (Owner only) or `admin`
- **Status Code**: `200 OK`

### 2.5 Submit for Moderation
- **Endpoint**: `POST /api/v1/products/{product_id}/submit`
- **Role**: `artisan` (Owner only)
- **Status Transition**: `DRAFT` or `REJECTED` -> `PENDING_REVIEW`

---

## 3. Product Media Endpoints

### 3.1 Attach Media Asset Metadata
- **Endpoint**: `POST /api/v1/products/{product_id}/media`
- **Role**: `artisan` (Owner only; IDOR protected)
- **Status Code**: `201 Created`
- **Validation**:
  - `mime_type`: Only `image/jpeg`, `image/png`, `image/webp`, `audio/mpeg`, `application/pdf`
  - `file_size_bytes`: Maximum 10MB (10,485,760 bytes)
  - `original_filename`: Path-traversal sanitization (no `..` or path separators)
- **Request Body**:
```json
{
  "media_type": "IMAGE",
  "url": "https://storage.artisanmarket.gov.in/products/chanderi_1.webp",
  "thumbnail_url": "https://storage.artisanmarket.gov.in/products/chanderi_1_thumb.webp",
  "original_filename": "chanderi_front.webp",
  "file_size_bytes": 450000,
  "mime_type": "image/webp",
  "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "width": 1920,
  "height": 1080,
  "sort_order": 0,
  "alt_text": "Close-up of golden zari pallu on Chanderi silk",
  "is_primary": true
}
```

### 3.2 Delete Media Asset
- **Endpoint**: `DELETE /api/v1/products/{product_id}/media/{media_id}`
- **Role**: `artisan` (Owner only; IDOR protected)
- **Status Code**: `200 OK`

---

## 4. Public Catalogue Endpoints

### 4.1 Browse and Filter Catalogue
- **Endpoint**: `GET /api/v1/products`
- **Auth**: None (Public)
- **Status**: Strictly returns products with `status == "PUBLISHED"`
- **Query Parameters**:
  - `query`: Text search in title, narrative, technique
  - `craft_id`: Master craft UUID filter
  - `category_id`: Category UUID filter
  - `region`: Origin state or cluster filter
  - `min_price`: Minimum price in INR
  - `max_price`: Maximum price in INR
  - `min_capacity`: Minimum monthly production capacity
  - `max_moq`: Maximum acceptable MOQ
  - `page`: Page number (default 1)
  - `page_size`: Items per page (default 20, max 100)

### 4.2 Public Product Detail
- **Endpoint**: `GET /api/v1/products/{product_id}`
- **Auth**: None (Public)
- **Sanitization**: Excludes artisan phone number, Pehchan ID, bank accounts, and private street address. Returns sanitized artisan name, district, state, craft heritage, and GI tags.

---

## 5. Administrative Moderation Endpoints

### 5.1 List Pending Queue
- **Endpoint**: `GET /api/v1/products/admin/pending`
- **Role**: `admin`
- **Response**: Array of `ProductResponse` objects in `PENDING_REVIEW` status.

### 5.2 Review Product
- **Endpoint**: `POST /api/v1/products/admin/{product_id}/review`
- **Role**: `admin`
- **Request Body**:
```json
{
  "decision": "APPROVE",
  "admin_notes": "Meets authentic GI Chanderi specifications.",
  "rejection_reason": null
}
```
- **Decisions**:
  - `APPROVE`: Transitions to `PUBLISHED` (and `GOVERNMENT_GI_CONFIRMED` if craft has GI)
  - `REJECT`: Transitions to `REJECTED`
  - `REQUEST_CORRECTION`: Transitions to `DRAFT`
