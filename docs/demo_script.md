# SIH 26090: INTERACTIVE DEMO SCRIPT FOR JUDGES
## 15-Step End-to-End Walkthrough

**Target Audience**: Smart India Hackathon (SIH) 2026 Evaluation Panel  
**Estimated Walkthrough Time**: 12–15 minutes  
**Guiding Principle**: Absolute honesty. Every screen clearly indicates what data is user-provided, what is source-backed from official registries, what is mathematically calculated, and what is staged AI suggestions.

---

### Step 1: Secure Role-Based Authentication & Session Defense
- **Route**: [`/login`](file:///e:/frontend/src/app/login/page.tsx)
- **Actor**: Any User (`artisan`, `buyer`, or `admin`)
- **Action**: Log in using email/phone and password, or simulate token rotation.
- **Under the Hood**: Argon2id password verification, issuance of short-lived JWT access token (15m) and secure refresh token (7d).
- **What to Notice**: Session cookies/tokens use token family tracking. Replaying an expired refresh token triggers immediate family-wide revocation to defend against token theft.

---

### Step 2: Artisan Profile & Verifiable Craft Passport
- **Route**: [`/artisan/profile`](file:///e:/frontend/src/app/artisan/profile/page.tsx) and [`/passport/[id]`](file:///e:/frontend/src/app/passport/[id]/page.tsx)
- **Actor**: Master Artisan
- **Action**: View the artisan profile and inspect the verifiable Craft Passport.
- **Data Status**:
  - *User-Provided*: Artisan name, location (district, state), production capacity.
  - *Source-Backed*: Official GI Registry certificate linkage and Ministry of Textiles Pehchan ID.
- **What to Notice**: The Craft Passport distinguishes between internal platform review (`ADMIN_REVIEWED`) and formal government registry confirmation (`AUTHORITY_VERIFIED`). The system never auto-promotes self-reported claims.

---

### Step 3: Craft Catalogue & Regional GI Browsing
- **Route**: [`/catalogue`](file:///e:/frontend/src/app/catalogue/page.tsx)
- **Actor**: Public Buyer / Evaluator
- **Action**: Browse Indian handicrafts filtered by GI Tag status, state/region, and craft category.
- **Data Status**: Seeded from authentic Indian Geographical Indications records (e.g., Chanderi Fabric, Madhubani Painting, Blue Pottery of Jaipur).
- **What to Notice**: Real-time filtering, responsive cards with certified GI tags, and clean public asset loading without exposing internal storage bucket paths.

---

### Step 4: Product Creation & Staged Draft
- **Route**: [`/artisan/products/new`](file:///e:/frontend/src/app/artisan/products/new/page.tsx)
- **Actor**: Artisan
- **Action**: Create a new handcrafted product listing with photos, material specifications, and storytelling description.
- **Data Status**: Initial state is `DRAFT` / `ARTISAN_PROVIDED`.
- **What to Notice**: Media attachments are validated for MIME safety, max 10MB limit, and path traversal prevention before submission.

---

### Step 5: AI Product Studio — Vision Extraction & Human Confirmation
- **Route**: [`/artisan/products/[id]/ai-studio`](file:///e:/frontend/src/app/artisan/products/[id]/ai-studio/page.tsx)
- **Actor**: Artisan
- **Action**: Upload an uncurated workshop photograph. Request AI catalogue analysis. Review suggested attributes (materials, primary color, motif technique). Accept, edit, or reject each field.
- **What AI Does**: Google Gemini (`gemini-1.5-flash`) analyzes visual features and suggests structured attributes with honest confidence levels.
- **What to Notice**: Suggestions are strictly isolated in `AI_SUGGESTED` staging. They **never** directly overwrite the canonical product fields until the artisan explicitly clicks "Confirm". The artisan retains full creative sovereignty.

---

### Step 6: Explainable Fair Price Intelligence
- **Route**: [`/artisan/products/[id]/pricing`](file:///e:/frontend/src/app/artisan/products/[id]/pricing/page.tsx)
- **Actor**: Artisan
- **Action**: Enter raw material costs, labor hours, and living wage hourly rate. Trigger `FAIR_PRICE_ENGINE_V1`.
- **What is Calculated**:
  - Pure Python Decimal arithmetic calculates direct unit production cost, workshop overhead, and break-even floor price.
  - The engine enforces `floor_price >= unit_production_cost` under all conditions.
  - Evaluates regional market observations: requires $N \ge 3$ valid comparable observations to display market range; otherwise cleanly defaults to the Cost-Only Baseline.
- **What to Notice**: Complete step-by-step mathematical explanation trace. The price suggestion is advisory; the artisan decides their final selling price.

---

### Step 7: Institutional Buyer Procurement Requirement Creation
- **Route**: [`/buyer/requirements/new`](file:///e:/frontend/src/app/buyer/requirements/new/page.tsx)
- **Actor**: Enterprise / Institutional Buyer
- **Action**: Paste an unstructured corporate procurement brief (e.g., *"Need 100 authentic handwoven silk stoles with gold zari borders for Diwali corporate gifting by next month, budget Rs 1500 each"*).
- **What AI Does**: Language model extracts structured procurement parameters (craft category, required quantity, target unit price, maximum lead time, GI tag requirement).
- **What to Notice**: Staged in `requirement_understandings` for buyer review before locking the specification.

---

### Step 8: Buyer Requirement Confirmation & Activation
- **Route**: [`/buyer/requirements/[id]`](file:///e:/frontend/src/app/buyer/requirements/[id]/page.tsx)
- **Actor**: Buyer
- **Action**: Review extracted parameters, make manual corrections, and confirm requirement into `ACTIVE` state.
- **What to Notice**: Prevents inaccurate AI interpretations from initiating commercial matchmaking without human oversight.

---

### Step 9: Two-Stage Semantic Matching Engine
- **Route**: [`/buyer/requirements/[id]/matches`](file:///e:/frontend/src/app/buyer/requirements/[id]/matches/page.tsx)
- **Actor**: Buyer
- **Action**: Click "Find Matching Artisans".
- **What the Engine Does**:
  - *Stage 1*: Eliminates candidates failing hard constraints (capacity feasibility, minimum order quantity ceiling, GI requirement).
  - *Stage 2*: Calculates 7-component score using `gemini-embedding-2` 768-dimensional normalized vectors:
    $$S_{\text{final}} = w_1 S_{\text{sem}} + w_2 S_{\text{craft}} + w_3 S_{\text{mat}} + w_4 S_{\text{cap}} + w_5 S_{\text{price}} + w_6 S_{\text{lead}} + B_{\text{prov}}$$
- **What to Notice**: Ranked results display compatibility scores ($0.0 \le S \le 1.0$), NOT fake "probability of sale" percentages.

---

### Step 10: Transparent Match Scorecard & Limitation Callouts
- **Route**: [`/buyer/requirements/[id]/matches`](file:///e:/frontend/src/app/buyer/requirements/[id]/matches/page.tsx)
- **Actor**: Buyer
- **Action**: Click on a candidate card to expand the Explainability Scorecard.
- **What to Notice**: The modal displays factor breakdown progress bars, positive justifications (e.g., *"Artisan has 10 units/mo capacity, sufficient for requirement"*), and transparent limitation callouts (e.g., *"Lead time is 18 days vs requested 15 days; requires minor negotiation"*).

---

### Step 11: Commercial RFQ Creation & Negotiation State Machine
- **Route**: [`/buyer/rfqs`](file:///e:/frontend/src/app/buyer/rfqs/page.tsx) and [`/artisan/rfqs/[id]`](file:///e:/frontend/src/app/artisan/rfqs/[id]/page.tsx)
- **Actor**: Buyer & Artisan
- **Action**: Buyer initiates an RFQ with reference `RFQ-YYYYMMDD-XXXX`. Artisan opens the inquiry, reviews terms, and submits a counter-offer.
- **What to Notice**: Enforces strict party-to-transaction IDOR checks. Third parties cannot view or modify the transaction. Full state transition history recorded in audit logs.

---

### Step 12: Real Demand Intelligence & Trend Forecasting
- **Route**: [`/artisan/demand`](file:///e:/frontend/src/app/artisan/demand/page.tsx) and [`/admin/analytics/demand`](file:///e:/frontend/src/app/admin/analytics/demand/page.tsx)
- **Actor**: Artisan / Administrator
- **Action**: Inspect seasonal demand trends and festivals for target craft.
- **What to Notice**: Metrics strictly distinguish `OBSERVED` (verified historical commercial signals), `CALCULATED` (moving averages), and `FORECAST` (WMA/Holt-Winters projections). If history is $<12$ periods, the system displays `INSUFFICIENT_HISTORY` rather than hallucinating fake demand curves.

---

### Step 13: Offline-First PWA Resilience Demonstration
- **Route**: Any Artisan Screen (e.g., [`/artisan/products/new`](file:///e:/frontend/src/app/artisan/products/new/page.tsx))
- **Actor**: Artisan in Low-Connectivity Village
- **Action**: Open DevTools, switch Network to "Offline". Create a new product draft or submit an RFQ counter-offer. Notice the "Working Offline" banner. Switch Network back to "Online".
- **Under the Hood**: Dexie 4.x IndexedDB stores mutations locally. Background sync fires with UUIDv4 idempotency keys, reconciling mutations on the server without duplicate writes.
- **What to Notice**: Zero data loss, zero duplicate rows, and no sensitive KYC credentials stored offline.

---

### Step 14: Unified Admin Moderation Console & Critical Allowlist
- **Route**: [`/admin/moderation`](file:///e:/frontend/src/app/admin/moderation/page.tsx) and [`/admin/verification`](file:///e:/frontend/src/app/admin/verification/page.tsx)
- **Actor**: Platform Administrator
- **Action**: Inspect pending catalogue submissions and artisan credential verifications.
- **What to Notice**:
  - Updating operational fields (`stock_quantity`) keeps products `PUBLISHED`.
  - Updating critical fields (`title`, `price_inr`, `materials`) triggers re-moderation (`PENDING_APPROVAL`).
  - Admin approval assigns `ADMIN_REVIEWED`. Granting `AUTHORITY_VERIFIED` strictly requires entering official government registry evidence.

---

### Step 15: Cryptographic Provenance Inspector & SHA-256 Tamper Detection
- **Route**: [`/admin/provenance`](file:///e:/frontend/src/app/admin/provenance/page.tsx)
- **Actor**: Compliance Auditor / Judge
- **Action**: Select a product or verification entity. View the complete chronological timeline of field changes. Click "Verify Cryptographic Chain".
- **Under the Hood**: Iterates through `ProvenanceEvent` records, recomputing $\text{SHA-256}(\text{canonical\_payload} \parallel \text{prev\_hash})$.
- **What to Notice**: Green "Chain Cryptographically Intact" badge. Demonstrates that any manual database alteration or out-of-order insertion breaks the mathematical chain and is immediately flagged as `PAYLOAD_TAMPERED`.
