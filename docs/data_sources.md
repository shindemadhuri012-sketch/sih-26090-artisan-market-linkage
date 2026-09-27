# SIH 26090: Legitimate External Data Sources & Citations
## Authoritative Public Data Registries Grounding the Platform

---

## 1. Official Data Sources Inventory

| Source Identifier | Source Authority | Official Custodian | Public URL | License / Usage | Verified Status |
|---|---|---|---|---|---|
| **`GI-REGISTRY-INDIA`** | Geographical Indications Registry of India | Office of the Controller General of Patents, Designs and Trade Marks (CGPDTM), DPIIT, Ministry of Commerce and Industry | `https://ipindia.gov.in/registered-gls.htm` | Government Open Data License - India (GODL) | **VERIFIED & INGESTED** |
| **`ODOP-DPIIT-INDIA`** | One District One Product (ODOP) Initiative | Department for Promotion of Industry and Internal Trade (DPIIT) & Invest India | `https://www.investindia.gov.in/one-district-one-product` | Open Government Information (Invest India) | **VERIFIED & INGESTED** |
| **`DC-HANDICRAFTS`** | Office of the Development Commissioner (Handicrafts) | Ministry of Textiles, Government of India | `http://handicrafts.nic.in` | Public Government Publication | **MAPPED (Phase 2 Auth)** |
| **`HANDLOOM-CENSUS`** | 4th All India Handloom Census | Ministry of Textiles / data.gov.in | `https://data.gov.in/resource/4th-all-india-handloom-census` | National Data Sharing and Accessibility Policy (NDSAP) | **MAPPED (Phase 4 Pricing)** |
| **`COMMODITY-INDICES`**| Central Silk Board & Cotton Corporation of India | Ministry of Textiles | `https://csb.gov.in/statistics/silk-prices/` | Public Agricultural & Textile Commodity Indices | **MAPPED (Phase 4 Pricing)** |

---

## 2. Ingestion Status & Verification Notes

### Source 1: `GI-REGISTRY-INDIA`
- **Extracted Records**: 12 verified registered handicraft GI tags spanning textiles, metalware, pottery, and traditional folk art.
- **Attributes Verified**: Registered GI Tag number, traditional raw materials, geographical cluster (State + District), cultural heritage narrative.
- **Raw File**: `data/raw/gi_registry_handicrafts_official.json` (SHA-256 verified in manifest).
- **Seed Output**: `data/processed/gi_registry_india_seed.json`.

### Source 2: `ODOP-DPIIT-INDIA`
- **Extracted Records**: 10 official district-to-craft mappings across Uttar Pradesh, Rajasthan, Madhya Pradesh, West Bengal, Odisha, Gujarat, Maharashtra, and Assam.
- **Attributes Verified**: District, State, Product Name, Category, HSN Code, Export Potential.
- **Raw File**: `data/raw/odop_catalogue_official.json` (SHA-256 verified in manifest).
- **Seed Output**: `data/processed/odop_dpiit_india_seed.json`.
