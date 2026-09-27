"""
SIH 26090: AI Provenance, Canonical Product Protection & Human Confirmation Tests
Verifies the four information states (AI_SUGGESTED -> HUMAN_CONFIRMED),
canonical Product field isolation, field-level accept/edit/reject workflows,
and the re-moderation policy on published products.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_canonical_product_isolation_and_suggestion_provenance(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that running an AI analysis does NOT modify canonical Product fields.
    Verifies that suggestions are isolated in AI_SUGGESTED status with human_confirmed=False.
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

    initial_title = "Original Artisan Untouched Title"
    initial_materials = ["Handspun Cotton"]

    r_prod = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": initial_title,
        "storytelling_description": "Initial storytelling text provided by artisan.",
        "price_inr": 3200.0,
        "stock_quantity": 4,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7,
        "materials": initial_materials
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/photo.jpg",
        "original_filename": "photo.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg"
    })
    media_id = r_media.json()["id"]

    # 2. Run AI Analysis
    r_analysis = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    assert r_analysis.status_code == 201
    analysis_data = r_analysis.json()

    # 3. Check Suggestion Provenance: every suggestion must be AI_SUGGESTED and NOT human_confirmed
    for sug in analysis_data["suggestions"]:
        assert sug["source_type"] == "AI_SUGGESTED"
        assert sug["status"] == "AI_SUGGESTED"
        assert sug["human_confirmed"] is False
        assert sug["confirmed_value"] is None

    # 4. Canonical Product Protection: Product fields must remain 100% UNTOUCHED!
    r_check = await client.get("/api/v1/artisans/me/products", headers=artisan_headers)
    my_prods = r_check.json()
    curr_prod = next(p for p in my_prods if p["id"] == prod_id)

    assert curr_prod["title"] == initial_title
    assert curr_prod["materials"] == initial_materials


@pytest.mark.asyncio
async def test_field_level_human_confirmation_accept_edit_reject(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies human-in-the-loop decisions:
    - ACCEPT: status -> HUMAN_CONFIRMED, confirmed_value == suggested_value.
    - EDIT: status -> HUMAN_CONFIRMED, confirmed_value == custom_value, original suggested_value preserved.
    - REJECT: status -> REJECTED, human_confirmed = False.
    - Application to product updates canonical fields when apply_to_product=True.
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
        "title": "Old Draft Title",
        "storytelling_description": "Initial text.",
        "price_inr": 2500.0,
        "stock_quantity": 3,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7,
        "materials": ["Rough Cotton"]
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

    r_analysis = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    analysis_id = r_analysis.json()["id"]

    # Submit field-level decisions:
    # 1. ACCEPT materials
    # 2. EDIT title with custom wording
    # 3. REJECT technique
    confirm_payload = {
        "confirmations": [
            {
                "field_name": "materials",
                "action": "ACCEPT"
            },
            {
                "field_name": "title",
                "action": "EDIT",
                "custom_value": "Artisan-Refined Handloom Chanderi Saree",
                "notes": "Clarified that this is handloom not powerloom."
            },
            {
                "field_name": "technique",
                "action": "REJECT",
                "notes": "Technique was not pit loom; it was frame loom."
            }
        ],
        "apply_to_product": True
    }

    r_confirm = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyses/{analysis_id}/confirm",
        headers=artisan_headers,
        json=confirm_payload
    )
    assert r_confirm.status_code == 200
    updated_analysis = r_confirm.json()

    sug_map = {s["field_name"]: s for s in updated_analysis["suggestions"]}

    # Check ACCEPTED materials
    mat_sug = sug_map["materials"]
    assert mat_sug["status"] == "HUMAN_CONFIRMED"
    assert mat_sug["source_type"] == "HUMAN_CONFIRMED"
    assert mat_sug["human_confirmed"] is True
    assert mat_sug["confirmed_value"] == mat_sug["suggested_value"]

    # Check EDITED title: original suggested_value must be preserved!
    title_sug = sug_map["title"]
    assert title_sug["status"] == "HUMAN_CONFIRMED"
    assert title_sug["source_type"] == "HUMAN_CONFIRMED"
    assert title_sug["human_confirmed"] is True
    assert title_sug["confirmed_value"] == "Artisan-Refined Handloom Chanderi Saree"
    assert title_sug["suggested_value"] != "Artisan-Refined Handloom Chanderi Saree"  # Original preserved!
    assert title_sug["artisan_notes"] == "Clarified that this is handloom not powerloom."

    # Check REJECTED technique
    tech_sug = sug_map["technique"]
    assert tech_sug["status"] == "REJECTED"
    assert tech_sug["source_type"] == "REJECTED"
    assert tech_sug["human_confirmed"] is False

    # Check Canonical Product update: only confirmed attributes updated canonical fields
    r_check = await client.get("/api/v1/artisans/me/products", headers=artisan_headers)
    my_prods = r_check.json()
    curr_prod = next(p for p in my_prods if p["id"] == prod_id)

    assert curr_prod["title"] == "Artisan-Refined Handloom Chanderi Saree"
    assert curr_prod["materials"] == mat_sug["confirmed_value"]
    # Technique was rejected, so canonical technique must NOT be updated by AI suggestion
    assert curr_prod["technique"] is None
    # Check ai_metadata contract update
    assert curr_prod["ai_metadata"]["human_confirmed"] is True


@pytest.mark.asyncio
async def test_re_moderation_policy_on_published_product(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that if confirmed AI attributes modify a product that is currently
    PUBLISHED, its lifecycle status is automatically reverted to DRAFT for re-moderation.
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
        "price_inr": 5000.0,
        "stock_quantity": 2,
        "monthly_production_capacity": 5,
        "min_order_quantity": 1,
        "lead_time_days": 10
    })
    prod_id = r_prod.json()["id"]

    r_media = await client.post(f"/api/v1/products/{prod_id}/media", headers=artisan_headers, json={
        "media_type": "IMAGE",
        "url": "https://storage.artisanmarket.gov.in/products/saree.jpg",
        "original_filename": "saree.jpg",
        "file_size_bytes": 102400,
        "mime_type": "image/jpeg"
    })
    media_id = r_media.json()["id"]

    # Submit and Admin approves -> PUBLISHED
    await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)
    r_pub = await client.post(
        f"/api/v1/products/admin/{prod_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE"}
    )
    assert r_pub.json()["status"] == "PUBLISHED"

    # Now run AI analysis and confirm an attribute with apply_to_product=True
    r_analysis = await client.post(
        f"/api/v1/products/{prod_id}/ai/analyze",
        headers=artisan_headers,
        json={"media_id": media_id, "provider_override": "mock"}
    )
    analysis_id = r_analysis.json()["id"]

    await client.post(
        f"/api/v1/products/{prod_id}/ai/analyses/{analysis_id}/confirm",
        headers=artisan_headers,
        json={
            "confirmations": [
                {"field_name": "title", "action": "EDIT", "custom_value": "New Confirmed Title"}
            ],
            "apply_to_product": True
        }
    )

    # Product status must have been reset to DRAFT!
    r_check = await client.get("/api/v1/artisans/me/products", headers=artisan_headers)
    updated_prod = next(p for p in r_check.json() if p["id"] == prod_id)
    assert updated_prod["status"] == "DRAFT"
    assert updated_prod["title"] == "New Confirmed Title"
