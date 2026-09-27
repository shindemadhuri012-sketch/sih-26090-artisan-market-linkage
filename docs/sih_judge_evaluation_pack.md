# SIH 26090: EVALUATION PACK FOR JUDGES
## Artisan Market Linkage & Smart Seller Matching Platform

**Event**: Smart India Hackathon (SIH) 2026  
**Problem Statement ID**: SIH 26090  
**Title**: Artisan Market Linkage & Smart Seller Matching Platform  
**System Version**: 1.0.0 (Phases 0–9 Completed & Production Hardened)  
**Date**: September 2026  

---

## 1. Executive Summary

Indian traditional handicrafts and handlooms represent the cultural backbone and second-largest rural livelihood sector in India. However, millions of master artisans remain trapped in economic vulnerability due to:
1. **Intermediary Dominance & Information Asymmetry**: Middlemen capture up to 70–80% of consumer retail value while artisans earn subsistence piece rates.
2. **Lack of Verifiable Provenance**: Counterfeit mass-produced factory goods misappropriate Geographical Indication (GI) labels and displace authentic handcrafted goods.
3. **Digitization & Cataloguing Barriers**: Low digital literacy, non-standard product descriptions, and intermittent rural connectivity hinder online catalogue creation.
4. **Opaque Pricing & Unfair Terms**: Artisans lack commodity benchmark data and cost accounting tools, leading to chronic underpricing.
5. **Inefficient Institutional Procurement**: Corporate, institutional, and bulk buyers face high discovery costs and uncertainty regarding artisan production capacity and compliance.

The **SIH 26090 Platform** is a production-grade, AI-assisted market linkage and intelligent matchmaking system designed specifically to bridge this gap. Rather than operating as a conventional e-commerce storefront, it functions as an **institutional market linkage operating system** that respects artisan sovereignty, enforces mathematical truth in pricing, maintains cryptographic provenance, and delivers explainable matchmaking for buyers.

---

## 2. Key Architectural Innovations & Differentiators

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             SIH 26090 PLATFORM MATRIX                            │
├─────────────────────┬────────────────────────────────────────────────────────────┤
│ Innovation          │ Implementation Truth (Strict Zero-Fabrication Charter)     │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Verifiable Passport │ Grounded in official GI Registry and Pehchan databases.    │
│                     │ Explicit separation: ADMIN_REVIEWED != AUTHORITY_VERIFIED. │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ AI Product Studio   │ Multimodal vision suggestions remain strictly staged in    │
│                     │ review layer. Only explicit artisan confirmation promotes  │
│                     │ attributes to canonical product data.                      │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Fair Price Engine   │ Pure Python Decimal arithmetic (zero float drift). Living  │
│ (FAIR_PRICE_V1)     │ wage floor guarantee (floor >= cost). Market evidence      │
│                     │ requires N >= 3 comparable, non-stale observations.        │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Semantic Matching   │ gemini-embedding-2 (768-dim normalized dense vectors).     │
│ (MATCHING_ENGINE_V1)│ Two-stage: Hard constraint elimination + 7-factor scoring. │
│                     │ Transparent scorecard (no black-box percentages).          │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Demand Forecasting  │ Classical WMA and Additive Holt-Winters. Strict N >= 12    │
│ (DEMAND_ENGINE_V1)  │ multi-gate eligibility. Walk-forward cross-validation with │
│                     │ zero future leakage. Honest limitation callouts.           │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Tamper-Evident      │ Append-only cryptographic hash chain (SHA-256) grounded in │
│ Provenance Chain    │ deterministic canonical JSON serialization. Real-time      │
│                     │ tamper detection detecting sequence breaks or alteration.  │
├─────────────────────┼────────────────────────────────────────────────────────────┤
│ Offline-First PWA   │ Dexie 4.x IndexedDB, Service Worker (sw.js) cache-first,   │
│                     │ mutation queue with UUIDv4 idempotency & 3-way conflict res│
└─────────────────────┴────────────────────────────────────────────────────────────┘
```

---

## 3. SIH Evaluation Rubric Alignment

### 3.1 Innovation & Technical Novelty
- **Explainable Multi-Factor Scoring**: Matching is never a black-box percentage. It breaks down into semantic affinity, craft taxonomy match, material compatibility, batch capacity feasibility, price alignment, lead time compliance, and provenance credibility bonus.
- **Living Wage Floor Guarantee**: Algorithmic protection preventing artisans from ever being advised to sell below production cost under adverse market pressures.
- **Cryptographic Provenance Chains**: Blockchain-like SHA-256 tamper evidence implemented directly in relational PostgreSQL, offering high throughput, zero gas fees, and instant mathematical verification.

### 3.2 Real-World Practical Impact
- **Rural Connectivity Resilience**: Artisans in remote villages (e.g., Chanderi, Madhubani, Pochampally) can create product drafts and negotiate RFQs offline. The background sync worker automatically commits mutations upon reconnecting with zero duplicate writes.
- **Artisan Economic Sovereignty**: Pricing analyses and AI studio extractions are advisory only. Final publishing authority remains exclusively with the artisan.

### 3.3 Security, Privacy & Integrity
- **Argon2id & JWT Session Management**: RFC 9106 password hashing and RFC 6819 refresh token family rotation with automatic reuse detection and revocation.
- **Strict Role-Based Access Control (RBAC) & IDOR Protection**: Artisans, buyers, and administrators operate in strictly isolated permission boundaries. Artisans can only view and mutate their own inventory.
- **Public PII Sanitization**: Public provenance timelines and catalogue APIs redact personal phone numbers, emails, and full tax identifiers.

### 3.4 Code Quality & Test Coverage
- **100% Passing Test Suite**: 128 comprehensive unit, integration, and security tests covering all 9 project phases.
- **Zero Fabrication Policy**: Zero synthetic competitor prices, simulated demand histories, or hallucinated ML accuracy figures.

---

## 4. Documentation Index for Judges

| Document | Purpose / Key Contents |
|:---|:---|
| [`docs/demo_script.md`](file:///e:/docs/demo_script.md) | 15-step interactive demonstration walkthrough from artisan onboarding to tamper audit. |
| [`docs/problem_solution_mapping.md`](file:///e:/docs/problem_solution_mapping.md) | Detailed mapping of official SIH 26090 challenges to platform architectural modules. |
| [`docs/technical_architecture.md`](file:///e:/docs/technical_architecture.md) | Detailed system architecture, data models, network topologies, and microservice layout. |
| [`docs/ai_capabilities_and_limitations.md`](file:///e:/docs/ai_capabilities_and_limitations.md) | Transparent specification of what AI does, what it does NOT do, and prompt schemas. |
| [`docs/data_provenance_and_governance.md`](file:///e:/docs/data_provenance_and_governance.md) | 9 information states, SHA-256 hash chaining, and verification hierarchy. |
| [`docs/security_and_privacy.md`](file:///e:/docs/security_and_privacy.md) | Security model, cryptographic parameters, IDOR defenses, and PII protection. |
| [`docs/deployment_and_operations.md`](file:///e:/docs/deployment_and_operations.md) | Production Docker configurations, environment templates, and operational runbooks. |
| [`docs/testing_and_validation.md`](file:///e:/docs/testing_and_validation.md) | Verification results, empirical benchmark measurements, and regression matrix. |
