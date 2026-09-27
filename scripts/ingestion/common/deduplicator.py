"""
SIH 26090: Deterministic Record Deduplicator
Identifies and resolves duplicates using strict natural keys while preserving source lineage.
"""

import re
from typing import List, Dict, Any, Tuple


def normalize_text(text: str) -> str:
    """Normalizes string for comparison: lowercase, removes punctuation, single spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def deduplicate_gi_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Deduplicates GI records using primary key: normalized gi_tag_number,
    and secondary key: normalized (name + origin_state).
    """
    seen_gi_tags = set()
    seen_name_state = set()
    unique_records = []
    duplicate_count = 0

    for record in records:
        raw_tag = str(record.get("gi_tag_number", "")).strip().upper()
        norm_name = normalize_text(record.get("name", ""))
        norm_state = normalize_text(record.get("origin_state", ""))
        name_state_key = f"{norm_name}::{norm_state}"

        if raw_tag and raw_tag in seen_gi_tags:
            duplicate_count += 1
            continue
        if name_state_key in seen_name_state:
            duplicate_count += 1
            continue

        if raw_tag:
            seen_gi_tags.add(raw_tag)
        seen_name_state.add(name_state_key)
        unique_records.append(record)

    return unique_records, duplicate_count


def deduplicate_odop_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Deduplicates ODOP records using natural composite key: (state + district + normalized product_name).
    """
    seen_composite_keys = set()
    unique_records = []
    duplicate_count = 0

    for record in records:
        norm_state = normalize_text(record.get("state", ""))
        norm_dist = normalize_text(record.get("district", ""))
        norm_prod = normalize_text(record.get("product_name", ""))
        comp_key = f"{norm_state}::{norm_dist}::{norm_prod}"

        if comp_key in seen_composite_keys:
            duplicate_count += 1
            continue

        seen_composite_keys.add(comp_key)
        unique_records.append(record)

    return unique_records, duplicate_count
