"""
SIH 26090: Product Cost Structure Automated Tests
Tests itemized materials calculation, labor modes (hourly vs stated),
overhead allocation bases, batch quantities, and input validation rules.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest_asyncio.fixture
async def setup_product_for_artisan(client: AsyncClient, artisan_headers: dict, seed_craft: Craft):
    """Sets up an artisan profile and returns a created craft product."""
    # 1. Setup profile
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Madhav Rao",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    # 2. Create product
    res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Silk Dupatta",
        "storytelling_description": "Finely woven handloom silk dupatta with floral motifs.",
        "price_inr": 2500.00,
        "currency": "INR",
        "stock_quantity": 5,
        "monthly_production_capacity": 20,
        "min_order_quantity": 1,
        "lead_time_days": 5,
        "materials": ["Mulberry Silk", "Zari"],
        "primary_color": "Crimson"
    })
    assert res.status_code == 201
    return res.json()


@pytest.mark.asyncio
async def test_save_and_retrieve_cost_breakdown_hourly_labor(
    client: AsyncClient,
    artisan_headers: dict,
    setup_product_for_artisan: dict
):
    """
    Verifies saving structured cost breakdown with itemized materials and hourly labor calculation.
    Checks exact mathematical totals and retrieval.
    """
    prod_id = setup_product_for_artisan["id"]

    payload = {
        "materials": [
            {
                "material_name": "Mulberry Silk Yarn",
                "quantity": 2.5,
                "unit": "meters",
                "unit_cost_inr": 400.00,
                "source_type": "DOCUMENTED_INVOICE",
                "source_reference": "INV-2026-081"
            },
            {
                "material_name": "Pure Gold Zari Spool",
                "quantity": 1.0,
                "unit": "spool",
                "unit_cost_inr": 350.00,
                "source_type": "ARTISAN_ENTERED",
                "source_reference": None
            }
        ],
        "labor_calculation_method": "HOURLY_RATE",
        "labor_hours": 8.0,
        "hourly_labor_rate": 150.00,
        "packaging_cost": 80.00,
        "transport_cost": 120.00,
        "overhead_cost": 150.00,
        "overhead_allocation_basis": "PER_PRODUCT",
        "other_costs": 50.00,
        "other_costs_description": "Finishing and starching",
        "batch_quantity": 1,
        "currency": "INR",
        "desired_margin_percentage": 25.00
    }

    res = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json=payload)
    assert res.status_code == 200
    data = res.json()

    # Materials: (2.5 * 400 = 1000) + (1 * 350 = 350) = 1350.00
    assert float(data["total_material_cost"]) == 1350.00
    # Labor: 8 * 150 = 1200.00
    assert float(data["total_labor_cost"]) == 1200.00
    # Total production cost: 1350 + 1200 + 80 + 120 + 150 + 50 = 2950.00
    assert float(data["total_production_cost"]) == 2950.00
    assert float(data["cost_baseline_unit_cost"]) == 2950.00
    # Desired margin: 25% -> 2950 * 1.25 = 3687.50
    assert float(data["cost_baseline_recommended_price"]) == 3687.50
    assert data["provenance_status"] == "ARTISAN_PROVIDED"

    # Retrieve
    get_res = await client.get(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data["id"]
    assert float(get_res.json()["cost_baseline_unit_cost"]) == 2950.00


@pytest.mark.asyncio
async def test_save_cost_breakdown_total_stated_labor_and_batch_overhead(
    client: AsyncClient,
    artisan_headers: dict,
    setup_product_for_artisan: dict
):
    """
    Verifies TOTAL_STATED labor calculation and PER_BATCH overhead allocation for multi-unit batch.
    """
    prod_id = setup_product_for_artisan["id"]

    payload = {
        "materials": [
            {
                "material_name": "Clay & Mineral Pigments",
                "quantity": 10.0,
                "unit": "kg",
                "unit_cost_inr": 50.00,
                "source_type": "ARTISAN_ENTERED"
            }
        ],
        "labor_calculation_method": "TOTAL_STATED",
        "total_labor_cost": 1500.00,
        "packaging_cost": 100.00,
        "transport_cost": 200.00,
        "overhead_cost": 600.00,
        "overhead_allocation_basis": "PER_BATCH",
        "batch_quantity": 5,
        "currency": "INR",
        "desired_margin_percentage": 20.00
    }

    res = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json=payload)
    assert res.status_code == 200
    data = res.json()

    # Materials: 10 * 50 = 500.00
    assert float(data["total_material_cost"]) == 500.00
    # Labor stated: 1500.00
    assert float(data["total_labor_cost"]) == 1500.00
    # Direct costs + batch overhead: 500 + 1500 + 100 + 200 + 600 = 2900.00 for batch of 5
    assert float(data["total_production_cost"]) == 2900.00
    # Unit cost: 2900 / 5 = 580.00
    assert float(data["cost_baseline_unit_cost"]) == 580.00
    # Desired margin: 20% -> 580 * 1.20 = 696.00
    assert float(data["cost_baseline_recommended_price"]) == 696.00


@pytest.mark.asyncio
async def test_cost_breakdown_validation_errors(
    client: AsyncClient,
    artisan_headers: dict,
    setup_product_for_artisan: dict
):
    """
    Verifies that invalid costs, negative numbers, and invalid parameters are rejected with 422.
    """
    prod_id = setup_product_for_artisan["id"]

    # Negative material unit cost
    r1 = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json={
        "materials": [{"material_name": "Silk", "quantity": 1, "unit": "m", "unit_cost_inr": -100.0}]
    })
    assert r1.status_code == 422

    # Negative material quantity
    r2 = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json={
        "materials": [{"material_name": "Silk", "quantity": -2, "unit": "m", "unit_cost_inr": 100.0}]
    })
    assert r2.status_code == 422

    # Batch quantity < 1
    r3 = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json={
        "batch_quantity": 0
    })
    assert r3.status_code == 422

    # Invalid labor calculation method
    r4 = await client.post(f"/api/v1/products/{prod_id}/pricing/costs", headers=artisan_headers, json={
        "labor_calculation_method": "AI_ESTIMATE"
    })
    assert r4.status_code == 422
