"""
SIH 26090: AI Product Studio Media Validation Tests
Verifies input validation on product media before passing to AI vision providers.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_ai_studio_rejects_unrelated_or_non_image_media(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that AI analysis requests are rejected when:
    1. The media does not belong to the specified product (404 Not Found).
    2. The media is not an image (e.g. document/PDF) (400 Bad Request).
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    # Create Product A
    r_prod_a = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Saree A",
        "storytelling_description": "First product listing.",
        "price_inr": 3500.0,
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    prod_a_id = r_prod_a.json()["id"]

    # Create Product B
    r_prod_b = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Saree B",
        "storytelling_description": "Second product listing.",
        "price_inr": 3800.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    prod_b_id = r_prod_b.json()["id"]

    # Attach image media to Product B
    r_media_b = await client.post(f"/api/v1/products/{prod_b_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/b.jpg",
        "original_filename": "b.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg"
    })
    media_b_id = r_media_b.json()["id"]

    # Attach document (PDF) to Product A
    r_doc_a = await client.post(f"/api/v1/products/{prod_a_id}/media", headers=artisan_headers, json={
        "media_type": "DOCUMENT",
        "url": "https://storage.artisanmarket.gov.in/products/spec.pdf",
        "original_filename": "spec.pdf",
        "file_size_bytes": 50000,
        "mime_type": "application/pdf"
    })
    doc_a_id = r_doc_a.json()["id"]

    # 1. Request AI analysis on Product A using Media B (unrelated media) -> 404
    r_unrelated = await client.post(
        f"/api/v1/products/{prod_a_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_b_id, "provider_override": "mock"}
    )
    assert r_unrelated.status_code == 404
    assert "does not belong to this product" in r_unrelated.json()["detail"]

    # 2. Request AI analysis on Product A using document (PDF) -> 400
    r_non_image = await client.post(
        f"/api/v1/products/{prod_a_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": doc_a_id, "provider_override": "mock"}
    )
    assert r_non_image.status_code == 400
    assert "non-image" in r_non_image.json()["detail"]
