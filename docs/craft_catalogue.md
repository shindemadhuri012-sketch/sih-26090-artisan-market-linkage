# Craft Catalogue & Master Taxonomy

SIH 26090: Artisan Market Linkage & Smart Seller Matching

## 1. Overview
The Craft Catalogue establishes the canonical repository of Indian traditional crafts, handlooms, and folk art forms. It provides structured categorization, Geographical Indication (GI) registry linkage, cluster/state geographic associations, and many-to-many linkages to registered artisan profiles.

---

## 2. Master Category Hierarchy
Categories are modeled as an extensible self-referential tree structure allowing deep hierarchical categorization (e.g., `Textiles & Weaving` -> `Handloom Brocades` -> `Extra-Weft Zari Motifs`).

### Entity: `CraftCategory` (`craft_categories`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Canonical UUIDv4 identifier |
| `name` | String(100) | Unique, Not Null | Human-readable craft category name |
| `description` | Text | Nullable | Detailed scope of the category |
| `parent_id` | UUID | FK -> `craft_categories.id`, Nullable | Parent category UUID for hierarchical trees |
| `created_at` | DateTime (UTC) | Not Null | Creation timestamp |

---

## 3. Master Craft Entity
Each registered craft corresponds to an authentic craft tradition recognized under state/national handloom registries or the official Geographical Indications Registry (CGPDTM).

### Entity: `Craft` (`crafts`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Canonical craft UUID |
| `category_id` | UUID | FK -> `craft_categories.id` | Associated primary category |
| `name` | String(150) | Unique, Not Null | Official craft name (e.g. "Chanderi Silk Saree") |
| `normalized_name` | String(150) | Indexed, Not Null | Lowercased, stripped name for deterministic search |
| `gi_tag_number` | String(50) | Unique, Nullable | Official GI registration tag (e.g. "GI-007") |
| `has_gi_tag` | Boolean | Default False | Whether this craft possesses official GI status |
| `origin_state` | String(100) | Indexed, Not Null | Primary Indian origin state |
| `origin_district` | String(100) | Nullable | Primary cluster district |
| `region` | String(100) | Nullable | Geographic zone (e.g. "Bundelkhand", "Northern India") |
| `cultural_heritage_description` | Text | Nullable | Verified cultural narrative and historical origins |
| `traditional_technique` | String(255) | Nullable | Standard traditional technique (e.g. "Pit Loom Weaving") |
| `traditional_raw_materials` | JSONB / ARRAY | Default `[]` | List of authentic materials (e.g. `["Mulberry Silk", "Cotton"]`) |
| `is_active` | Boolean | Default True | Administrative active listing flag |

---

## 4. Artisan-Craft Many-to-Many Association
Artisans can master multiple craft traditions across different skill tiers and years of experience. This relationship is modeled via the `artisan_crafts` join table.

### Entity: `ArtisanCraft` (`artisan_crafts`)
| Field | Type | Description |
|---|---|---|
| `id` | UUID | Association record identifier |
| `artisan_id` | UUID (FK) | Link to `artisan_profiles.id` |
| `craft_id` | UUID (FK) | Link to `crafts.id` |
| `skill_level` | String(50) | `APPRENTICE`, `JOURNEYMAN`, `MASTER_CRAFTSMAN`, `NATIONAL_AWARD_WINNER` |
| `years_of_experience` | Integer | Total years actively practicing this craft |
| `is_primary` | Boolean | Artisan's signature craft specialty |
| `technique` | String(200) | Specific specialized sub-technique mastered |
| `evidence_url` | String(500) | Link to certificate, master craftsman award, or guild attestation |
| `status` | String(50) | `ACTIVE`, `SUSPENDED` |

Unique Constraint: `(artisan_id, craft_id)` ensures no duplicate associations.

---

## 5. Master Catalogue APIs
1. **Public Tree**: `GET /api/v1/craft-categories` returns complete category hierarchy.
2. **Deterministic Directory Search**: `GET /api/v1/crafts` supports:
   - `query`: Case-insensitive substring match against `normalized_name`
   - `state`: Origin state filtering
   - `has_gi_tag`: Boolean filter for GI-certified crafts
   - `category_id`: Category UUID filter
   - Pagination (`page`, `page_size`, `total_pages`)
3. **Master Craft Admin Endpoints**:
   - `POST /api/v1/craft-categories` (Admin only)
   - `POST /api/v1/crafts` (Admin only)
   - `PUT /api/v1/crafts/{id}` (Admin only)
