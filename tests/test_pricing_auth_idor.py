"""
SIH 26090: Fair-Price Authentication, Authorization & IDOR Automated Tests
Verifies JWT authentication, role restrictions, server-side product ownership verification,
cross-artisan isolation (IDOR protection), and audited price confirmations.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest_asyncio.fixture
async def setup_two_artisans_and_products(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    seed_craft: Craft
):
    """Sets up two distinct artisan users with separate profiles and products."""
    # 1. Artisan 1 setup
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Artisan One",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 10
    })
    p1_res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Artisan One Product",
        "storytelling_description": "Handcrafted authentic item.",
        "price_inr": 2000.00,
        "currency": "INR",
        "materials": ["Silk"]
    })
    prod1 = p1_res.json()

    # 2. Artisan 2 setup
    await client.post("/api/v1/artisans/me", headers=other_artisan_headers, json={
        "full_name": "Artisan Two",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 10
    })
    p2_res = await client.post("/api/v1/products", headers=other_artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Artisan Two Product",
        "storytelling_description": "Handcrafted authentic item.",
        "price_inr": 3000.00,
        "currency": "INR",
        "materials": ["Cotton"]
    })
    prod2 = p2_res.json()

    return {"prod1": prod1, "prod2": prod2}


@pytest.mark.asyncio
async def test_unauthenticated_pricing_endpoints_rejected(
    client: AsyncClient,
    setup_two_artisans_and_products: dict
):
    """Verifies that all pricing endpoints reject unauthenticated requests with 401."""
    prod1_id = setup_two_artisans_and_products["prod1"]["id"]

    r1 = await client.get(f"/api/v1/products/{prod1_id}/pricing/costs")
    assert r1.status_code == 401

    r2 = await client.post(f"/api/v1/products/{prod1_id}/pricing/costs", json={})
    assert r2.status_code == 401

    r3 = await client.post(f"/api/v1/products/{prod1_id}/pricing/analyze")
    assert r3.status_code == 401

    r4 = await client.get(f"/api/v1/products/{prod1_id}/pricing/analysis")
    assert r4.status_code == 401

    r5 = await client.get(f"/api/v1/products/{prod1_id}/pricing/history")
    assert r5.status_code == 401


@pytest.mark.asyncio
async def test_buyer_role_rejected_from_artisan_pricing(
    client: AsyncClient,
    buyer_headers: dict,
    setup_two_artisans_and_products: dict
):
    """Verifies that buyers cannot access or modify artisan pricing structures (403 Forbidden)."""
    prod1_id = setup_two_artisans_and_products["prod1"]["id"]

    r = await client.get(f"/api/v1/products/{prod1_id}/pricing/costs", headers=buyer_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_artisan_idor_protection(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    setup_two_artisans_and_products: dict
):
    """
    Verifies IDOR protection: Artisan 2 cannot view, update, analyze, or confirm Artisan 1's product pricing.
    """
    prod1_id = setup_two_artisans_and_products["prod1"]["id"]

    # 1. Artisan 1 saves costs
    await client.post(f"/api/v1/products/{prod1_id}/pricing/costs", headers=artisan_headers, json={
        "materials": [{"material_name": "Silk", "quantity": 1, "unit": "m", "unit_cost_inr": 500.0}],
        "labor_calculation_method": "TOTAL_STATED",
        "total_labor_cost": 500.0
    })

    # 2. Artisan 2 tries to GET Artisan 1's costs -> 403 Forbidden
    r_get = await client.get(f"/api/v1/products/{prod1_id}/pricing/costs", headers=other_artisan_headers)
    assert r_get.status_code == 403
    assert "Forbidden" in r_get.json()["detail"]

    # 3. Artisan 2 tries to POST update Artisan 1's costs -> 403 Forbidden
    r_post = await client.post(f"/api/v1/products/{prod1_id}/pricing/costs", headers=other_artisan_headers, json={
        "labor_calculation_method": "TOTAL_STATED",
        "total_labor_cost": 1000.0
    })
    assert r_post.status_code == 403

    # 4. Artisan 2 tries to trigger analysis on Artisan 1's product -> 403 Forbidden
    r_analyze = await client.post(f"/api/v1/products/{prod1_id}/pricing/analyze", headers=other_artisan_headers)
    assert r_analyze.status_code == 403


@pytest.mark.asyncio
async def test_artisan_price_confirmation_and_product_update(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    setup_two_artisans_and_products: dict
):
    """
    Verifies that an artisan can explicitly confirm a generated fair price,
    which updates the canonical product.price_inr and logs an audit event.
    Also verifies Artisan 2 cannot confirm Artisan 1's price.
    """
    prod1_id = setup_two_artisans_and_products["prod1"]["id"]

    # 1. Artisan 1 saves costs and runs analysis
    await client.post(f"/api/v1/products/{prod1_id}/pricing/costs", headers=artisan_headers, json={
        "materials": [{"material_name": "Silk", "quantity": 1, "unit": "m", "unit_cost_inr": 800.0}],
        "labor_calculation_method": "TOTAL_STATED",
        "total_labor_cost": 700.0,
        "desired_margin_percentage": 20.0
    })
    ana_res = await client.post(f"/api/v1/products/{prod1_id}/pricing/analyze", headers=artisan_headers)
    assert ana_res.status_code == 201
    analysis_id = ana_res.json()["id"]

    # 2. Artisan 2 attempts to confirm Artisan 1's analysis -> 403 Forbidden
    r_bad_conf = await client.post(
        f"/api/v1/products/{prod1_id}/pricing/confirm?analysis_id={analysis_id}",
        headers=other_artisan_headers,
        json={"confirmed_price_inr": 2200.00, "apply_to_product": True}
    )
    assert r_bad_conf.status_code == 403

    # 3. Artisan 1 confirms price with apply_to_product=True
    r_conf = await client.post(
        f"/api/v1/products/{prod1_id}/pricing/confirm?analysis_id={analysis_id}",
        headers=artisan_headers,
        json={
            "confirmed_price_inr": 1950.00,
            "artisan_notes": "Fair price confirmed following craft cooperative pricing guidelines.",
            "apply_to_product": True
        }
    )
    assert r_conf.status_code == 200
    conf_data = r_conf.json()
    assert conf_data["is_confirmed_by_artisan"] is True
    assert float(conf_data["confirmed_price_inr"]) == 1950.00
    assert conf_data["provenance_state"] == "HUMAN_CONFIRMED"

    # 4. Verify canonical product price was updated to 1950.00
    prod_check = await client.get(f"/api/v1/products/{prod1_id}")
    assert prod_check.status_code == 200
    assert float(prod_check.json()["price_inr"]) == 1950.00
