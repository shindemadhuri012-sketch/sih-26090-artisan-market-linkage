"""
SIH 26090: Demand Observations & Aggregations Unit Tests
Verifies observation ingestion, validation, provenance tags, role-based authorization,
and deterministic demand summary rollups.
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient

from backend.app.models.auth import User
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_admin_can_record_demand_observation(
    client: AsyncClient,
    admin_headers: dict,
    seed_craft: Craft
):
    """Verifies that admins can ingest verified demand observations with provenance."""
    start = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    end = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    payload = {
        "craft_id": seed_craft.id,
        "craft_category_id": seed_craft.category_id,
        "geography_state": "Madhya Pradesh",
        "observation_period_start": start,
        "observation_period_end": end,
        "total_enquiries": 15,
        "fulfilled_orders": 8,
        "unit_volume": 250,
        "monetary_volume_inr": 450000.00,
        "average_realized_price": 1800.00,
        "seasonal_festival_tag": "Diwali Pre-Orders",
        "signal_tier": "TRANSACTIONAL_CONFIRMED",
        "observation_type": "GOVERNMENT_REGISTRY",
        "data_quality_status": "VERIFIED",
        "is_sample_or_demo": False
    }

    res = await client.post("/api/v1/demand/observations", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["craft_id"] == seed_craft.id
    assert data["geography_state"] == "Madhya Pradesh"
    assert data["unit_volume"] == 250
    assert data["signal_tier"] == "TRANSACTIONAL_CONFIRMED"
    assert data["is_sample_or_demo"] is False
    assert data["data_provenance_level"] == "VERIFIED_EXTERNAL_SOURCE"


@pytest.mark.asyncio
async def test_artisan_and_buyer_forbidden_from_ingesting_demand(
    client: AsyncClient,
    artisan_headers: dict,
    buyer_headers: dict,
    seed_craft: Craft
):
    """Verifies RBAC protection: only admins can ingest demand observations."""
    start = datetime.now(timezone.utc).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    payload = {
        "craft_id": seed_craft.id,
        "geography_state": "Rajasthan",
        "observation_period_start": start,
        "observation_period_end": end,
        "unit_volume": 100
    }

    art_res = await client.post("/api/v1/demand/observations", json=payload, headers=artisan_headers)
    assert art_res.status_code == 403

    buy_res = await client.post("/api/v1/demand/observations", json=payload, headers=buyer_headers)
    assert buy_res.status_code == 403


@pytest.mark.asyncio
async def test_demand_summary_deterministic_aggregation(
    client: AsyncClient,
    admin_headers: dict,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that GET /api/v1/demand/summary aggregates unit volume, enquiries, and orders correctly."""
    now = datetime.now(timezone.utc)

    # Ingest 2 distinct real observations
    p1 = {
        "craft_id": seed_craft.id,
        "craft_category_id": seed_craft.category_id,
        "geography_state": "Madhya Pradesh",
        "observation_period_start": (now - timedelta(days=90)).isoformat(),
        "observation_period_end": (now - timedelta(days=61)).isoformat(),
        "total_enquiries": 10,
        "fulfilled_orders": 5,
        "unit_volume": 120,
        "monetary_volume_inr": 240000.00,
        "is_sample_or_demo": False
    }
    p2 = {
        "craft_id": seed_craft.id,
        "craft_category_id": seed_craft.category_id,
        "geography_state": "Madhya Pradesh",
        "observation_period_start": (now - timedelta(days=60)).isoformat(),
        "observation_period_end": (now - timedelta(days=31)).isoformat(),
        "total_enquiries": 20,
        "fulfilled_orders": 12,
        "unit_volume": 280,
        "monetary_volume_inr": 560000.00,
        "is_sample_or_demo": False
    }
    # Ingest 1 sample/demo observation (must be excluded from real aggregation)
    p_demo = {
        "craft_id": seed_craft.id,
        "craft_category_id": seed_craft.category_id,
        "geography_state": "Madhya Pradesh",
        "observation_period_start": (now - timedelta(days=30)).isoformat(),
        "observation_period_end": now.isoformat(),
        "total_enquiries": 999,
        "fulfilled_orders": 999,
        "unit_volume": 99999,
        "monetary_volume_inr": 9999999.00,
        "is_sample_or_demo": True
    }

    await client.post("/api/v1/demand/observations", json=p1, headers=admin_headers)
    await client.post("/api/v1/demand/observations", json=p2, headers=admin_headers)
    await client.post("/api/v1/demand/observations", json=p_demo, headers=admin_headers)

    # Query summary as authenticated artisan
    summary_res = await client.get(
        f"/api/v1/demand/summary?craft_id={seed_craft.id}&geography_state=Madhya Pradesh",
        headers=artisan_headers
    )
    assert summary_res.status_code == 200
    data = summary_res.json()

    assert data["craft_id"] == seed_craft.id
    assert data["total_observations"] == 2  # Demo record excluded
    assert data["total_unit_volume"] == 400  # 120 + 280
    assert float(data["total_monetary_volume_inr"]) == 800000.00  # 240,000 + 560,000
    assert data["total_enquiries"] == 30  # 10 + 20
    assert data["total_fulfilled_orders"] == 17  # 5 + 12
    assert data["data_sufficiency_state"] == "INSUFFICIENT_DATA"  # < 3 observations
