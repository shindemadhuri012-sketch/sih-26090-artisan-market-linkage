# SIH 26090: Phase 6 Engineering Plan
## Buyer–Artisan Semantic Matching Engine & RFQ Linkage Architecture

**Phase**: Phase 6 — Core Market Linkage  
**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Planning Status**: COMPLETE — PENDING IMPLEMENTATION APPROVAL  
**Current Milestone State**: Phase 5 Complete & Verified (82/82 Tests Passing)  

---

## 1. Current-State Assessment

### 1.1 Existing Foundations (Phases 0–5)
- **Phase 0 (Architecture & Strategy)**: Full domain specifications, AI honesty charter, and architectural blueprints (`docs/`).
- **Phase 1 (Data Layer & Ingestion)**: 23 initial models, Alembic migrations, verified GI Registry and ODOP district data (`data/processed/`).
- **Phase 2 (Identity, RBAC & Craft Passport)**: JWT authentication, artisan/buyer profiles, digital Craft Passport with verification badges (35 tests).
- **Phase 3 (Product & Catalogue)**: Hierarchical craft categories, artisan-craft associations, decoupled commercial parameters (stock, capacity, MOQ, lead time), media upload with SHA-256 integrity (50 tests).
- **Phase 4 (AI Product Studio)**: Multimodal vision inference, isolated staging (`ai_product_analyses`, `ai_product_suggestions`), uncalibrated confidence scores, mandatory human confirmation (68 tests).
- **Phase 5 (Fair Price Intelligence)**: Deterministic pricing engine (`FAIR_PRICE_ENGINE_V1`), Python `Decimal` arithmetic, $N < 3$ sparse data rule, living wage floor price guarantee, traceable step-by-step explanations (82 tests).

### 1.2 Current Vector & Matching Assets
- `backend/app/models/custom_types.py`: Defines dialect-aware `EmbeddingVector(dim=768)` (PostgreSQL `pgvector.sqlalchemy.Vector` with fallback SQLite JSON serialization).
- Column `embedding` is already present on `products` and `buyer_requirements`.
- Entities `BuyerRequirement`, `Match`, and `MatchExplanation` exist as basic skeletons in `backend/app/models/buyer.py`.
- Entity `Enquiry` exists in `backend/app/models/market.py`.
- **Gaps to Address in Phase 6**:
  1. No embedding provider or generation pipeline exists (`ai/embeddings/` is currently a placeholder).
  2. `BuyerRequirement` lacks detailed procurement brief fields (desired techniques, materials, packaging, customization, destination).
  3. No Requirement Understanding layer exists to parse natural language RFQs into staged suggestions.
  4. `Match` does not currently reference `product_id` (only `artisan_id`), preventing direct catalogue item linkage alongside artisan capacity matching.
  5. The matching engine (`ai/matching/`) is unbuilt; no two-stage retrieval, hybrid scoring, or explanation synthesis exists.
  6. No API endpoints exist for buyer requirements, requirement understanding, match execution, or RFQ management.
  7. No frontend interfaces exist for buyers to post RFQs, review matches, or for artisans to manage incoming RFQs.

---

## 2. Existing Entities Reused

Phase 6 maximizes reuse of existing models to maintain architectural continuity:

| Existing Entity | Location | Phase 6 Role |
|---|---|---|
| `BuyerProfile` | `backend/app/models/buyer.py` | Buyer identity, buyer type (`RETAIL_CURATOR`, `INSTITUTIONAL_GIFTING`, `GOVERNMENT_GEM`, `EXPORT_AGGREGATOR`), company name, and verification tier. |
| `Product` | `backend/app/models/product.py` | Primary candidate pool for direct catalogue matching (`title`, `storytelling_description`, `price_inr`, `stock_quantity`, `monthly_production_capacity`, `min_order_quantity`, `lead_time_days`, `materials`, `technique`, `style`, `tags`, `is_customizable`, `embedding`, `status`). |
| `ProductAttributes` | `backend/app/models/product.py` | Technical specifications for deep structured attribute matching (`primary_material`, `technique`, `dimensions_cm`, `weight_grams`, `colors`). |
| `ArtisanProfile` | `backend/app/models/artisan.py` | Artisan-level candidate pool for capacity matching (`state`, `district`, `years_of_experience`, `monthly_production_capacity`, `pehchan_id`, `verification_status`). |
| `ArtisanCraft` | `backend/app/models/artisan.py` | Verified skill levels (`MASTER_CRAFTSMAN`, `SKILLED`), techniques, and craft associations. |
| `Craft` | `backend/app/models/craft.py` | Official GI tag linkage, origin district/state, craft classification. |
| `CraftCategory` | `backend/app/models/craft.py` | Hierarchical taxonomy evaluation (`parent_id` category tree). |
| `User` | `backend/app/models/auth.py` | Authentication, JWT claims, role-based authorization (`buyer`, `artisan`, `admin`). |
| `AuditLog` | `backend/app/models/auth.py` | Immutable security audit logging for RFQ submissions, match runs, and commercial negotiation state changes. |

---

## 3. New Entities Required

To maintain the strict separation between AI staging and canonical data, Phase 6 introduces one new staging entity and refines existing entities:

