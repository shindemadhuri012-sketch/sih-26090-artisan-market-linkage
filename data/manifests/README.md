# Ingestion Manifests Directory (`data/manifests/`)

This directory contains cryptographic audit records and execution receipts for every data ingestion batch run against raw sources.

### Standard Manifest Schema:
- `manifest_id`: UUID
- `source_id`: Text identifier
- `source_name`: Official agency/authority name
- `source_url`: Verifiable URL
- `retrieval_timestamp`: ISO 8601 UTC timestamp
- `raw_file_sha256`: Cryptographic checksum of raw input
- `raw_record_count`: Number of raw rows/items
- `validated_record_count`: Successfully validated items
- `rejected_record_count`: Rejected malformed items
- `deduplicated_record_count`: Redundant duplicate items filtered
- `transformation_version`: Script version
- `license`: Open government data license identifier
