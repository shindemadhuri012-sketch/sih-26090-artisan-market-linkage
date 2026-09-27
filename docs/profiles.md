# SIH 26090: Artisan & Buyer Profile Systems
## Private Onboarding, Profile CRUD, Master Craft Catalog Linkage & Sanitized Public Views

---

## 1. Overview

Artisans and Buyers have asymmetric informational requirements:
- **Artisan Profiles**: Represent rural producers, weaving cooperatives, craft traditions, location identifiers, Ministry of Textiles Pehchan IDs, and monthly production volumes.
- **Buyer Profiles**: Represent retail curation houses, export houses, institutional corporate gifting desks, or government GeM procurement desks.
- **Privacy Boundary**: Private data (personal street addresses, direct phone numbers, bank details) must remain strictly segregated from public or buyer-facing profile views to protect artisan privacy while preserving market discoverability.

---

## 2. Artisan Profile Architecture

### 2.1 Schema Definition
- **Entity**: `artisan_profiles` (mapped via `ArtisanProfile` model).
- **Core Attributes**:
  - `user_id`: Foreign key referencing `users.id` (1-to-1 relationship).
  - `full_name`: Artisan's primary name or master craftsman title.
  - `cooperative_name`: Optional handloom society, SHG, or producer company.
  - `state`, `district`, `pincode`: Geographic cluster origin.
  - `address_line`: Sensitive home/workshop street address (private).
  - `primary_craft_id`: Foreign key referencing master `crafts.id`.
  - `years_of_experience`: Craft heritage depth.
  - `monthly_production_capacity`: Units produceable per month.
  - `pehchan_id`: Ministry of Textiles artisan card identifier.
  - `verification_status`: `PENDING`, `COOPERATIVE_VERIFIED`, `GOVERNMENT_VERIFIED_GI`, `REJECTED`.

### 2.2 Endpoint Specifications

#### `GET /api/v1/artisans/me`
- **Auth**: Bearer token (role `artisan`).
- **Response**: Full private profile including sensitive address lines, capacity, and verification status.

#### `POST /api/v1/artisans/me`
- **Auth**: Bearer token (role `artisan`).
- **Body**: `ArtisanProfileCreate` schema.
- **Validations**: Validates that `primary_craft_id` points to a registered craft in the master catalog. Rejects duplicate creations with `409 Conflict`.

#### `PUT /api/v1/artisans/me`
- **Auth**: Bearer token (role `artisan`).
- **Body**: `ArtisanProfileUpdate` schema (partial patch allowed). Updates capacity, cooperative, or craft details.

#### `GET /api/v1/artisans/{id}/public`
- **Auth**: Public / Anonymous.
- **Response**: Sanitized `ArtisanPublicProfileResponse`.
- **Privacy Filtering**:
  ```json
  {
    "id": "c9801ad2-96d6-481f-84e9-e54aa53bcfda",
    "full_name": "Radha Bai",
    "state": "Madhya Pradesh",
    "district": "Ashoknagar",
    "craft_name": "Chanderi Weaves",
    "years_of_experience": 18,
    "verification_status": "GOVERNMENT_VERIFIED_GI"
  }
  ```
  *Note*: Street address, pincode, phone number, and internal system IDs are completely excluded.

---

## 3. Buyer Profile Architecture

### 3.1 Schema Definition
- **Entity**: `buyer_profiles` (mapped via `BuyerProfile` model).
- **Attributes**:
  - `user_id`: Foreign key referencing `users.id`.
  - `company_name`: Business or institutional trading name.
  - `buyer_type`: `RETAIL_CURATOR`, `INSTITUTIONAL_GIFTING`, `GOVERNMENT_GEM`, `EXPORT_AGGREGATOR`.
  - `gstin`: Indian Goods & Services Tax Identification Number (format validated).
  - `country`, `state`: Operational headquarters.
  - `typical_order_volume`: Procurement scale (e.g., `100-500 units`, `500-2000 units`).
  - `is_verified_buyer`: Flag indicating verified institutional standing.

### 3.2 Endpoint Specifications

#### `GET /api/v1/buyers/me`
- **Auth**: Bearer token (role `buyer`). Returns authenticated buyer's procurement profile.

#### `POST /api/v1/buyers/me`
- **Auth**: Bearer token (role `buyer`). Creates initial procurement profile. Enforces valid `buyer_type` taxonomy.

#### `PUT /api/v1/buyers/me`
- **Auth**: Bearer token (role `buyer`). Updates procurement volume, GSTIN, or company metadata.
