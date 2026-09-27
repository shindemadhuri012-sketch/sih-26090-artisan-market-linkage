"""
SIH 26090: Product Media Security & Validation Automated Tests
Tests product media metadata handling, MIME validation, file size limits,
filename path-traversal safety, and owner media management.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_product_media_creation_and_attributes(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that an artisan can attach valid image media with metadata:
    dimensions, primary status, sha256 checksum, and alt text.
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Saree",
        "storytelling_description": "Finely woven with silk warp and cotton weft.",
        "price_inr": 5000.0,
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 10
    })
    prod_id = r_prod.json()["id"]

    media_payload = {
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/chanderi_front.webp",
        "thumbnail_url": "https://storage.artisanmarket.gov.in/products/chanderi_front_thumb.webp",
        "storage_key": "products/2026/03/chanderi_front.webp",
        "original_filename": "chanderi_front.webp",
        "file_size_bytes": 450000,
        "mime_type": "image/webp",
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "width": 1920,
        "height": 1080,
        "sort_order": 0,
        "alt_text": "High resolution close-up of golden zari pallu on Chanderi silk",
        "is_primary": True
    }

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json=media_payload)
    assert r_media.status_code == 201
    media = r_media.json()
    assert media["mime_type"] == "image/webp"
    assert media["is_primary"] is True
    assert media["width"] == 1920
    assert media["height"] == 1080
    assert media["original_filename"] == "chanderi_front.webp"
    assert media["checksum_sha256"] == media_payload["checksum_sha256"]


@pytest.mark.asyncio
async def test_product_media_mime_and_size_validation(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies security validation on uploaded media metadata:
    - Disallows executable or dangerous MIME types (e.g. application/x-executable, text/html)
    - Rejects payloads exceeding the 10MB maximum file size limit
    - Blocks path traversal strings in filenames
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Saree",
        "storytelling_description": "Finely woven with silk warp and cotton weft.",
        "price_inr": 5000.0,
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 10
    })
    prod_id = r_prod.json()["id"]

    # 1. Invalid MIME type (HTML script injection attempt) -> 422
    bad_mime = {
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/malicious.html",
        "original_filename": "malicious.html",
        "file_size_bytes": 1024,
        "mime_type": "text/html"
    }
    r_bad_mime = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json=bad_mime)
    assert r_bad_mime.status_code == 422

    # 2. File size exceeding 10MB (10485760 bytes) -> 422
    huge_file = {
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/huge.jpg",
        "original_filename": "huge.jpg",
        "file_size_bytes": 15 * 1024 * 1024,  # 15MB
        "mime_type": "image/jpeg"
    }
    r_huge = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json=huge_file)
    assert r_huge.status_code == 422

    # 3. Path traversal in filename -> 422
    traversal_file = {
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/photo.jpg",
        "original_filename": "../../../etc/passwd",
        "file_size_bytes": 50000,
        "mime_type": "image/jpeg"
    }
    r_traversal = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json=traversal_file)
    assert r_traversal.status_code == 422


@pytest.mark.asyncio
async def test_owner_media_deletion(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that the product owner can successfully delete their media assets."""
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Saree",
        "storytelling_description": "Finely woven with silk warp and cotton weft.",
        "price_inr": 5000.0,
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 10
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/delete_me.png",
        "original_filename": "delete_me.png",
        "file_size_bytes": 10240,
        "mime_type": "image/png"
    })
    media_id = r_media.json()["id"]

    # Delete media
    r_del = await client.delete(f"/api/v1/products/{prod_id}/media/{media_id}", headers=artisan_headers)
    assert r_del.status_code == 200

    # Repeat delete returns 404
    r_del_again = await client.delete(f"/api/v1/products/{prod_id}/media/{media_id}", headers=artisan_headers)
    assert r_del_again.status_code == 404
