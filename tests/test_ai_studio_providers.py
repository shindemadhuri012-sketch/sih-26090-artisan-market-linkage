"""
SIH 26090: AI Vision Provider Abstraction & Idempotency Tests
Tests provider interface, unconfigured provider handling, mock provider output,
and idempotency caching.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_unconfigured_provider_safe_failure_without_fabrication(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that when an AI provider is unconfigured (e.g. GEMINI_API_KEY absent),
    the platform returns an honest 503 Service Unavailable error and records
    status=FAILED without fabricating synthetic model predictions or crashing.
    """
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
        "title": "Chanderi Saree",
        "storytelling_description": "Descriptive narrative.",
        "price_inr": 4000.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/item.jpg",
        "original_filename": "item.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg"
    })
    media_id = r_media.json()["id"]

    # Request analysis with unconfigured provider (none) -> 503 Service Unavailable
    r_unconfigured = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "none"}
    )
    assert r_unconfigured.status_code == 503
    detail = r_unconfigured.json()["detail"].lower()
    assert "unconfigured" in detail or "not configured" in detail

    # Verify analysis record exists in DB with status=FAILED
    r_list = await client.get(f"/api/v1/products/{prod_id}/ai/analyses", headers=artisan_headers)
    assert r_list.status_code == 200
    analyses = r_list.json()
    assert len(analyses) >= 1
    failed_analysis = analyses[0]
    assert failed_analysis["status"] == "FAILED"
    assert failed_analysis["error_message"] is not None
    assert len(failed_analysis["suggestions"]) == 0


@pytest.mark.asyncio
async def test_mock_provider_structured_output_and_idempotency(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that the MockVisionProvider generates valid structured craft attributes
    conforming to the schema, and that identical requests reuse cached analysis (idempotency).
    """
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
        "title": "Chanderi Saree",
        "storytelling_description": "Descriptive narrative.",
        "price_inr": 4000.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/item.jpg",
        "original_filename": "item.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg",
        "checksum_sha256": "abc123def456"
    })
    media_id = r_media.json()["id"]

    # 1. First analysis execution
    r_first = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    assert r_first.status_code == 201
    analysis_1 = r_first.json()
    assert analysis_1["status"] == "COMPLETED"
    assert analysis_1["model_name"] == "mock-vision-test"
    assert analysis_1["provider"] == "mock"
    assert len(analysis_1["suggestions"]) >= 5

    # Verify structured fields exist
    fields = [s["field_name"] for s in analysis_1["suggestions"]]
    assert "materials" in fields
    assert "technique" in fields
    assert "primary_color" in fields

    # 2. Second request without force_reanalyze -> Reuses cached analysis (Idempotency)
    r_cached = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock", "force_reanalyze": False}
    )
    assert r_cached.status_code == 201
    analysis_2 = r_cached.json()
    assert analysis_2["id"] == analysis_1["id"]

    # 3. Third request with force_reanalyze=True -> Generates a new analysis
    r_force = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock", "force_reanalyze": True}
    )
    assert r_force.status_code == 201
    analysis_3 = r_force.json()
    assert analysis_3["id"] != analysis_1["id"]
