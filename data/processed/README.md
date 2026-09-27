# Processed Data Directory (`data/processed/`)

This directory contains sanitized, validated, and normalized seed datasets generated from the raw sources via `scripts/ingestion/`.

### Standards:
- Formatted as clean JSON or Parquet.
- Strict Pydantic schema validation applied.
- Deduplicated via deterministic keys.
- Complete provenance headers embedded in every record.
