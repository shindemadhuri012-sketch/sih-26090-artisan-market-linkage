"""
SIH 26090: Unified Moderation Workflows & Legacy Bug Fix Regression Tests
Tests multi-entity queues, idempotency keys, critical-field re-moderation allowlists,
and proves that ADMIN_APPROVED does NOT automatically become AUTHORITY_VERIFIED.
"""

import pytest
import uuid
from httpx import AsyncClient
from backend.app.models.craft import Craft
from backend.app.models.auth import User


@pytest.mark.asyncio
async def test_critical_field_allowlist_re_moderation(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Tests that only modifications to CRITICAL fields (title, price, materials, craft)
    reset a PUBLISHED product to DRAFT.
    Non-critical operational changes (stock_quantity, capacity, lead_time) remain PUBLISHED.
    """
    # 1. Artisan profile
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Sita Devi",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 30
    })

    # 2. Create and approve product
    p_res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Cotton Silk Dupatta",
        "storytelling_description": "Finely woven traditional Chanderi dupatta.",
        "price_inr": "1800.00",
        "stock_quantity": 10
    })
    product_id = p_res.json()["id"]

    await client.post(f"/api/v1/products/{product_id}/submit", headers=artisan_headers)
    await client.post(
        f"/api/v1/products/admin/{product_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE"}
    )

    # Verify published
    p_check = await client.get(f"/api/v1/products/{product_id}", headers=artisan_headers)
    assert p_check.json()["status"] == "PUBLISHED"

    # 3. Update NON-CRITICAL field: stock_quantity
    up1 = await client.put(
        f"/api/v1/products/{product_id}",
        headers=artisan_headers,
        json={"stock_quantity": 15}
    )
    assert up1.status_code == 200
    assert up1.json()["stock_quantity"] == 15
    assert up1.json()["status"] == "PUBLISHED"  # Stays PUBLISHED!

    # 4. Update CRITICAL field: title
    up2 = await client.put(
        f"/api/v1/products/{product_id}",
        headers=artisan_headers,
        json={"title": "Updated Chanderi Heavy Dupatta"}
    )
    assert up2.status_code == 200
    assert up2.json()["title"] == "Updated Chanderi Heavy Dupatta"
    assert up2.json()["status"] == "DRAFT"  # Reset to DRAFT for re-moderation!


@pytest.mark.asyncio
async def test_legacy_gi_verification_bug_fixed_and_cannot_regress(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    CRITICAL REGRESSION TEST:
    Verifies that approving a product for a GI-tagged craft WITHOUT authoritative evidence
    sets provenance_status = ADMIN_APPROVED, NEVER automatically GOVERNMENT_GI_CONFIRMED.
    """
    # 1. Setup artisan profile (without verified GI passport)
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Unverified GI Claimant",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })

    # 2. Create product for seed_craft (which has GI tag GI-007)
    assert seed_craft.has_gi_tag is True

    p_res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Pure Silk Fabric",
        "storytelling_description": "Hand-crafted silk fabric without official AU certificate.",
        "price_inr": "3200.00"
    })
    prod_id = p_res.json()["id"]

    await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)

    # 3. Admin APPROVES product WITHOUT providing authoritative_evidence_reference
    app_res = await client.post(
        f"/api/v1/products/admin/{prod_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE"}
    )
    assert app_res.status_code == 200
    approved_prod = app_res.json()
    assert approved_prod["status"] == "PUBLISHED"
    # MUST BE ADMIN_APPROVED, NOT GOVERNMENT_GI_CONFIRMED!
    assert approved_prod["provenance_status"] == "ADMIN_APPROVED"
    assert approved_prod["provenance_status"] != "GOVERNMENT_GI_CONFIRMED"


@pytest.mark.asyncio
async def test_moderation_queue_and_idempotency_key(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Tests unified moderation queue and verifies that duplicate review calls
    with the same idempotency_key return the cached decision.
    """
    # 1. Artisan creates and submits product
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Idempotent Artisan",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 10
    })

    p_res = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Queued Product Item",
        "storytelling_description": "Testing queue retrieval and idempotency.",
        "price_inr": "1400.00"
    })
    prod_id = p_res.json()["id"]
    await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)

    # 2. Check unified queue
    q_res = await client.get("/api/v1/moderation/queue?entity_type=PRODUCT", headers=admin_headers)
    assert q_res.status_code == 200
    queue_ids = [item["entity_id"] for item in q_res.json()["items"]]
    assert prod_id in queue_ids

    # 3. Submit decision with idempotency_key
    idempotency_key = f"IDEM-MOD-{uuid.uuid4().hex}"
    decision_payload = {
        "entity_type": "PRODUCT",
        "entity_id": prod_id,
        "decision": "APPROVE",
        "reason_category": "AUTHENTICITY_VERIFIED",
        "moderator_notes": "First submission check.",
        "idempotency_key": idempotency_key
    }

    res1 = await client.post("/api/v1/moderation/review", headers=admin_headers, json=decision_payload)
    assert res1.status_code == 200
    action1 = res1.json()
    assert action1["decision"] == "APPROVE"

    # 4. Duplicate submission with SAME idempotency_key
    res2 = await client.post("/api/v1/moderation/review", headers=admin_headers, json=decision_payload)
    assert res2.status_code == 200
    action2 = res2.json()
    assert action2["id"] == action1["id"]
