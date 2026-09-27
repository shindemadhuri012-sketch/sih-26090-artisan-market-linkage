# SIH 26090: Provenance & Data Lineage Architecture
## Traceability, Auditability & Zero-Fabrication Enforcement

---

## 1. Traceability Principle: "Where did this record come from?"

Every external record imported into the SIH 26090 platform must answer four audit questions:
1. **Who is the legal custodian?** (e.g., Office of CGPDTM, DPIIT, Ministry of Commerce)
2. **What is the verifiable source URL?** (e.g., `https://ipindia.gov.in/registered-gls.htm`)
3. **When was it retrieved?** (ISO 8601 UTC timestamp)
4. **What batch/manifest validated it?** (Cryptographic SHA-256 hash and manifest UUID)

---

## 2. Ingestion Manifest Schema

Every execution of an ingestion adapter creates an unalterable receipt stored in `data/manifests/`:

```json
{
  "manifest_id": "0d1829e0-cb41-4775-8ce6-a7fe01f2f0a8",
  "source_id": "GI-REGISTRY-INDIA",
  "source_name": "Geographical Indications Registry of India",
  "source_url": "https://ipindia.gov.in/registered-gls.htm",
  "custodian": "Office of the Controller General of Patents, Designs & Trade Marks (CGPDTM), DPIIT",
  "license_type": "Government Open Data License - India (GODL)",
  "retrieval_timestamp": "2026-09-26T15:05:07.123456+00:00",
  "raw_file_path": "data/raw/gi_registry_handicrafts_official.json",
  "raw_file_sha256": "7665d0c44531a042e88a096c...",
  "raw_record_count": 12,
  "validated_record_count": 12,
  "rejected_record_count": 0,
  "deduplicated_record_count": 0,
  "transformation_version": "1.0.0",
  "execution_status": "COMPLETED_SUCCESS",
  "summary_notes": "Successfully extracted 12 authenticated records from Geographical Indications Registry of India."
}
```

---

## 3. Demo / Sample Data Isolation

To prevent demo data from corrupting legitimate marketplace metrics:
- Every table includes `is_sample_or_demo: boolean NOT NULL DEFAULT false`.
- Any fixture used for local edge-case testing carries `is_sample_or_demo = true`.
- The database enforces that records with `is_sample_or_demo = true` are excluded from official cluster statistics, national price benchmarks, and public demand forecasts.
