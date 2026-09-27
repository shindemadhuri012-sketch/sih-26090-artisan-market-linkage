"""
SIH 26090: Ingestion Manifest & Provenance Receipt Manager
Calculates SHA-256 checksums, tracks execution batches, and outputs immutable audit receipts.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class IngestionManifest(BaseModel):
    manifest_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_name: str
    source_url: str
    custodian: str
    license_type: str
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_file_path: str
    raw_file_sha256: str
    raw_record_count: int = 0
    validated_record_count: int = 0
    rejected_record_count: int = 0
    deduplicated_record_count: int = 0
    transformation_version: str = "1.0.0"
    execution_status: str = "PENDING"
    rejection_reasons: Dict[str, int] = Field(default_factory=dict)
    summary_notes: Optional[str] = None


def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 checksum of any local file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_str_sha256(content: str) -> str:
    """Computes SHA-256 checksum of raw text/JSON content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def save_manifest(manifest: IngestionManifest, output_dir: str = "data/manifests") -> str:
    """Persists manifest as JSON in the manifests directory."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"manifest_{manifest.source_id.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    target_path = os.path.join(output_dir, filename)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)
    return target_path