### 3.1 New Staging Entity: `RequirementUnderstanding` (`requirement_understandings`)
Following the proven Phase 4 AI Product Studio staging pattern:
- **Purpose**: Holds staged AI-extracted structured attributes from a buyer's unstructured natural-language brief (`raw_text`).
- **Isolation Guarantee**: AI extraction runs write ONLY to `requirement_understandings`. They **never** silently overwrite canonical `BuyerRequirement` fields.
- **Fields**:
  - `id`: UUID (String 36, PK)
  - `requirement_id`: Foreign Key to `buyer_requirements.id` (CASCADE)
  - `buyer_id`: Foreign Key to `buyer_profiles.id` (CASCADE)
  - `raw_input_text`: Text
  - `extracted_fields_json`: JSON (extracted craft, materials, techniques, quantity, budget, deadline, customization)
  - `confidence_scores_json`: JSON (uncalibrated confidence or null)
  - `provider`: String(50) (e.g. `gemini`, `mock`)
  - `model_name`: String(100)
  - `prompt_version`: String(50) (e.g. `rfq_understanding_v1`)
  - `status`: String(30) (`SUGGESTED`, `CONFIRMED`, `REJECTED`)
  - `is_confirmed_by_buyer`: Boolean (default False)
  - `confirmed_fields_json`: JSON (nullable)
  - `confirmed_at`: DateTime (nullable)
  - `created_at`, `updated_at`: DateTime

---

## 4. Database Schema Changes & Alembic Migration

### 4.1 Modifications to Existing Entities
1. **`BuyerRequirement` (`buyer_requirements`)**:
   - Add `target_category_id` (String 36, FK to `craft_categories.id`, nullable).
   - Add `desired_materials` (JSON, default list).
   - Add `desired_techniques` (JSON, default list).
   - Add `desired_motifs` (JSON, default list).
   - Add `preferred_region` (String 100, nullable).
   - Add `max_acceptable_moq` (Integer, nullable).
   - Add `max_lead_time_days` (Integer, nullable).
   - Add `requires_customization` (Boolean, default False).
   - Add `quality_specifications` (Text, nullable).
   - Add `packaging_requirements` (Text, nullable).
   - Add `destination_state` (String 100, nullable).
   - Add `destination_pincode` (String 10, nullable).
   - Add `currency` (String 3, default 'INR').
   - Add `data_provenance_level` (String 50, default 'USER_DECLARED').
   - Add `provenance_state` (String 30, default 'HUMAN_CONFIRMED').
   - Add relationship: `understandings = relationship("RequirementUnderstanding", back_populates="requirement", cascade="all, delete-orphan")`.

2. **`Match` (`matches`)**:
   - Add `product_id` (String 36, FK to `products.id`, nullable, index=True).
   - Add `engine_version` (String 50, default 'MATCHING_ENGINE_V1').
   - Add `craft_compatibility` (Float, nullable=False, default=0.0).
   - Add `material_compatibility` (Float, nullable=False, default=0.0).
   - Add `technique_compatibility` (Float, nullable=False, default=0.0).
   - Add `data_sufficiency_state` (String 30, default 'MATCHABLE', index=True).
   - Add `is_dismissed_by_buyer` (Boolean, default False).

3. **`MatchExplanation` (`match_explanations`)**:
   - Add `positive_reasons` (JSON, default list).
   - Add `limitations` (JSON, default list).
   - Add `unmatched_fields` (JSON, default list).
   - Add `missing_fields` (JSON, default list).

4. **`Enquiry` (`enquiries`)**:
   - Add `match_id` (String 36, FK to `matches.id`, nullable, index=True).
   - Add `rfq_reference_number` (String 50, unique=True, index=True).
   - Expand `status` enum: `DRAFT`, `OPEN`, `SENT`, `VIEWED`, `RESPONDED`, `NEGOTIATION`, `ACCEPTED`, `DECLINED`, `EXPIRED`, `CANCELLED`.
   - Add `artisan_response_message` (Text, nullable).
   - Add `counter_unit_price` (Numeric 10, 2, nullable).
   - Add `counter_lead_time_days` (Integer, nullable).
   - Add `viewed_at` (DateTime, nullable).
   - Add `responded_at` (DateTime, nullable).
   - Add `expires_at` (DateTime, nullable).

### 4.2 Alembic Migration Plan
- Migration Script: `backend/alembic/versions/20260326_0006_matching_and_rfq_linkage.py`
- Down Revision: `20260326_0005`
- Operations:
  - `op.create_table('requirement_understandings', ...)`
  - `op.add_column('buyer_requirements', ...)`
  - `op.add_column('matches', ...)`
  - `op.add_column('match_explanations', ...)`
  - `op.add_column('enquiries', ...)`
  - Create B-Tree indexes on `matches(requirement_id, product_id)`, `matches(requirement_id, rank)`, and `enquiries(rfq_reference_number)`.

---

## 5. API Architecture

All endpoints will be organized under `/api/v1` with strict RBAC, Pydantic validation, and server-side ownership checks:

