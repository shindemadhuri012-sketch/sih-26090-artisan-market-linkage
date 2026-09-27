# Data Architecture & Real-Data Repository
## SIH 26090: Artisan Market Linkage & Smart Seller Matching

---

## 1. Directory Structure

```
data/
├── raw/            # Pristine, unmodified downloaded source files (JSON, CSV, PDF, HTML)
├── processed/      # Normalized, schema-validated, and deduplicated seed files
├── manifests/      # Ingestion batch audit records, checksums, and execution reports
└── README.md       # Data policy documentation (this file)
```

---

## 2. Real Data Policy & Zero-Fabrication Mandate

1. **Authentic Government Records**: All handicraft cluster, Geographical Indication (GI), and district mapping records must originate from authoritative public portals (GI Registry of India / DPIIT, Invest India ODOP, Ministry of Textiles DC Handicrafts).
2. **Immutability of Raw Inputs**: Files placed in `data/raw/` must NEVER be manually modified or edited. Any corrections or normalizations must occur via deterministic Python transformation scripts in `scripts/ingestion/`.
3. **Audit Trail**: Every batch in `data/manifests/` records the source URL, SHA-256 hash, record count, execution timestamp, and license details.
4. **Sample & Demo Isolation**: Any fixture used strictly for development or synthetic edge-case tests must reside in `tests/fixtures/` and carry an explicit `is_sample_or_demo: true` attribute. Demo records are never loaded into the production seed pipeline.
