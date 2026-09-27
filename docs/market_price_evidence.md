# Market Price Evidence Architecture & Quality Framework

SIH 26090 — Institutional Provenance & Comparability Standards

---

## 1. Objective

To provide artisans with realistic, evidence-backed context on what authentic craft products realize in official and verified marketplaces, without hallucinating competitor listings.

---

## 2. Institutional Source Hierarchy

Market observations are categorized into transparent institutional source types:

1. **`GOVERNMENT`**:
   - Entities like TRIFED (*Tribes India*), Central Cottage Industries Emporium (CCIC), State Handloom & Handicraft Corporations (e.g., Mrignayanee, Co-optex, Boyanika).
2. **`OFFICIAL_REGISTRY`**:
   - Geographical Indication authorized user price benchmarks, state ODOP directories.
3. **`OFFICIAL_MARKETPLACE`**:
   - Government e-Marketplace (GeM), verified cooperative direct sales portals.
4. **`VERIFIED_ARTISAN`**:
   - Master craftsperson peer-group sales benchmarks documented through craft passport verification.
5. **`AUTHORIZED_SOURCE` / `OTHER_DOCUMENTED_SOURCE`**:
   - Academic research surveys, trade council reports (e.g., Export Promotion Council for Handicrafts).

Arbitrary web scrapers or unverified classified sites are **never** labeled as authoritative.

---

## 3. Evidence Quality Scoring

Observations are assigned a qualitative evidence score based on documented criteria:

| Quality Status | Criteria |
|---|---|
| **`HIGH`** | $\ge 5$ comparable observations; at least 2 from `GOVERNMENT` or `OFFICIAL_REGISTRY`; all fresh ($< 24$ months); complete technical attributes. |
| **`MEDIUM`** | $3 - 4$ comparable observations; fresh ($< 24$ months); compatible material and technique descriptors. |
| **`LOW`** | Contains observations older than 24 months (`STALE`), or sources lack institutional verification. |
| **`INSUFFICIENT`** | Fewer than 3 valid comparable observations ($N < 3$). |

---

## 4. Comparability Rules

Market observations are filtered against the target artisan product using multi-attribute matching:
- **`craft_id` Match (Mandatory)**: An observation must match the exact craft record.
- **Material Consistency**: If the artisan product is pure mulberry silk, observations specifying synthetic polyester or blended rayon are excluded (`NOT_COMPARABLE`).
- **Currency Match**: Must be Indian Rupees (`INR`).
- **Deduplication**: Identical tuples of `(source_name, observed_price, observation_date)` are deduplicated to prevent artificial clustering.

---

## 5. Zero-Fabrication Guarantee

If no authentic source is currently available for a specific craft, the `market_price_observations` table remains clean and empty. The system will cleanly report `INSUFFICIENT_MARKET_EVIDENCE` and fall back to the artisan's **Cost-Only Baseline**.