### 5.1 Buyer Requirements Management (`/api/v1/buyer-requirements`)
| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/buyer-requirements` | `buyer` | Create new procurement brief / RFQ. |
| `GET` | `/api/v1/buyer-requirements` | `buyer` | List authenticated buyer's requirements (paginated, status filter). |
| `GET` | `/api/v1/buyer-requirements/{id}` | `buyer`, `admin` | Get detailed requirement by ID (ownership checked). |
| `PUT` | `/api/v1/buyer-requirements/{id}` | `buyer` | Update requirement specifications. |
| `DELETE` | `/api/v1/buyer-requirements/{id}` | `buyer` | Cancel or close requirement. |

### 5.2 AI Requirement Understanding (`/api/v1/buyer-requirements/{id}/understand`)
| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/buyer-requirements/{id}/understand` | `buyer` | Parse `raw_text` into staged attribute suggestions. |
| `GET` | `/api/v1/buyer-requirements/{id}/understand` | `buyer` | Retrieve latest staged extraction suggestions. |
| `POST` | `/api/v1/buyer-requirements/{id}/understand/confirm` | `buyer` | Accept/edit suggestions and apply to canonical requirement. |

### 5.3 Smart Matching Engine (`/api/v1/buyer-requirements/{id}/matches`)
| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/buyer-requirements/{id}/matches/run` | `buyer` | Execute two-stage matching pipeline and persist matches. |
| `GET` | `/api/v1/buyer-requirements/{id}/matches` | `buyer` | List ranked matches with composite scorecards (paginated). |
| `GET` | `/api/v1/matches/{match_id}` | `buyer`, `admin` | Get detailed match scorecard, factor weights, and explanation. |
| `POST` | `/api/v1/matches/{match_id}/dismiss` | `buyer` | Dismiss match candidate from buyer view. |

### 5.4 RFQ & Enquiry Linkage (`/api/v1/rfqs`)
| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/rfqs` | `buyer` | Create and send RFQ to artisan from match or requirement. |
| `GET` | `/api/v1/rfqs/sent` | `buyer` | List RFQs sent by authenticated buyer. |
| `GET` | `/api/v1/rfqs/incoming` | `artisan` | List RFQs received by authenticated artisan. |
| `GET` | `/api/v1/rfqs/{id}` | `buyer`, `artisan`, `admin` | Get RFQ details (strict party-to-transaction authorization). |
| `POST` | `/api/v1/rfqs/{id}/view` | `artisan` | Mark RFQ as VIEWED. |
| `POST` | `/api/v1/rfqs/{id}/respond` | `artisan` | Respond with ACCEPT, DECLINE, or COUNTER_OFFER. |
| `POST` | `/api/v1/rfqs/{id}/buyer-decision` | `buyer` | Accept or decline artisan's counter-offer. |

---

## 6. Matching Pipeline Architecture (Two-Stage Hybrid)

The matching pipeline is structured into two decoupled, deterministic stages:

```
                    ┌───────────────────────────────┐
                    │   Buyer Requirement / RFQ     │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 1: Candidate Retrieval & Hard Filter Filtering   │
       │                                                        │
       │  1. Hard Constraint Filter (SQL):                      │
       │     - product.status == 'PUBLISHED'                    │
       │     - artisan.is_active == True                        │
       │     - craft_id match (if hard constraint)              │
       │     - budget ceiling check (if strict)                 │
       │     - lead time deadline check (if strict)             │
       │                                                        │
       │  2. Semantic Vector Pre-Filter (pgvector):             │
       │     - Cosine distance: requirement.emb <=> product.emb │
       │     - Retrieve Top-K candidates (K = 50)               │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 2: Multi-Criteria Hybrid Scoring & Scorecards    │
       │                                                        │
       │  Evaluate 7 Component Scores:                          │
       │  - S_sem   : Semantic Vector Similarity [0, 1]         │
       │  - S_craft : Craft & Taxonomy Proximity [0, 1]         │
       │  - S_mat   : Material & Technique Overlap [0, 1]       │
       │  - S_cap   : Capacity vs Quantity Ratio [0, 1]         │
       │  - S_price : Price vs Target Budget [0, 1]             │
       │  - S_lead  : Lead Time vs Deadline [0, 1]              │
       │  - B_prov  : Institutional Provenance Bonus [0, 0.05]  │
       │                                                        │
       │  Composite Match Score = Sum(W_i * S_i) + B_prov       │
       │                                                        │
       │  Data Sufficiency State Evaluation:                    │
       │  [MATCHABLE | PARTIALLY_MATCHABLE | INSUFFICIENT_DATA] │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 3: Traceable Explanation Synthesis & Persistence │
       │                                                        │
       │  - Synthesize positive reasons from verified data      │
       │  - Flag missing data & trade-off limitations           │
       │  - Deterministic tie-breaking and rank assignment      │
       │  - Persist to `matches` and `match_explanations`       │
       └────────────────────────────────────────────────────────┘
```

---

## 7. Structured Matching Design

Structured matching evaluates domain parameters with exact and continuous scoring functions:

1. **Craft & Taxonomy Matching ($S_{craft}$)**:
   - If `product.craft_id == req.target_craft_id`: $S_{craft} = 1.0$.
   - Else if `product.category_id == req.target_category_id`: $S_{craft} = 0.70$.
   - Else if `product.category.parent_id == req.target_category.parent_id`: $S_{craft} = 0.40$.
   - Else: $S_{craft} = 0.0$.
2. **Material Compatibility ($S_{mat}$)**:
   - Evaluates the intersection of requested materials and declared product materials:
     $$S_{mat} = \frac{|\text{DesiredMaterials} \cap \text{ProductMaterials}|}{|\text{DesiredMaterials}|}$$
   - If the buyer specifies no materials: $S_{mat} = 1.0$ (neutral).
