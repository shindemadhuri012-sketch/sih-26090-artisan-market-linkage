"""
SIH 26090: Ingestion Record Validator
Enforces schema compliance, validates geographic values, and flags data anomalies without silent dropping.
"""

from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    record_identifier: str
    field_name: str
    issue_type: str
    message: str


class ValidationSummary(BaseModel):
    total_inspected: int = 0
    total_valid: int = 0
    total_invalid: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)


VALID_INDIAN_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Jammu & Kashmir", "Ladakh", "Delhi", "Puducherry", "Chandigarh"
}


def validate_gi_record(record: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
    """Validates an authentic Geographical Indication record."""
    issues: List[ValidationIssue] = []
    ident = str(record.get("gi_tag_number") or record.get("name") or "UNKNOWN")

    # 1. Check required fields
    for req in ["name", "gi_tag_number", "origin_state", "origin_district", "cultural_heritage_description"]:
        val = record.get(req)
        if not val or not str(val).strip():
            issues.append(ValidationIssue(
                record_identifier=ident,
                field_name=req,
                issue_type="MISSING_REQUIRED_FIELD",
                message=f"Field '{req}' cannot be null or empty."
            ))

    # 2. Check GI Tag number format
    gi_tag = str(record.get("gi_tag_number", "")).strip()
    if gi_tag and not gi_tag.replace("GI-", "").isdigit():
        issues.append(ValidationIssue(
            record_identifier=ident,
            field_name="gi_tag_number",
            issue_type="INVALID_GI_TAG_FORMAT",
            message=f"GI tag number '{gi_tag}' does not conform to standard format (GI-### or digits)."
        ))

    # 3. Check State validity
    state = str(record.get("origin_state", "")).strip()
    if state and state not in VALID_INDIAN_STATES:
        issues.append(ValidationIssue(
            record_identifier=ident,
            field_name="origin_state",
            issue_type="INVALID_GEOGRAPHY",
            message=f"State '{state}' is not recognized in official Indian states list."
        ))

    # 4. Description length check
    desc = str(record.get("cultural_heritage_description", "")).strip()
    if desc and len(desc) < 20:
        issues.append(ValidationIssue(
            record_identifier=ident,
            field_name="cultural_heritage_description",
            issue_type="INSUFFICIENT_DESCRIPTION",
            message="Cultural heritage description is too brief (minimum 20 characters required)."
        ))

    return len(issues) == 0, issues


def validate_odop_record(record: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
    """Validates an authentic One District One Product record."""
    issues: List[ValidationIssue] = []
    ident = f"{record.get('district', '')}-{record.get('product_name', '')}"

    for req in ["state", "district", "product_name", "category"]:
        val = record.get(req)
        if not val or not str(val).strip():
            issues.append(ValidationIssue(
                record_identifier=ident,
                field_name=req,
                issue_type="MISSING_REQUIRED_FIELD",
                message=f"Field '{req}' cannot be null or empty."
            ))

    state = str(record.get("state", "")).strip()
    if state and state not in VALID_INDIAN_STATES:
        issues.append(ValidationIssue(
            record_identifier=ident,
            field_name="state",
            issue_type="INVALID_GEOGRAPHY",
            message=f"State '{state}' is not recognized in official Indian states list."
        ))

    return len(issues) == 0, issues
