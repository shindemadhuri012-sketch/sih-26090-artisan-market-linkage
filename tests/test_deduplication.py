"""
SIH 26090: Deduplication Unit Tests
Verifies deterministic duplicate identification and preservation of unique records.
"""

from scripts.ingestion.common.deduplicator import (
    deduplicate_gi_records,
    deduplicate_odop_records,
    normalize_text
)


def test_text_normalization():
    """Verify that normalize_text removes special characters and standardizes spaces."""
    assert normalize_text("  Banarasi   Silk, &  Brocades! ") == "banarasi silk brocades"


def test_gi_deduplication_exact_tag():
    """Verify that records with identical GI tag numbers are deduplicated."""
    records = [
        {"gi_tag_number": "GI-4", "name": "Pochampally Ikat", "origin_state": "Telangana"},
        {"gi_tag_number": "GI-4", "name": "Pochampally Ikat Duplicate", "origin_state": "Telangana"},
        {"gi_tag_number": "GI-7", "name": "Chanderi Saree", "origin_state": "Madhya Pradesh"}
    ]
    unique, dup_count = deduplicate_gi_records(records)
    assert len(unique) == 2
    assert dup_count == 1
    assert unique[0]["name"] == "Pochampally Ikat"


def test_odop_deduplication_composite_key():
    """Verify that records with identical state, district, and product are deduplicated."""
    records = [
        {"state": "Uttar Pradesh", "district": "Varanasi", "product_name": "Banarasi Silk"},
        {"state": "Uttar Pradesh", "district": "Varanasi", "product_name": "banarasi   silk"},  # Case/space variant
        {"state": "Uttar Pradesh", "district": "Moradabad", "product_name": "Brassware"}
    ]
    unique, dup_count = deduplicate_odop_records(records)
    assert len(unique) == 2
    assert dup_count == 1