3. **Technique Compatibility ($S_{tech}$)**:
   - Evaluates normalized match between requested techniques and product technique / artisan craft technique:
     - Exact match = 1.0; Partial token overlap = 0.5; No match = 0.0.
4. **Capacity Compatibility ($S_{cap}$)**:
   - Compares required quantity ($Q_{req}$) to artisan monthly capacity ($C_{artisan}$):
     $$S_{cap} = \begin{cases} 
     1.0 & \text{if } C_{artisan} \ge 1.5 \times Q_{req} \\
     \frac{C_{artisan}}{1.5 \times Q_{req}} & \text{if } C_{artisan} < 1.5 \times Q_{req}
     \end{cases}$$
5. **Price Compatibility ($S_{price}$)**:
   - If product price $\le$ target unit price: $S_{price} = 1.0$.
   - If product price exceeds target price but $\le \text{max\_budget} / Q_{req}$:
     $$S_{price} = 1.0 - \frac{\text{Price} - \text{TargetPrice}}{\text{MaxBudget}/Q_{req} - \text{TargetPrice}} \times 0.5$$
   - If buyer specified no budget: $S_{price} = 1.0$ (neutral, flagged in limitations).
6. **Lead Time Compatibility ($S_{lead}$)**:
   - Compares available turnaround days ($D_{avail} = \text{deadline} - \text{today}$) against `product.lead_time_days`:
     $$S_{lead} = \begin{cases}
     1.0 & \text{if } \text{LeadDays} \le D_{avail} \\
     \max(0.0, 1.0 - \frac{\text{LeadDays} - D_{avail}}{D_{avail}}) & \text{if } \text{LeadDays} > D_{avail}
     \end{cases}$$

---

## 8. Semantic / Vector Matching Design

### 8.1 Provider Abstraction & Model Selection
Located in `ai/providers/embeddings/`:
- **Model Choice**: `gemini-embedding-2` configured with `output_dimensionality=768` to preserve compatibility with the platform's dialect-aware `EmbeddingVector(dim=768)` type.
- **Deprecation Note**: `text-embedding-004` was formally decommissioned by Google on January 14, 2026, and is strictly prohibited in this codebase.
- `BaseEmbeddingProvider` (`base.py`): Abstract interface with `embed_text(text: str) -> EmbeddingResult` and `embed_batch(texts: List[str]) -> List[EmbeddingResult]`.
- `GeminiEmbeddingProvider` (`gemini.py`): Async REST implementation targeting `models/gemini-embedding-2` with `output_dimensionality=768`, returning $L_2$-normalized 768-dimensional dense vectors.
- `MockEmbeddingProvider` (`mock.py`): Deterministic unit vector generation strictly for automated testing and offline CI (`is_mock=True`, `model_name="mock-embedding-test"`). Must NEVER be used or presented as real production semantic matching data.
- `EmbeddingProviderFactory` (`factory.py`): `get_embedding_provider()` based on environment settings.
- **Model Versioning & Integrity Rule**:
  - The embedding model name and version (`embedding_model_version`) are stored directly alongside each embedding record in metadata and provenance columns.
  - Embeddings generated by different models or versions must NEVER be silently mixed or compared. If the embedding model is upgraded, all embeddings must be regenerated and vector indexes re-indexed atomically.

### 8.2 Canonical Embedding Texts
To ensure vector semantic compatibility, textual representations are constructed using strict domain templates:
- **Product Text for Embedding**:
  `"Title: {title} | Craft: {craft_name} | Category: {category_name} | Materials: {materials} | Technique: {technique} | Style: {style} | Description: {storytelling_description}"`
- **Buyer Requirement Text for Embedding**:
  `"Requirement: {title} | Craft: {craft_name} | Materials: {desired_materials} | Techniques: {desired_techniques} | Description: {raw_text}"`

### 8.3 Vector Similarity Calculation
- Native PostgreSQL `pgvector`: Cosine distance operator `<=>`.
  $$\text{Cosine Similarity} = 1.0 - (\vec{u} \Leftrightarrow \vec{v})$$
- Normalization: Vector embeddings are $L_2$-normalized upon generation, ensuring cosine similarity ranges between $0.0000$ and $1.0000$.

---

## 9. Hard vs. Soft Constraint Design

To protect buyers from invalid candidates while preventing overly restrictive empty result sets:

### 9.1 Hard Constraints (Non-Negotiable Filters)
A candidate failing any active hard constraint is **immediately excluded** from Stage 2 scoring:
1. **Listing Lifecycle**: `product.status == 'PUBLISHED'` (DRAFT, ARCHIVED, or PAUSED products are never matched).
2. **Artisan Status**: Artisan account must not be banned, deleted, or suspended.
3. **GI Certification Mandate**: If buyer sets `requires_gi_certification = True`, product must belong to a verified GI craft (`craft.gi_tag_number IS NOT NULL`).
4. **Strict Budget Ceiling**: If buyer sets `max_budget_inr` and marks it strict, candidates with `price_inr > max_budget_inr / required_quantity` are filtered out.
5. **Strict Deadline**: If buyer sets `deadline_date` and marks it strict, candidates with `lead_time_days > available_days` are filtered out.

### 9.2 Soft Preferences (Scored Dimensions)
Soft preferences influence the ranking score without causing candidate elimination:
- Region / State preference.
- Non-essential secondary materials.
- Specific motifs or cultural styles.
- Customization capability (`is_customizable`).

---

## 10. Match Score Calculation Methodology

