"""
SIH 26090: Ingestion Validation Unit Tests
Verifies schema enforcement, geographic consistency, and error detection without silent dropping.
"""

from scripts.ingestion.common.validator import validate_gi_record, validate_odop_record


def test_valid_gi_record_passes():
    """Verify that a compliant GI record passes validation with zero issues."""
    record = {
        "name": "Kashmir Pashmina",
        "gi_tag_number": "GI-144",
        "origin_state": "Jammu & Kashmir",
        "origin_district": "Srinagar",
        "cultural_heritage_description": "Finest hand-spun and handwoven cashmere shawls from Changthangi mountain goat fleece.",
        "traditional_raw_materials": ["Pashm fleece", "Rice water starch"]
    }
    is_valid, issues = validate_gi_record(record)
    assert is_valid is True
    assert len(issues) == 0


def test_invalid_gi_record_missing_field():
    """Verify that a record missing required fields fails validation."""
    record = {
        "name": "Incomplete Craft",
        "gi_tag_number": "GI-999",
        "origin_state": "Rajasthan"
        # missing origin_district and cultural_heritage_description
    }
    is_valid, issues = validate_gi_record(record)
    assert is_valid is False
    assert any(i.field_name == "origin_district" for i in issues)
    assert any(i.field_name == "cultural_heritage_description" for i in issues)


def test_invalid_gi_tag_format():
    """Verify that invalid GI tag formatting is detected."""
    record = {
        "name": "Test Craft",
        "gi_tag_number": "INVALID_TAG_ABC",
        "origin_state": "Gujarat",
        "origin_district": "Kutch",
        "cultural_heritage_description": "Valid detailed cultural description spanning more than twenty characters."
    }
    is_valid, issues = validate_gi_record(record)
    assert is_valid is False
    assert any(i.issue_type == "INVALID_GI_TAG_FORMAT" for i in issues)


def test_invalid_state_geography():
    """Verify that invalid state names are flagged."""
    record = {
        "name": "Test Craft",
        "gi_tag_number": "GI-500",
        "origin_state": "NonExistentStateInIndia",
        "origin_district": "Central",
        "cultural_heritage_description": "Valid detailed cultural description spanning more than twenty characters."
    }
    is_valid, issues = validate_gi_record(record)
    assert is_valid is False
    assert any(i.issue_type == "INVALID_GEOGRAPHY" for i in issues)


def test_valid_odop_record_passes():
    """Verify that a compliant ODOP record passes validation."""
    record = {
        "state": "Uttar Pradesh",
        "district": "Moradabad",
        "product_name": "Brass Metal Handicrafts",
        "category": "Metalware"
    }
    is_valid, issues = validate_odop_record(record)
    assert is_valid is True
    assert len(issues) == 0
