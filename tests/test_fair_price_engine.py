"""
SIH 26090: Fair Price Engine Automated Tests
Tests FAIR_PRICE_ENGINE_V1 deterministic synthesis, cost-only baseline under N < 3,
evidence-based fair price ranges under N >= 3, historical versioning, and explanation generation.
"""

from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest_asyncio.fixture
async def setup_artisan_product_with_costs(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
) -> dict:
    """Sets up an artisan profile, creates a product, and saves initial production costs."""
    # 1. Profile
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Devi Sharma",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })

    # 2. Product
    prod_res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Traditional Silk Zari Saree",
        "storytelling_description": "Hand-spun silk saree with authentic gold border.",
        "price_inr": 3800.00,  # Note: 3800 current selling price
        "currency": "INR",
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 10,
        "materials": ["Mulberry Silk", "Zari"],
        "primary_color": "Royal Blue"
    })
    product = prod_res.json()

    # 3. Cost breakdown:
    # Materials: 2200.00
    # Labor: 12 hrs @ 150 = 1800.00
    # Packaging: 100.00
    # Transport: 150.00
    # Overhead: 250.00
    # Total production cost = 2200 + 1800 + 100 + 150 + 250 = 4500.00
    # Desired margin: 25% -> Cost baseline price = 4500 * 1.25 = 5625.00
    cost_payload = {
        "materials": [
            {"material_name": "Mulberry Silk", "quantity": 5.5, "unit": "meters", "unit_cost_inr": 400.00}
        ],
        "labor_calculation_method": "HOURLY_RATE",
        "labor_hours": 12.0,
        "hourly_labor_rate": 150.00,
        "packaging_cost": 100.00,
        "transport_cost": 150.00,
        "overhead_cost": 250.00,
        "overhead_allocation_basis": "PER_PRODUCT",
        "batch_quantity": 1,
        "current_selling_price": 3800.00,
        "desired_margin_percentage": 25.00
    }
    await client.post(f"/api/v1/products/{product['id']}/pricing/costs", headers=artisan_headers, json=cost_payload)

    return product


@pytest.mark.asyncio
async def test_fair_price_analysis_cost_only_baseline_when_no_market_evidence(
    client: AsyncClient,
    artisan_headers: dict,
    setup_artisan_product_with_costs: dict
):
    """
    Verifies that when market evidence is empty (< 3 observations), the engine
    strictly produces a COST_ONLY_BASELINE without fabricating market numbers.
    """
    prod_id = setup_artisan_product_with_costs["id"]

    res = await client.post(f"/api/v1/products/{prod_id}/pricing/analyze", headers=artisan_headers)
    assert res.status_code == 201
    data = res.json()

    assert data["engine_version"] == "FAIR_PRICE_ENGINE_V1"
    assert data["evidence_status"] == "INSUFFICIENT_MARKET_EVIDENCE"
    assert data["provenance_state"] == "CALCULATED"

    # Cost baseline values
    assert float(data["cost_baseline"]["unit_production_cost"]) == 4500.00
    assert float(data["cost_baseline"]["cost_baseline_price"]) == 5625.00

    # Market evidence must have NO fabricated numbers
    assert data["market_evidence"]["observation_count"] == 0
    assert data["market_evidence"]["median_inr"] is None
    assert data["market_evidence"]["min_inr"] is None
    assert data["market_evidence"]["max_inr"] is None

    # Recommendations under cost-only baseline
    assert float(data["fair_price_analysis"]["floor_price"]) == 4500.00
    assert float(data["fair_price_analysis"]["recommended_price"]) == 5625.00

    # Verify structured explanation steps exist
    steps = data["explanation_steps"]
    assert len(steps) >= 4
    # Step 4 must explain insufficient evidence
    assert any("insufficient" in s["detail"].lower() for s in steps)
    # Current selling price was 3800, which is below cost 4500 -> must contain warning step
    assert any("warning" in s["title"].lower() or "loss" in s["detail"].lower() for s in steps)


@pytest.mark.asyncio
async def test_fair_price_analysis_with_sufficient_market_evidence(
    client: AsyncClient,
    admin_headers: dict,
    artisan_headers: dict,
    seed_craft: Craft,
    setup_artisan_product_with_costs: dict
):
    """
    Verifies full FAIR_PRICE_ANALYSIS when sufficient comparable observations (N >= 3) exist.
    Checks median, IQR, floor price floor protection, and historical preservation.
    """
    prod_id = setup_artisan_product_with_costs["id"]
    now = datetime.now(timezone.utc)

    # Ingest 4 comparable market observations (4800, 5200, 5800, 6400)
    prices = [4800.00, 5200.00, 5800.00, 6400.00]
    for i, p in enumerate(prices):
        await client.post("/api/v1/pricing/market-evidence", headers=admin_headers, json={
            "craft_id": seed_craft.id,
            "product_title": f"Documented Chanderi Benchmark {i+1}",
            "observed_price": p,
            "currency": "INR",
            "source_name": f"Official Source {i+1}",
            "source_type": "GOVERNMENT" if i % 2 == 0 else "OFFICIAL_REGISTRY",
            "observation_date": now.isoformat(),
            "attributes_json": {"primary_material": "Mulberry Silk"},
            "evidence_quality_status": "HIGH",
            "is_sample_or_demo": True
        })

    # Run price analysis
    res = await client.post(f"/api/v1/products/{prod_id}/pricing/analyze", headers=artisan_headers)
    assert res.status_code == 201
    data = res.json()

    assert data["evidence_status"] == "SUFFICIENT_MARKET_EVIDENCE"
    assert data["market_evidence"]["observation_count"] == 4
    # Median of [4800, 5200, 5800, 6400] is (5200 + 5800) / 2 = 5500.00
    assert float(data["market_evidence"]["median_inr"]) == 5500.00
    assert float(data["market_evidence"]["min_inr"]) == 4800.00
    assert float(data["market_evidence"]["max_inr"]) == 6400.00

    # Cost baseline price is 5625.00, Market median is 5500.00
    # Recommended price = max(cost_baseline, median) = max(5625, 5500) = 5625.00
    # Floor price = max(unit_cost 4500, min(cost_baseline 5625, q1 4800)) = 4800.00 (or unit_cost 4500)
    assert float(data["fair_price_analysis"]["floor_price"]) >= 4500.00
    assert float(data["fair_price_analysis"]["recommended_price"]) == 5625.00

    # Re-run analysis a second time to verify historical persistence
    res2 = await client.post(f"/api/v1/products/{prod_id}/pricing/analyze", headers=artisan_headers)
    assert res2.status_code == 201

    # Verify history preservation: We ran analysis twice, so history must have at least 2 entries
    hist_res = await client.get(f"/api/v1/products/{prod_id}/pricing/history", headers=artisan_headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 2
    # Verify both have version FAIR_PRICE_ENGINE_V1
    assert all(h["engine_version"] == "FAIR_PRICE_ENGINE_V1" for h in history)