### 10.1 Score Nomenclature & Anti-Deception Charter
> [!IMPORTANT]
> The composite metric is formally designated **"MATCH SCORE"**.
> Under NO circumstances shall it be described as "purchase probability", "conversion rate", "success likelihood", or "guaranteed match". It represents multi-criteria attribute and semantic compatibility only.

### 10.2 Weight Distribution (`MATCHING_ENGINE_V1`)
All weights are explicitly declared, configuration-backed constants:

| Score Component | Weight ($W_i$) | Architectural & Domain Justification |
|---|---|---|
| **Semantic Similarity** ($S_{sem}$) | **0.25** | Captures stylistic, aesthetic, and descriptive nuances beyond rigid categorical tags. |
| **Craft & Category** ($S_{craft}$) | **0.20** | Ensures fundamental craft authenticity and taxonomic alignment. |
| **Material & Technique** ($S_{mat}$) | **0.15** | Verifies technical feasibility and authentic production methods. |
| **Capacity Compatibility** ($S_{cap}$) | **0.15** | Protects buyers from supply shortfalls and protects artisans from overcommitment. |
| **Price Compatibility** ($S_{price}$) | **0.15** | Ensures commercial viability within stated procurement parameters. |
| **Lead Time Adherence** ($S_{lead}$) | **0.10** | Ensures production can meet buyer fulfillment deadlines. |
| **Provenance Bonus** ($B_{prov}$) | **+0.05 (Bonus)** | Rewards authentic credentials: GI Authorized User (+0.03), Pehchan ID (+0.02). Capped at total score 1.0. |

$$\text{Composite Match Score} = \min\left(1.0000, \sum_{i=1}^{6} (W_i \times S_i) + B_{prov}\right)$$

### 10.3 Deterministic Tie-Breaking
When candidates achieve identical scores, ranking follows a deterministic order:
`ORDER BY composite_score DESC, provenance_bonus DESC, monthly_production_capacity DESC, updated_at DESC, id ASC`

---

## 11. Missing-Data & Data Sufficiency Strategy

The platform enforces the principle: **"Never punish an artisan unfairly for missing optional data, and never invent data to fill the gap."**

### 11.1 Dynamic Weight Re-Normalization
If a buyer has not provided optional criteria (e.g. no budget ceiling specified):
1. That component score is omitted.
2. The remaining component weights are re-normalized to sum to $1.0$:
   $$W'_i = \frac{W_i}{\sum_{j \in \text{Active}} W_j}$$
3. The omission is explicitly recorded in `MatchExplanation.limitations`.

### 11.2 Artisan Missing Data Policy
If an artisan's product listing lacks optional technical attributes (e.g. dimensions or secondary materials):
- The score component receives a neutral baseline ($0.50$).
- A limitation note is attached: *"Product dimensions/materials not specified by artisan; verify during enquiry."*
- Zero synthetic values are inserted.

### 11.3 Data Sufficiency Classification States
Each generated match is assigned one of three data sufficiency states:
- `MATCHABLE`: All primary structured attributes and embeddings are present on both buyer requirement and product.
- `PARTIALLY_MATCHABLE`: One or more optional attributes (e.g., budget, lead time, dimensions) are absent; neutral weighting applied.
- `INSUFFICIENT_INFORMATION`: Crucial parameters are missing; manual inquiry required.

---

## 12. Explainability Architecture

Every surfaced match generates an immutable, data-grounded `MatchExplanation`:

### 12.1 Grounded Justification Matrix
Explanations are assembled strictly from actual database fields:
- **Positive Reasons (`positive_reasons`)**:
  - *"Matches requested craft Paithani Weaving (GI-tagged)."*
  - *"Stated monthly capacity of 25 units easily satisfies requirement of 10 units."*
  - *"Product unit price ₹4,200 is within stated target budget of ₹5,000."*
- **Limitations & Disclaimers (`limitations`)**:
  - *"Artisan is located in Nashik, Maharashtra; buyer preferred Gujarat origin."*
  - *"Lead time of 14 days leaves narrow buffer before requested deadline of 18 days."*
  - *"Buyer did not specify maximum budget; price compatibility assumed neutral."*
- **Decomposed Factor Scorecard (`factors_json`)**:
  Stores exact numerical component scores and active weights for rendering interactive radar charts or breakdown sliders in the UI.

---

## 13. RFQ & Enquiry Lifecycle

The commercial linkage workflow connects buyers with matched artisans through a controlled state machine:

```
               ┌───────────────────────┐
               │    BuyerRequirement   │
               └───────────┬───────────┘
                           │ Run Matching
                           ▼
               ┌───────────────────────┐
               │     Match Results     │
               └───────────┬───────────┘
                           │ Select Candidate & Initiate RFQ
                           ▼
               ┌───────────────────────┐
               │    Enquiry / RFQ      │◄── Status: DRAFT
               └───────────┬───────────┘
                           │ Send RFQ
                           ▼
               ┌───────────────────────┐
               │     Status: SENT      │
               └───────────┬───────────┘
                           │ Artisan Opens Dashboard
                           ▼
               ┌───────────────────────┐
               │    Status: VIEWED     │
               └─────┬───────────┬─────┘
                     │           │
      Artisan Accepts│           │Artisan Counter-Offers
                     ▼           ▼
        ┌──────────────────┐   ┌───────────────────────┐
        │ Status: ACCEPTED │   │  Status: NEGOTIATION  │
        └──────────────────┘   └───────────┬───────────┘
                                           │ Buyer Accepts/Declines
                                           ▼
                               ┌───────────────────────┐
                               │ ACCEPTED / DECLINED   │
                               └───────────────────────┘
```

