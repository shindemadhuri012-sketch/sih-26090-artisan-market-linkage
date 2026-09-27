# SIH 26090: Match Scorecard & Explainability Architecture

---

## 1. Overview

Every candidate evaluated by `MATCHING_ENGINE_V1` produces an immutable, explainable **Match Scorecard** (`Match` + `MatchExplanation`). 

To ensure complete trust and transparency between commercial procurement teams and traditional artisans, the platform avoids "black box" recommendations. Every match score is broken down into constituent subscores, transparent positive justifications, and upfront limitations.

---

## 2. Factor Breakdown & Formulas

| Score Factor | Dimension | Base Weight ($w_i$) | Evaluation Method |
|---|---|---|---|
| **$S_{\text{sem}}$** | Semantic Similarity | 0.25 | Cosine similarity of 768-dim embeddings: $\frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$ |
| **$S_{\text{craft}}$** | Craft & Category | 0.20 | $1.0$ if exact craft ID match; $0.7$ if same category; $0.0$ otherwise |
| **$S_{\text{mat}}$** | Material Overlap | 0.15 | Jaccard similarity: $\frac{|M_{\text{buyer}} \cap M_{\text{product}}|}{|M_{\text{buyer}} \cup M_{\text{product}}|}$ (or $0.5$ if unspecified) |
| **$S_{\text{tech}}$** | Technique Overlap | (included in $S_{\text{mat}}$) | Set overlap between requested and traditional artisan techniques |
| **$S_{\text{cap}}$** | Capacity Fit | 0.15 | Ratio $\min\left(1.0, \frac{C_{\text{monthly}}}{Q_{\text{req}}}\right)$ with threshold curve (or $0.5$ if missing) |
| **$S_{\text{price}}$** | Price Compatibility | 0.15 | $1.0$ if $P \le P_{\text{target}}$; linear falloff up to $1.35 \times P_{\text{target}}$ |
| **$S_{\text{lead}}$** | Lead Time Fit | 0.10 | $1.0$ if $T_{\text{lead}} \le T_{\text{buyer}}$; linear degradation beyond deadline |
| **$B_{\text{prov}}$** | Provenance Bonus | $+0.05$ max | $+0.03$ for GI-certified craft; $+0.02$ for active Craft Passport |

---

## 3. Dynamic Re-Weighting Formula

When a buyer requirement leaves optional criteria unspecified (such as budget, lead time, or specific materials), the engine redistributes the unallocated weights proportionally across active criteria:

$$w_i' = \frac{w_i}{\sum_{k \in \text{Active}} w_k}$$

This guarantees that:
1. Active weights always sum to $1.0$.
2. Artisans are never penalized for unspecified buyer parameters.
3. The composite score remains strictly normalized between $0.0$ and $1.0$.

---

## 4. Explainability Structure (`MatchExplanation`)

Every match record is accompanied by a structured explanation entity (`match_explanations`) stored with the following schema:

```json
{
  "composite_score": 0.88,
  "data_sufficiency_state": "COMPLETE",
  "positive_reasons": [
    "Verified Geographical Indication (GI) craft origin",
    "Monthly production capacity (150 units) exceeds required quantity (100 units)",
    "Product price (₹1,800) fits comfortably within target unit price (₹2,000)",
    "High semantic similarity with buyer procurement brief"
  ],
  "limitations": [
    "Lead time of 25 days approaches the requested 30-day deadline"
  ],
  "unmatched_fields": [],
  "missing_fields": [],
  "capacity_justification": "Sustainable production capacity of 150 units/month covers batch requirement of 100 units.",
  "price_justification": "Catalog price of ₹1,800 is 10.0% below buyer target of ₹2,000.",
  "provenance_justification": "GI Tag registered with Ministry of Commerce; verified artisan passport active."
}
```

---

## 5. UI Presentation Guidelines

In the frontend buyer interface (`/buyer/requirements/[id]/matches`):
- Display score as **Match Score: XX%**, never "Probability of Purchase".
- Render multi-slider scorecard breakdown showing exact factor scores ($S_{\text{sem}}, S_{\text{craft}}, S_{\text{mat}}, S_{\text{cap}}, S_{\text{price}}, S_{\text{lead}}$).
- Render green badges for `positive_reasons` and amber/red notices for `limitations`.
- Display data sufficiency badge: `COMPLETE` (green), `PARTIAL_PROFILE` (yellow), or `UNVERIFIED_DATA` (gray).
