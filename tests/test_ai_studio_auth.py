"""
SIH 26090: AI Product Studio Authentication & IDOR Defense Tests
Verifies that unauthenticated users and buyers cannot invoke AI studio endpoints,
and that strict server-side ownership prevents cross-artisan tampering.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_ai_studio_unauthenticated_and_buyer_rejected(
    client: AsyncClient,
    buyer_headers: dict,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies authentication and role-based permissions:
    - Unauthenticated calls return 401 Unauthorized.
    - Buyer calls return 403 Forbidden.
    """
    # 1. Setup artisan and product
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Silk Saree",
        "storytelling_description": "Hand-woven silk saree.",
        "price_inr": 4500.0,
        "stock_quantity": 4,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    prod_id = r_prod.json()["id"]

    # 2. Unauthenticated request -> 401
    r_unauth = await client.post(f"/api/v1/products/{prod_id}/ai/analyze", json={
        "media_id": "00000000-0000-0000-0000-000000000000"
    })
    assert r_unauth.status_code == 401

    # 3. Buyer role cannot invoke AI Studio -> 403
    r_buyer = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=buyer_headers,
        json={"media_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert r_buyer.status_code == 403


@pytest.mark.asyncio
async def test_ai_studio_idor_cross_artisan_protection(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies server-side IDOR defense:
    Artisan 2 cannot analyze, view, confirm, or reject Artisan 1's products or suggestions.
    """
    # Setup Artisan 1
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Artisan Primary",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    # Setup Artisan 2
    await client.post("/api/v1/artisans/me", headers=other_artisan_headers, json={
        "full_name": "Artisan Competitor",
        "state": "Rajasthan",
        "district": "Jaipur",
        "pincode": "302001",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })

    # Artisan 1 creates product and media
    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Masterpiece Weave",
        "storytelling_description": "Authentic master weave.",
        "price_inr": 8000.0,
        "stock_quantity": 2,
        "monthly_production_capacity": 5,
        "min_order_quantity": 1,
        "lead_time_days": 14
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/master.jpg",
        "original_filename": "master.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg"
    })
    media_id = r_media.json()["id"]

    # Artisan 1 runs AI analysis using mock provider
    r_analysis = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    assert r_analysis.status_code == 201
    analysis_id = r_analysis.json()["id"]

    # 1. Artisan 2 attempts to analyze Artisan 1's product -> 403 Forbidden
    r_idor_analyze = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=other_artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    assert r_idor_analyze.status_code == 403
    assert "Access denied" in r_idor_analyze.json()["detail"]

    # 2. Artisan 2 attempts to list Artisan 1's analyses -> 403 Forbidden
    r_idor_list = await client.get(
        f"/api/v1/products/{prod_id}/ai/analyses",
        headers=other_artisan_headers
    )
    assert r_idor_list.status_code == 403

    # 3. Artisan 2 attempts to retrieve Artisan 1's analysis by ID -> 403 Forbidden
    r_idor_get = await client.get(
        f"/api/v1/products/{prod_id}/ai/analyses/{analysis_id}",
        headers=other_artisan_headers
    )
    assert r_idor_get.status_code == 403

    # 4. Artisan 2 attempts to confirm Artisan 1's suggestions -> 403 Forbidden
    r_idor_confirm = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyses/{analysis_id}/confirm",
        headers=other_artisan_headers,
        json={"confirmations": [{"field_name": "materials", "action": "ACCEPT"}]}
    )
    assert r_idor_confirm.status_code == 403

    # 5. Artisan 2 attempts to reject Artisan 1's analysis -> 403 Forbidden
    r_idor_reject = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyses/{analysis_id}/reject",
        headers=other_artisan_headers,
        json={"reason": "Malicious competitor rejection"}
    )
    assert r_idor_reject.status_code == 403
