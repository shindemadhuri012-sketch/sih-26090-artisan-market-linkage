# SIH 26090: AI CAPABILITIES & HONEST LIMITATIONS
## Specification of Artificial Intelligence Roles, Failure Modes & Data Safety

**Project**: SIH 26090 – Artisan Market Linkage & Smart Seller Matching  
**Phase**: Phase 9 — Production Deployment & Judge Pack  

---

## 1. AI Honesty Charter

In enterprise and government procurement systems, unverified AI outputs present severe risks of hallucination, false certification, and legal liability. The SIH 26090 platform adheres to a strict **AI Honesty Charter**:

1. **AI Output Is NEVER an Automatic Fact**: Model outputs are classified strictly as `AI_SUGGESTED`. Only explicit human confirmation elevates suggestions to `HUMAN_CONFIRMED`.
2. **AI Is NEVER an Authoritative Verifier**: Formal government or GI certification (`AUTHORITY_VERIFIED`) can only be granted through documented registry references (`authority_source`, `authoritative_registry_reference`, `evidence_url`). AI cannot verify authenticity.
3. **Zero Fabricated Confidence**: The platform does not generate arbitrary confidence percentages (e.g., "94.2% authentic"). If calibrated probabilities are not genuinely returned by the model API, confidence is explicitly stored as `null`.
4. **Deterministic Calculation Integrity**: Financial pricing and demand forecasts do NOT rely on LLM text generation. They execute via audited, deterministic mathematical algorithms.

---

## 2. Capabilities & Boundaries Matrix

| AI Component | Underlying Model / Technology | What It DOES | What It DOES NOT DO (Honest Boundaries) |
|:---|:---|:---|:---|
| **Product AI Studio** | Google Gemini (`gemini-1.5-flash`) via async REST | Analyzes artisan workshop photos to suggest craft techniques, primary materials, colors, and draft storytelling descriptions. | Does NOT directly modify product listings; does NOT verify if an item is handmade or powerloom; does NOT award GI tags. |
| **Requirement Understanding** | Google Gemini Language Model | Parses unstructured procurement briefs into structured constraints (category, units, budget, lead time). | Does NOT commit orders; does NOT override buyer intent; requires explicit buyer review. |
| **Semantic Embeddings** | Google Gemini (`gemini-embedding-2`, 768-dim) | Generates 768-dimensional normalized dense vectors capturing semantic meaning of crafts and buyer requirements. | Does NOT mix embeddings from different models; deprecated `text-embedding-004` is completely excluded. |
| **Hybrid Matching Engine** | `MATCHING_ENGINE_V1` | Eliminates infeasible candidates via hard gates; scores remaining via 7-factor compatibility formula ($S_{\text{sem}}, S_{\text{craft}}, S_{\text{mat}}, S_{\text{cap}}, S_{\text{price}}, S_{\text{lead}}, B_{\text{prov}}$). | Does NOT output arbitrary "probability of sale"; does NOT fabricate conversion rates; explicitly flags missing data. |
| **Fair Price Intelligence** | `FAIR_PRICE_ENGINE_V1` (Pure Python Decimal) | Deterministically computes production cost baselines, living wage floors, and evidence-based market ranges ($N \ge 3$). | Does NOT fabricate competitor prices; does NOT simulate synthetic demand curves; does NOT recommend sub-cost prices. |
| **Demand Forecasting** | `DEMAND_ENGINE_V1` (WMA & Holt-Winters) | Generates statistical time-series projections with residual standard error prediction intervals ($N \ge 12$). | Does NOT claim accuracy without held-out walk-forward validation; does NOT fabricate historical transactions. |

---

## 3. Provider Failure Handling & Graceful Degradation

If external AI APIs (Google Gemini Vision or Embeddings) experience latency spikes, network failures, HTTP 5xx errors, or quota exhaustion:

1. **Explicit Error States**: The platform catches exceptions and returns an explicit, safe response:
   ```json
   {
     "status": "AI_SERVICE_UNAVAILABLE",
     "detail": "AI inference provider is currently unavailable. Manual entry is enabled."
   }
   ```
2. **Zero Synthetic Fallbacks**: The system **never** substitutes fake AI suggestions, synthetic attributes, or simulated confidence scores during an outage.
3. **Manual Flow Continuity**: All user workflows (product cataloguing, pricing calculations, requirement posting) function completely and autonomously without requiring live AI connectivity.
