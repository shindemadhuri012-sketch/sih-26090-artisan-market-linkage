"""
SIH 26090: Product Authorization & IDOR Defense Automated Tests
Verifies server-side ownership enforcement across all product operations,
preventing Insecure Direct Object References (IDOR), and checks role boundaries.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_artisan_idor_prevention_on_update_and_delete(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that Artisan 2 cannot update, delete, or modify Artisan 1's products.
    Must return 403 Forbidden.
    """
    # 1. Setup profiles for Artisan 1 and Artisan 2
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Artisan Primary",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    await client.post("/api/v1/artisans/me", headers=other_artisan_headers, json={
        "full_name": "Artisan Secondary",
        "state": "Rajasthan",
        "district": "Jaipur",
        "pincode": "302001",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })

    # 2. Artisan 1 creates a product
    r_create = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Master Artisan Saree",
        "storytelling_description": "Exquisite handmade masterpiece.",
        "price_inr": 6500.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 8,
        "min_order_quantity": 1,
        "lead_time_days": 10
    })
    assert r_create.status_code == 201
    prod_id = r_create.json()["id"]

    # 3. Artisan 2 tries to update Artisan 1's product -> 403 Forbidden
    r_update_idor = await client.put(
        f"/api/v1/products/{prod_id}",
        headers=other_artisan_headers,
        json={"title": "Hacked Title by Competitor", "price_inr": 100.0}
    )
    assert r_update_idor.status_code == 403
    assert "Access denied" in r_update_idor.json()["detail"]

    # 4. Artisan 2 tries to submit Artisan 1's product -> 403 Forbidden
    r_submit_idor = await client.post(
        f"/api/v1/products/{prod_id}/submit",
        headers=other_artisan_headers
    )
    assert r_submit_idor.status_code == 403

    # 5. Artisan 2 tries to delete Artisan 1's product -> 403 Forbidden
    r_del_idor = await client.delete(
        f"/api/v1/products/{prod_id}",
        headers=other_artisan_headers
    )
    assert r_del_idor.status_code == 403

    # 6. Verify product was NOT modified or deleted
    r_my_prods = await client.get("/api/v1/artisans/me/products", headers=artisan_headers)
    assert r_my_prods.status_code == 200
    assert any(p["id"] == prod_id and p["title"] == "Master Artisan Saree" for p in r_my_prods.json())


@pytest.mark.asyncio
async def test_artisan_idor_prevention_on_media_operations(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that Artisan 2 cannot attach media to or delete media from Artisan 1's products.
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Artisan Primary",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    await client.post("/api/v1/artisans/me", headers=other_artisan_headers, json={
        "full_name": "Artisan Secondary",
        "state": "Rajasthan",
        "district": "Jaipur",
        "pincode": "302001",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })

    # Artisan 1 creates product
    r_create = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Scarf",
        "storytelling_description": "Delicate handloom scarf.",
        "price_inr": 1200.0,
        "stock_quantity": 10,
        "monthly_production_capacity": 50,
        "min_order_quantity": 2,
        "lead_time_days": 3
    })
    prod_id = r_create.json()["id"]

    # Artisan 1 attaches legitimate media
    r_media = await client.post(
        f"/api/v1/products/{prod_id}/media",
        headers=artisan_headers,
        json={
            "media_type": "IMAGE",
            "url": "https://storage.artisanmarket.gov.in/products/scarf_1.jpg",
            "original_filename": "scarf_1.jpg",
            "file_size_bytes": 102400,
            "mime_type": "image/jpeg"
        }
    )
    assert r_media.status_code == 201
    media_id = r_media.json()["id"]

    # Artisan 2 attempts to upload media to Artisan 1's product -> 403 Forbidden
    r_media_idor = await client.post(
        f"/api/v1/products/{prod_id}/media",
        headers=other_artisan_headers,
        json={
            "media_type": "IMAGE",
            "url": "https://malicious.org/fake.jpg",
            "original_filename": "fake.jpg",
            "file_size_bytes": 50000,
            "mime_type": "image/jpeg"
        }
    )
    assert r_media_idor.status_code == 403

    # Artisan 2 attempts to delete Artisan 1's media asset -> 403 Forbidden
    r_del_media_idor = await client.delete(
        f"/api/v1/products/{prod_id}/media/{media_id}",
        headers=other_artisan_headers
    )
    assert r_del_media_idor.status_code == 403


@pytest.mark.asyncio
async def test_role_boundaries_buyer_and_artisan(
    client: AsyncClient,
    buyer_headers: dict,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies role privilege boundaries:
    - Buyers cannot create products (403 Forbidden)
    - Artisans cannot access admin moderation queue (403 Forbidden)
    - Artisans cannot approve products (403 Forbidden)
    """
    # 1. Buyer attempts to create product -> 403 Forbidden
    r_buyer_create = await client.post("/api/v1/products", headers=buyer_headers, json={
        "craft_id": seed_craft.id,
        "title": "Unauthorized Listing",
        "storytelling_description": "Buyer should not be allowed to list products.",
        "price_inr": 2000.0,
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    assert r_buyer_create.status_code == 403

    # 2. Artisan attempts to view admin moderation queue -> 403 Forbidden
    r_art_pending = await client.get("/api/v1/products/admin/pending", headers=artisan_headers)
    assert r_art_pending.status_code == 403

    # 3. Artisan attempts to self-approve product -> 403 Forbidden
    r_art_approve = await client.post(
        f"/api/v1/products/admin/{seed_craft.id}/review",
        headers=artisan_headers,
        json={"decision": "APPROVE"}
    )
    assert r_art_approve.status_code == 403
