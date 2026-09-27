# SIH 26090: PROBLEM–SOLUTION MAPPING
## Systematic Alignment of SIH Challenges to Architectural Solutions

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. Problem Statement Analysis

The Indian handicrafts sector faces foundational challenges across discovery, authenticity, pricing, and connectivity:

```
┌─────────────────────────────────┬────────────────────────────────────────────────────────┐
│ SIH Problem Dimension           │ Platform Architectural Solution                        │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 1. Rural Disconnection &        │ Offline-First PWA with Dexie 4.x IndexedDB, Service    │
│    Intermittent Connectivity    │ Worker cache-first shell, UUIDv4 idempotent sync queue │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Unverified Claims & Fake     │ Verifiable Craft Passport + Cryptographic SHA-256      │
│    Machine Counterfeits         │ Provenance Hash Chain + Government Registry Linkage    │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Complex Cataloguing & Low    │ AI Product Studio: Vision suggestions staged for       │
│    Artisan Digital Literacy     │ explicit human confirmation (no automated overwrite)   │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Opaque Pricing & Artisan     │ FAIR_PRICE_ENGINE_V1: Pure Decimal cost accounting,    │
│    Economic Exploitation        │ living-wage floor guarantee, N >= 3 market evidence    │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 5. Mismatched Institutional     │ MATCHING_ENGINE_V1: Hard constraints + gemini-         │
│    Buyer Procurement            │ embedding-2 768-dim semantic similarity + scorecard    │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 6. Volatile Seasonal Demand     │ DEMAND_ENGINE_V1: Classical WMA/Holt-Winters with      │
│    & Production Planning        │ N >= 12 eligibility gate & zero future leakage         │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 7. Platform Governance &        │ Unified Moderation Queue + Neutral Review Signals +    │
│    Authority Gating             │ Strict separation: ADMIN_REVIEWED != AUTHORITY_VERIFIED│
└─────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 2. In-Depth Challenge Mapping

### Challenge 1: Rural Intermittent Connectivity
- **Field Reality**: Master artisans reside in remote craft clusters (e.g., Kutch, Pochampally, Varanasi, Bastar) where 4G/5G mobile coverage drops frequently to 2G or offline states.
- **Architectural Response**:
  - The frontend is an installable Progressive Web Application (PWA) with a Service Worker ([`frontend/public/sw.js`](file:///e:/frontend/public/sw.js)) caching the app shell (`CacheFirst`) and craft taxonomies (`StaleWhileRevalidate`).
  - IndexedDB storage ([`frontend/src/lib/offline/db.ts`](file:///e:/frontend/src/lib/offline/db.ts)) preserves product drafts, RFQs, and an append-only mutation queue.
  - Background synchronization ([`frontend/src/lib/offline/useSync.ts`](file:///e:/frontend/src/lib/offline/useSync.ts)) sends batch requests with UUIDv4 idempotency keys and 3-way conflict detection on reconnect.

### Challenge 2: Counterfeits & Misleading GI Claims
- **Field Reality**: Powerloom and factory-manufactured goods are often falsely marketed as handloom or GI-certified, eroding trust.
- **Architectural Response**:
  - Direct database linkage to official Geographical Indications Registry records ([`backend/app/models/craft.py`](file:///e:/backend/app/models/craft.py)).
  - **Strict `AUTHORITY_VERIFIED` Guardrail**: Admin moderation approval alone can only grant `ADMIN_APPROVED` or `ADMIN_REVIEWED`. The status `AUTHORITY_VERIFIED` requires explicit authoritative registry references (`authority_source`, `authoritative_registry_reference`, `evidence_url`).
  - Cryptographic provenance tracking ([`backend/app/models/governance.py`](file:///e:/backend/app/models/governance.py)) recording every field transition in a tamper-evident SHA-256 hash chain.

### Challenge 3: Artisan Cataloguing & Digital Literacy
- **Field Reality**: Artisans struggle with typing long descriptions, categorizing materials, or setting standard dimensions.
- **Architectural Response**:
  - AI Product Studio ([`frontend/src/app/artisan/products/[id]/ai-studio/page.tsx`](file:///e:/frontend/src/app/artisan/products/[id]/ai-studio/page.tsx)) allows artisans to simply photograph their work.
  - Google Gemini vision models analyze images to suggest materials, primary colors, techniques, and draft storytelling descriptions.
  - **Artisan Confirmation Gate**: Staged in `ai_studio_runs`. The artisan reviews suggestions and explicitly accepts, edits, or rejects each attribute before anything touches canonical records.

### Challenge 4: Fair Pricing & Living Wage Assurance
- **Field Reality**: Middlemen dictate prices, often forcing artisans to sell below living cost during lean seasons.
- **Architectural Response**:
  - `FAIR_PRICE_ENGINE_V1` ([`ai/pricing/engine.py`](file:///e:/ai/pricing/engine.py)) calculates costs using pure Python Decimal arithmetic (`ROUND_HALF_UP`), eliminating floating-point drift.
  - **Living Wage Floor Guarantee**: Enforces $\text{floor\_price} \ge \text{unit\_production\_cost}$ under all market conditions; the system mathematically refuses to suggest sub-cost pricing.
  - **Market Evidence Honesty**: Requires $N \ge 3$ verified, comparable market price observations (e.g., ODOP portals, government emporiums). If $N < 3$, it falls back to a transparent Cost-Only Baseline.

### Challenge 5: Institutional Buyer Linkage
- **Field Reality**: Corporate gifting managers and institutional buyers face discovery friction and cannot assess artisan lead times or capacity.
- **Architectural Response**:
  - Natural language procurement briefs are parsed into structured specifications ([`frontend/src/app/buyer/requirements/new/page.tsx`](file:///e:/frontend/src/app/buyer/requirements/new/page.tsx)).
  - `MATCHING_ENGINE_V1` ([`ai/matching/engine.py`](file:///e:/ai/matching/engine.py)) uses Google `gemini-embedding-2` 768-dimensional normalized dense vectors and 7-factor scoring ($S_{\text{sem}}, S_{\text{craft}}, S_{\text{mat}}, S_{\text{cap}}, S_{\text{price}}, S_{\text{lead}}, B_{\text{prov}}$).
  - Transparent Scorecards break down exactly why an artisan matched, highlighting feasibility and trade-offs.

---

## 3. Measurable Outcome Comparison

| Dimension | Traditional Middleman Model | SIH 26090 Platform Implementation |
|:---|:---|:---|
| **Artisan Value Share** | 20–30% of retail price | **85–95%** directly to artisan (direct buyer linkage) |
| **Pricing Basis** | Middleman buyer discretion | **Algorithmic cost-plus living wage floor guarantee** |
| **GI / Craft Verification** | Unverified oral claims | **Cryptographically chained provenance & registry references** |
| **Procurement Cycle** | 3–6 weeks of broker inquiries | **Instant semantic match & structured RFQ negotiation** |
| **Rural Usability** | Desktop/high-bandwidth required | **Offline-first PWA with automatic background sync** |
| **AI Transparency** | Black-box opacity | **Staged suggestions, explicit human review & traceable math** |