### 13.1 Server-Side State Transition Rules
- `DRAFT` $\rightarrow$ `SENT`: Only by owning buyer.
- `SENT` $\rightarrow$ `VIEWED`: Triggered automatically when artisan loads RFQ details.
- `VIEWED` $\rightarrow$ `ACCEPTED`: By artisan (confirms agreed quantity, price, timeline).
- `VIEWED` $\rightarrow$ `NEGOTIATION`: By artisan (submits `counter_unit_price` or `counter_lead_time_days`).
- `VIEWED` $\rightarrow$ `DECLINED`: By artisan (with structured decline reason: *Capacity Full*, *Material Unavailable*, *Timeline Infeasible*).
- `NEGOTIATION` $\rightarrow$ `ACCEPTED`: By buyer.
- Any state $\rightarrow$ `CANCELLED`: By buyer prior to acceptance.
- Any unresponded state $\rightarrow$ `EXPIRED`: System cron after deadline.

---

## 14. Security, RBAC & IDOR Design

1. **Buyer Data Privacy**:
   - Buyers can only access their own requirements (`where requirement.buyer_id == current_user.buyer_profile.id`).
   - Match results are visible only to the buyer who submitted the requirement.
2. **Artisan Data Privacy**:
   - Artisans cannot view general buyer requirements or other artisans' incoming RFQs.
   - Artisans can only view RFQs explicitly addressed to their `artisan_id`.
3. **Contact Information Protection**:
   - Initial match scorecards and RFQs conceal private contact details (phone number, email, street address).
   - Communication occurs strictly through platform enquiry messaging.
4. **Credential Isolation**:
   - All AI/embedding API keys (e.g. Gemini) remain backend-only. Never sent to frontend clients.

---

## 15. Provenance & Audit Trail Design

Every matching and linkage operation writes an immutable record to `audit_logs`:
- `MATCH_RUN_EXECUTED`: Records `requirement_id`, candidate count, top score, algorithm version (`MATCHING_ENGINE_V1`), and processing duration.
- `RFQ_CREATED`: Records `buyer_id`, `artisan_id`, `product_id`, proposed quantity, and unit price.
- `RFQ_STATUS_CHANGED`: Records previous state, new state, actor ID, and counter-offer values.

All models inherit or specify `data_provenance_level`:
- `USER_DECLARED`: Requirements provided by buyer.
- `AI_SUGGESTED`: Staged suggestions in `requirement_understandings`.
- `CALCULATED`: Deterministic match scores in `matches`.
- `HUMAN_CONFIRMED`: Final accepted RFQs and confirmed requirement attributes.

---

## 16. Embedding Architecture & Storage

1. **Vector Dimension**: Exactly 768 dimensions (compatible with `pgvector` and standard embedding models).
2. **Storage**: Dialect-aware `EmbeddingVector(dim=768)` in `backend/app/models/custom_types.py`.
3. **Database Index**:
   - PostgreSQL: HNSW index on `buyer_requirements.embedding` and `products.embedding` using `vector_cosine_ops`:
     `CREATE INDEX idx_products_embedding_hnsw ON products USING hnsw (embedding vector_cosine_ops);`
   - SQLite (Local / CI): Stored as JSON strings; semantic search falls back to in-memory cosine dot-product calculation for test reproducibility.
4. **Invalidation Policy**:
   - Product embedding is regenerated whenever title, storytelling description, craft, or materials are updated.
   - Requirement embedding is generated upon submission or confirmation of AI understanding.

---

## 17. Performance & Indexing Strategy

1. **Two-Stage Scalability**:
   - In Stage 1, PostgreSQL evaluates hard relational filters and HNSW vector distance in sub-50ms.
   - In Stage 2, Python evaluates detailed scoring only on the top $K=50$ candidates.
2. **Database Indexes**:
   - `CREATE INDEX ix_buyer_req_buyer_status ON buyer_requirements(buyer_id, status);`
   - `CREATE INDEX ix_matches_req_score ON matches(requirement_id, composite_score DESC);`
   - `CREATE INDEX ix_enquiries_artisan_status ON enquiries(artisan_id, status);`
   - `CREATE INDEX ix_enquiries_buyer_status ON enquiries(buyer_id, status);`
3. **Deterministic Pagination**:
   - Match results use keyset or limit/offset pagination with deterministic tie-breaking.

---

## 18. Frontend Pages & Components Plan

All user interfaces will be developed using Next.js 14+ App Router, Tailwind CSS, and Lucide icons:

### 18.1 Buyer Portal
1. **`frontend/src/app/buyer/requirements/new/page.tsx`**:
   - Procurement brief creation wizard.
   - Natural language brief input ("Paste your RFQ brief...") with instant "Analyze with AI" trigger.
   - Structured parameter inputs (craft, quantity, budget, deadline, materials).
2. **`frontend/src/app/buyer/requirements/[id]/page.tsx`**:
   - Requirement overview and AI Understanding review card.
   - Field-by-field accept/edit controls for extracted parameters.
   - "Find Matches" action button.
