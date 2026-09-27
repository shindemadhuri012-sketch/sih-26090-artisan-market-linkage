"""
SIH 26090: Governance Flags & Dashboard Tests
Verifies neutral review signal creation, duplicate prevention,
resolution workflows, and factual dashboard metrics.
"""

import pytest
import uuid
from httpx import AsyncClient
from backend.app.models.auth import User
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_raise_and_resolve_governance_flag(
    client: AsyncClient,
    admin_headers: dict
):
    """
    Tests raising a neutral review signal, preventing duplicate open flags,
    and resolving it with an audited explanation.
    """
    prod_id = str(uuid.uuid4())

    # 1. Raise a flag
    res1 = await client.post(
        "/api/v1/governance/flags",
        headers=admin_headers,
        json={
            "entity_type": "Product",
            "entity_id": prod_id,
            "flag_type": "PRICE_ANOMALY_REVIEW",
            "severity": "MEDIUM",
            "details_json": {"stated_price": 15000, "cluster_median": 2200}
        }
    )
    assert res1.status_code == 201
    flag_data1 = res1.json()
    assert flag_data1["flag_type"] == "PRICE_ANOMALY_REVIEW"
    assert flag_data1["status"] == "OPEN"
    flag_id = flag_data1["id"]

    # 2. Raising identical flag on same entity does not duplicate
    res2 = await client.post(
        "/api/v1/governance/flags",
        headers=admin_headers,
        json={
            "entity_type": "Product",
            "entity_id": prod_id,
            "flag_type": "PRICE_ANOMALY_REVIEW",
            "severity": "MEDIUM",
            "details_json": {"stated_price": 15000, "updated_check": True}
        }
    )
    assert res2.status_code == 201
    assert res2.json()["id"] == flag_id

    # 3. List flags
    list_res = await client.get("/api/v1/governance/flags?severity=MEDIUM", headers=admin_headers)
    assert list_res.status_code == 200
    flag_ids = [f["id"] for f in list_res.json()["items"]]
    assert flag_id in flag_ids

    # 4. Resolve flag
    resolve_res = await client.post(
        f"/api/v1/governance/flags/{flag_id}/resolve",
        headers=admin_headers,
        json={
            "decision": "RESOLVED_VALIDATED",
            "resolution_notes": "Artisan uses pure gold zari and natural mulberry silk; premium pricing validated."
        }
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED_VALIDATED"
    assert "pure gold zari" in resolve_res.json()["resolution_notes"]


@pytest.mark.asyncio
async def test_governance_dashboard_metrics(
    client: AsyncClient,
    admin_headers: dict
):
    """
    Tests that the dashboard outputs real, factual counts without synthetic or arbitrary trust scores.
    """
    res = await client.get("/api/v1/governance/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert "pending_product_reviews" in data
    assert "pending_verification_reviews" in data
    assert "pending_passport_reviews" in data
    assert "open_flags_total" in data
    assert "open_flags_by_severity" in data
    assert "HIGH" in data["open_flags_by_severity"]
    assert "ai_suggestions_awaiting_review" in data
    assert "active_demo_records_count" in data
    # Ensure no fabricated score keys exist
    assert "trust_score" not in data
    assert "reputation_index" not in data
