"""
SIH 26090: Product Provenance, AI Contract & Privacy Sanitization Automated Tests
Verifies real-data provenance levels, future AI suggestion data contract integrity,
and strict omission of artisan PII from public catalogue endpoints.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_product_provenance_levels_and_gi_confirmation(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that product listings adhere to strict provenance levels:
    - Upon creation: provenance_status is ARTISAN_DECLARED
    - Upon administrative approval for GI-tagged craft: GOVERNMENT_GI_CONFIRMED
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    # Create product
    r_create = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Traditional Zari Saree",
        "storytelling_description": "Authenticated hand-woven silk saree.",
        "price_inr": 5500.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 14
    })
    prod = r_create.json()
    assert prod["provenance_status"] == "ARTISAN_DECLARED"

    # Submit and approve
    prod_id = prod["id"]
    await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)
    r_app = await client.post(
        f"/api/v1/products/admin/{prod_id}/review",
        headers=admin_headers,
        json={
            "decision": "APPROVE",
            "authoritative_evidence_reference": "CGPDTM-GI-AU-2026-CHANDERI-042"
        }
    )
    approved_prod = r_app.json()
    assert approved_prod["provenance_status"] == "GOVERNMENT_GI_CONFIRMED"


@pytest.mark.asyncio
async def test_ai_suggestion_contract_placeholder(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies the data contract schema for future AI modules without executing any AI models.
    Asserts placeholder schema compliance (no AI models executed in Phase 3).
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    r = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Kurta Fabric",
        "storytelling_description": "Unstitched 3-meter piece of pure handloom Chanderi fabric.",
        "price_inr": 2100.0,
        "stock_quantity": 8,
        "monthly_production_capacity": 20,
        "min_order_quantity": 1,
        "lead_time_days": 5
    })
    prod = r.json()
    ai_meta = prod["ai_metadata"]

    assert ai_meta is not None
    assert "title_suggestion" in ai_meta
    assert "description_suggestion" in ai_meta
    assert "suggested_tags" in ai_meta
    assert "confidence" in ai_meta
    assert "human_confirmed" in ai_meta

    # Phase 3 constraint check: no AI models run, human_confirmed is False
    assert ai_meta["human_confirmed"] is False
    assert ai_meta["model_name"] is None
    assert ai_meta["confidence"] is None


@pytest.mark.asyncio
async def test_public_catalogue_strict_pii_sanitization(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that public catalogue and public detail responses strictly withhold
    artisan personal PII (phone number, Pehchan ID, email, street address).
    Only sanitized public attributes (name, district, state, craft) are returned.
    """
    # 1. Create artisan profile with full details including Pehchan ID
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Devi Bai",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "pehchan_id": "PEH-MP-78945612",
        "years_of_experience": 30,
        "monthly_production_capacity": 10
    })

    # 2. Create product
    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Ashoknagar Heritage Chanderi Saree",
        "storytelling_description": "Woven with intricate peacock buttis using heritage techniques.",
        "price_inr": 7200.0,
        "stock_quantity": 2,
        "monthly_production_capacity": 5,
        "min_order_quantity": 1,
        "lead_time_days": 15
    })
    prod_id = r_prod.json()["id"]

    # 3. Submit and publish
    await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)
    await client.post(f"/api/v1/products/admin/{prod_id}/review", headers=admin_headers, json={"decision": "APPROVE"})

    # 4. Fetch public detail endpoint
    r_detail = await client.get(f"/api/v1/products/{prod_id}")
    assert r_detail.status_code == 200
    pub_data = r_detail.json()

    # Allowed public fields
    assert pub_data["artisan_public_name"] == "Devi Bai"
    assert pub_data["artisan_district"] == "Ashoknagar"
    assert pub_data["artisan_state"] == "Madhya Pradesh"
    assert pub_data["craft_name"] == seed_craft.name
    assert pub_data["has_gi_tag"] is True
    assert pub_data["gi_tag_number"] == "GI-007"

    # Strictly forbidden PII fields in public response
    assert "phone_number" not in pub_data
    assert "pehchan_id" not in pub_data
    assert "email" not in pub_data
    assert "bank_account" not in pub_data
    assert "aadhaar" not in pub_data
    assert "pincode" not in pub_data

    # Check serialized JSON text to ensure Pehchan ID string doesn't leak anywhere in payload
    assert "PEH-MP-78945612" not in r_detail.text
    assert "+919876543201" not in r_detail.text