3. **`frontend/src/app/buyer/requirements/[id]/matches/page.tsx`**:
   - Ranked match candidates list with match score badges (e.g. `92% Match`).
   - Match Explanation Drawer displaying positive reasons, limitations, and factor breakdown sliders.
   - "Send RFQ / Enquiry" modal.
4. **`frontend/src/app/buyer/rfqs/page.tsx`**:
   - Sent RFQ tracker with status timeline (`SENT` $\rightarrow$ `VIEWED` $\rightarrow$ `RESPONDED` $\rightarrow$ `ACCEPTED`).

### 18.2 Artisan Portal
1. **`frontend/src/app/artisan/rfqs/page.tsx`**:
   - Incoming RFQs dashboard with quantity, target price, and delivery deadline badges.
   - Status filters (`Pending Response`, `Accepted`, `Declined`).
2. **`frontend/src/app/artisan/rfqs/[id]/page.tsx`**:
   - RFQ inspection page showing buyer specifications, matched product/craft details.
   - Action controls: **Accept Terms**, **Submit Counter-Offer** (price & lead time), or **Decline**.

---

## 19. Test Strategy

Phase 6 will add **16 new automated tests** across 5 focused test suites:

1. **`tests/test_buyer_requirements.py`** (4 tests):
   - `test_create_buyer_requirement`: Creation of structured requirement with validation.
   - `test_buyer_requirement_auth_and_idor`: Unauthorized access and cross-buyer isolation.
   - `test_update_and_cancel_requirement`: State transition and update handling.
   - `test_requirement_data_provenance`: Provenance state tracking (`USER_DECLARED`).
2. **`tests/test_requirement_understanding.py`** (3 tests):
   - `test_ai_understanding_extraction_staging`: Verifies that AI extraction writes only to staging table.
   - `test_buyer_confirmation_workflow`: Acceptance/editing of suggestions promotes fields to canonical requirement.
   - `test_mock_provider_fallback`: Deterministic extraction using mock provider without external API calls.
3. **`tests/test_embeddings.py`** (2 tests):
   - `test_embedding_provider_mock_dimension`: Verifies normalized 768-dimensional vector output.
   - `test_embedding_cosine_similarity_math`: Validates mathematical bounds ($0.0 \le \text{sim} \le 1.0$).
4. **`tests/test_matching_engine.py`** (4 tests):
   - `test_hard_constraint_filtering`: Validates elimination of unpublished products, inactive artisans, or GI tag violations.
   - `test_hybrid_scoring_deterministic_weights`: Verifies composite score calculation against known inputs.
   - `test_missing_data_neutral_scoring`: Verifies that missing optional fields trigger neutral scoring and limitations notes without failure.
   - `test_explainability_matrix_synthesis`: Verifies generation of data-grounded positive reasons and limitations.
5. **`tests/test_rfq_enquiry_lifecycle.py`** (3 tests):
   - `test_rfq_creation_from_match`: Links enquiry to requirement, match, and product.
   - `test_artisan_counter_offer_and_buyer_acceptance`: Verifies multi-party negotiation flow.
   - `test_rfq_idor_isolation`: Cross-artisan and cross-buyer access rejection with 403 Forbidden.

*Target Suite Total*: **98 / 98 tests passing** (82 existing + 16 new).

---

## 20. Migration Strategy

- **Backward Compatibility Guarantee**: All changes are strictly additive.
- Existing database tables (`buyer_requirements`, `matches`, `match_explanations`, `enquiries`) will be extended using nullable columns or sensible defaults.
- All schema changes executed exclusively through Alembic migration `20260326_0006_matching_and_rfq_linkage.py`.
- No data loss or table truncation will occur.

---

## 21. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Sparse Product Catalogue** | Low match count for niche crafts. | Matching engine falls back to matching artisan craft capability (`ArtisanCraft`) when specific catalogued products are absent. |
| **External AI API Downtime** | Failure during RFQ natural language parsing or embedding generation. | `MockEmbeddingProvider` and rule-based heuristic extraction act as immediate circuit-breaker fallbacks. |
| **Cross-Party Data Leakage** | Buyer or artisan private contact information exposed. | Server-side DTO sanitization strips all contact PII before transmitting candidate or RFQ details. |
| **Arbitrary Score Interpretation** | Buyers assume score is statistical purchase probability. | Explicit UI labeling ("MATCH SCORE") and component factor scorecards with plain-language explanations. |

---

## 22. Explicit Phase 6 Boundaries

To ensure architectural discipline and milestone integrity, **Phase 6 strictly excludes**:
- Demand forecasting, festival calendars, and regional trend analytics (Phase 7).
- Indic voice recording, ASR, and multilingual speech synthesis (Phase 7).
- Offline PWA caching with Dexie.js and Service Workers (Phase 7).
- Admin KYC/GI verification moderation workflows (Phase 8).
- Payment gateways, escrow contracts, and shipping fulfillment tracking (Future Commerce Phase).
- Dynamic learning models or reinforcement learning from click conversion rates.

---

## 23. Future Integration Points for Phase 7+

- **Demand Intelligence (Phase 7)**: Seasonal demand surge indicators will feed into the matching engine as an optional advisory signal for institutional buyers.
- **Multilingual Voice RFQ (Phase 7)**: Artisans will be able to record audio voice responses to incoming RFQs.
- **Admin Moderation (Phase 8)**: High-value institutional RFQs (e.g. > ₹5,00,000) will appear in the admin governance portal for compliance review.

