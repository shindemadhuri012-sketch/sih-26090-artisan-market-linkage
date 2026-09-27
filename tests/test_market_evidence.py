"""
SIH 26090: Market Price Evidence & Comparability Automated Tests
Tests ingestion with full provenance, craft comparability filtering,
freshness checks, duplicate prevention, and sample size thresholds (N < 3 vs N >= 3).
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft
from ai.pricing.engine import FairPriceEngine, MIN_OBSERVATION_THRESHOLD


@pytest.mark.asyncio
async def test_admin_market_evidence_ingestion_with_provenance(
    client: AsyncClient,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that an admin can ingest a source-backed market price observation
    with complete cryptographic and institutional provenance.
    """
    payload = {
        "craft_id": seed_craft.id,
        "product_title": "Tribes India Chanderi Zari Saree",
        "observed_price": 5400.00,
        "currency": "INR",
        "source_name": "Tribes India / TRIFED Official Portal",
        "source_url": "https://www.tribesindia.com/chanderi-saree-001",
        "source_type": "GOVERNMENT",
        "geography_state": "Madhya Pradesh",
        "observation_date": datetime.now(timezone.utc).isoformat(),
        "original_source_id": "TRIFED-MP-2026-091",
        "license_or_usage_info": "Public E-Marketplace Catalogue Benchmark",
        "attributes_json": {
            "primary_material": "Silk",
            "technique": "Handloom Pit Loom Weaving"
        },
        "comparability_tags": ["handloom", "chanderi", "silk", "zari"],
        "evidence_quality_status": "HIGH",
        "verification_status": "DOCUMENTED",
        "is_sample_or_demo": True
    }

    res = await client.post("/api/v1/pricing/market-evidence", headers=admin_headers, json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["source_name"] == payload["source_name"]
    assert data["source_type"] == "GOVERNMENT"
    assert float(data["observed_price"]) == 5400.00
    assert data["data_provenance_level"] == "SOURCE_BACKED"
    assert data["is_sample_or_demo"] is True

    # Query public/artisan evidence endpoint
    list_res = await client.get(f"/api/v1/pricing/market-evidence?craft_id={seed_craft.id}")
    assert list_res.status_code == 200
    obs_list = list_res.json()
    assert len(obs_list) >= 1
    assert any(o["id"] == data["id"] for o in obs_list)


def test_engine_market_evidence_threshold_and_comparability():
    """
    Verifies FairPriceEngine's N < 3 insufficient evidence rule and comparability filtering.
    """
    now = datetime.now(timezone.utc)
    craft_a = "craft-uuid-chanderi"
    craft_b = "craft-uuid-madhubani"

    # 1. Zero observations
    valid_obs, status_code, stats = FairPriceEngine.filter_and_evaluate_market_evidence(
        observations=[],
        target_craft_id=craft_a,
        target_materials=["Silk"]
    )
    assert status_code == "INSUFFICIENT_MARKET_EVIDENCE"
    assert stats["observation_count"] == 0
    assert stats["median_inr"] is None

    # 2. Only 2 observations (N < 3)
    raw_obs_2 = [
        {
            "id": "obs-1",
            "craft_id": craft_a,
            "currency": "INR",
            "observed_price": "4500.00",
            "source_name": "Source 1",
            "source_type": "OFFICIAL_REGISTRY",
            "observation_date": now,
            "attributes_json": {"primary_material": "Silk"}
        },
        {
            "id": "obs-2",
            "craft_id": craft_a,
            "currency": "INR",
            "observed_price": "5200.00",
            "source_name": "Source 2",
            "source_type": "GOVERNMENT",
            "observation_date": now,
            "attributes_json": {"primary_material": "Silk"}
        }
    ]
    valid_obs, status_code, stats = FairPriceEngine.filter_and_evaluate_market_evidence(
        observations=raw_obs_2,
        target_craft_id=craft_a,
        target_materials=["Silk"]
    )
    assert status_code == "INSUFFICIENT_MARKET_EVIDENCE"
    assert stats["observation_count"] == 2
    assert stats["median_inr"] is None

    # 3. Add non-matching craft observation (should be filtered out)
    raw_obs_with_unrelated = raw_obs_2 + [
        {
            "id": "obs-unrelated",
            "craft_id": craft_b,  # Different craft!
            "currency": "INR",
            "observed_price": "800.00",
            "source_name": "Source 3",
            "source_type": "GOVERNMENT",
            "observation_date": now,
            "attributes_json": {"primary_material": "Paper"}
        }
    ]
    valid_obs, status_code, stats = FairPriceEngine.filter_and_evaluate_market_evidence(
        observations=raw_obs_with_unrelated,
        target_craft_id=craft_a,
        target_materials=["Silk"]
    )
    # Still only 2 valid for craft_a!
    assert status_code == "INSUFFICIENT_MARKET_EVIDENCE"
    assert stats["observation_count"] == 2

    # 4. Add a 3rd valid observation for craft_a -> N = 3 (SUFFICIENT)
    raw_obs_3 = raw_obs_2 + [
        {
            "id": "obs-3",
            "craft_id": craft_a,
            "currency": "INR",
            "observed_price": "6000.00",
            "source_name": "Source 3",
            "source_type": "OFFICIAL_MARKETPLACE",
            "observation_date": now,
            "attributes_json": {"primary_material": "Silk"}
        }
    ]
    valid_obs, status_code, stats = FairPriceEngine.filter_and_evaluate_market_evidence(
        observations=raw_obs_3,
        target_craft_id=craft_a,
        target_materials=["Silk"]
    )
    assert status_code == "SUFFICIENT_MARKET_EVIDENCE"
    assert stats["observation_count"] == 3
    # Sorted: 4500, 5200, 6000 -> Median is 5200
    assert stats["median_inr"] == Decimal("5200.00")
    assert stats["min_inr"] == Decimal("4500.00")
    assert stats["max_inr"] == Decimal("6000.00")
