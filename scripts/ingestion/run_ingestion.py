"""
SIH 26090: Master Real-Data Ingestion Pipeline
Executes ingestion for official Indian GI Registry and ODOP data sources.
Validates records, enforces deduplication, maintains raw immutability,
outputs cryptographic manifests, and saves processed seeds.
"""

import os
import sys
import json
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.ingestion.common.manifest import IngestionManifest, compute_sha256, save_manifest
from scripts.ingestion.gi.gi_adapter import GIIngestionAdapter
from scripts.ingestion.odop.odop_adapter import ODOPIngestionAdapter
from backend.app.core.telemetry import logger


def run_pipeline() -> Dict[str, Any]:
    """Executes the complete data ingestion pipeline across all official sources."""
    print("=" * 80)
    print("SIH 26090: REAL-DATA INGESTION PIPELINE")
    print("Authoritative Government Sources: GI Registry of India (CGPDTM) & ODOP (DPIIT)")
    print("=" * 80)

    adapters = [
        GIIngestionAdapter(),
        ODOPIngestionAdapter()
    ]

    pipeline_report = {
        "sources_processed": 0,
        "total_raw_records": 0,
        "total_validated_records": 0,
        "total_rejected_records": 0,
        "total_duplicates_filtered": 0,
        "manifests_generated": [],
        "processed_files_generated": []
    }

    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)

    for adapter in adapters:
        print(f"\n[+] Ingesting from: {adapter.source_name} ({adapter.source_id})")
        print(f"    Source URL: {adapter.source_url}")
        print(f"    Custodian:  {adapter.custodian}")

        # 1. Load Raw Source
        raw_content, raw_file_path = adapter.load_raw_data()
        raw_sha256 = compute_sha256(raw_file_path)
        print(f"    [1/5] Raw file verified: {raw_file_path} (SHA-256: {raw_sha256[:16]}...)")

        # 2. Parse Raw Records
        raw_records = adapter.parse_raw(raw_content)
        raw_count = len(raw_records)
        print(f"    [2/5] Parsed {raw_count} raw records.")

        # 3. Validate Records
        valid_records, rejected_records = adapter.validate_records(raw_records)
        val_count = len(valid_records)
        rej_count = len(rejected_records)
        print(f"    [3/5] Validation: {val_count} passed, {rej_count} rejected.")

        # 4. Deduplicate Records
        unique_records, dup_count = adapter.deduplicate(valid_records)
        unique_count = len(unique_records)
        print(f"    [4/5] Deduplication: {unique_count} unique records preserved ({dup_count} duplicates removed).")

        # 5. Manifest & Transformation
        manifest = IngestionManifest(
            source_id=adapter.source_id,
            source_name=adapter.source_name,
            source_url=adapter.source_url,
            custodian=adapter.custodian,
            license_type=adapter.license_type,
            raw_file_path=raw_file_path,
            raw_file_sha256=raw_sha256,
            raw_record_count=raw_count,
            validated_record_count=val_count,
            rejected_record_count=rej_count,
            deduplicated_record_count=dup_count,
            execution_status="COMPLETED_SUCCESS",
            summary_notes=f"Successfully extracted {unique_count} authenticated records from {adapter.source_name}."
        )

        manifest_path = save_manifest(manifest)
        print(f"    [5/5] Ingestion audit manifest saved to: {manifest_path}")

        # Transform and write processed seed
        transformed = adapter.transform(unique_records, manifest.manifest_id)
        out_filename = f"{adapter.source_id.lower().replace('-', '_')}_seed.json"
        out_path = os.path.join(processed_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(transformed, f, indent=2, ensure_ascii=False)
        print(f"    --> Normalized seed saved to: {out_path} ({len(transformed)} records)")

        # Update pipeline aggregates
        pipeline_report["sources_processed"] += 1
        pipeline_report["total_raw_records"] += raw_count
        pipeline_report["total_validated_records"] += val_count
        pipeline_report["total_rejected_records"] += rej_count
        pipeline_report["total_duplicates_filtered"] += dup_count
        pipeline_report["manifests_generated"].append(manifest_path)
        pipeline_report["processed_files_generated"].append(out_path)

    print("\n" + "=" * 80)
    print("INGESTION SUMMARY REPORT:")
    print(f"  Sources Processed:      {pipeline_report['sources_processed']}")
    print(f"  Total Raw Records:      {pipeline_report['total_raw_records']}")
    print(f"  Valid Records:          {pipeline_report['total_validated_records']}")
    print(f"  Rejected Records:       {pipeline_report['total_rejected_records']}")
    print(f"  Duplicates Filtered:    {pipeline_report['total_duplicates_filtered']}")
    print(f"  Output Seeds Generated: {len(pipeline_report['processed_files_generated'])}")
    print("=" * 80)

    return pipeline_report


if __name__ == "__main__":
    run_pipeline()