---

## 24. File-by-File Implementation Plan

### Files to be Created:
1. `backend/alembic/versions/20260326_0006_matching_and_rfq_linkage.py`: Alembic migration.
2. `backend/app/models/requirement_understanding.py`: Staging entity for AI RFQ extraction.
3. `ai/providers/embeddings/__init__.py`: Package initialization.
4. `ai/providers/embeddings/base.py`: Abstract `BaseEmbeddingProvider`.
5. `ai/providers/embeddings/gemini.py`: Gemini REST embedding provider.
6. `ai/providers/embeddings/mock.py`: Deterministic mock embedding provider for tests.
7. `ai/providers/embeddings/factory.py`: Embedding provider factory.
8. `ai/matching/__init__.py`: Package initialization exporting `MatchingEngine` and `MATCHING_ENGINE_V1`.
9. `ai/matching/engine.py`: Core two-stage hybrid matching engine and explainability builder.
10. `backend/app/schemas/matching.py`: Pydantic v2 schemas for requirements, understandings, matches, and RFQs.
11. `backend/app/services/matching_service.py`: Service layer orchestrating candidate retrieval, scoring, and persistence.
12. `backend/app/services/rfq_service.py`: Service layer managing RFQ negotiation state machine.
13. `backend/app/api/v1/endpoints/buyer_requirements.py`: REST endpoints for requirements and AI understanding.
14. `backend/app/api/v1/endpoints/matches.py`: REST endpoints for matching runs and scorecards.
15. `backend/app/api/v1/endpoints/rfqs.py`: REST endpoints for RFQ / Enquiry negotiation.
16. `frontend/src/app/buyer/requirements/new/page.tsx`: Next.js RFQ brief creation wizard.
17. `frontend/src/app/buyer/requirements/[id]/page.tsx`: Next.js requirement overview & AI understanding review.
18. `frontend/src/app/buyer/requirements/[id]/matches/page.tsx`: Next.js match results and explanation scorecard.
19. `frontend/src/app/buyer/rfqs/page.tsx`: Next.js sent RFQ tracker.
20. `frontend/src/app/artisan/rfqs/page.tsx`: Next.js incoming RFQs dashboard.
21. `frontend/src/app/artisan/rfqs/[id]/page.tsx`: Next.js RFQ response and counter-offer page.
22. `tests/test_buyer_requirements.py`: Automated tests for requirement CRUD and IDOR.
23. `tests/test_requirement_understanding.py`: Automated tests for AI extraction and staging.
24. `tests/test_embeddings.py`: Automated tests for vector embeddings.
25. `tests/test_matching_engine.py`: Automated tests for hybrid matching and scoring.
26. `tests/test_rfq_enquiry_lifecycle.py`: Automated tests for RFQ negotiation.
27. `docs/matching_engine.md`: System specification and algorithm documentation.
28. `docs/matching_scorecard.md`: Mathematical methodology and weight justifications.
29. `docs/rfq_lifecycle.md`: Negotiation state machine and commercial linkage guide.

### Files to be Modified:
1. `backend/app/models/buyer.py`: Extend `BuyerRequirement`, `Match`, and `MatchExplanation`.
2. `backend/app/models/market.py`: Extend `Enquiry` with RFQ lifecycle fields.
3. `backend/app/models/__init__.py`: Register and export `RequirementUnderstanding`.
4. `backend/app/api/v1/router.py`: Mount `buyer_requirements`, `matches`, and `rfqs` routers.
5. `backend/app/core/config.py`: Add embedding provider and matching configuration constants.
6. `docs/database_schema.md`: Add Section 2.7 documenting Phase 6 entities.
7. `README.md`: Update milestone progress and matching capabilities.
8. `docs/phase_plan.md`: Update Phase 6 status and acceptance notes.

---

## 25. Acceptance Criteria

Phase 6 will be considered 100% complete when:
1. **Migration Integrity**: Alembic migration `20260326_0006` applies cleanly and passes `alembic upgrade head --sql` dry run.
2. **AI Staging Isolation**: Natural language RFQ extraction writes strictly to `requirement_understandings`; canonical `BuyerRequirement` fields are updated only upon explicit buyer confirmation.
3. **Hard Constraint Enforcement**: The matching engine strictly eliminates unpublished products, suspended artisans, or GI violations from candidate pools.
4. **Deterministic Hybrid Scoring**: The engine evaluates both vector semantic similarity and structured parameters, yielding reproducible scores with configuration-controlled weights.
5. **No-Fabrication & Honest Missing Data**: Missing optional fields are handled with neutral scoring and explicit limitation notes; zero synthetic data is inserted.
6. **Transparent Explainability**: Every generated match includes data-grounded positive reasons, trade-offs, and factor scorecards.
7. **Complete RFQ Lifecycle**: The commercial linkage flow from match to RFQ dispatch, viewing, negotiation, counter-offer, and acceptance functions seamlessly with server-side validation.
8. **Comprehensive IDOR Defense**: All buyer and artisan endpoints enforce strict server-side party-to-transaction authorization.
9. **Full Automated Test Suite**: All 16 new automated tests pass, and all 82 existing Phase 1–5 regression tests pass (98/98 tests passing).
10. **Frontend Experience**: Buyers can draft briefs, review AI extractions, inspect match explanations, and dispatch RFQs; artisans can inspect incoming RFQs and submit counter-offers.
