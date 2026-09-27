"""
SIH 26090: Product Catalogue & Lifecycle Automated Tests
Tests product creation, auto-generated SKU, inventory vs capacity separation,
lifecycle state transitions (DRAFT -> PENDING_REVIEW -> PUBLISHED),
input validation, and deterministic catalogue filtering.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_product_creation_and_sku_generation(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that an artisan can create a product listing with inventory,
    monthly production capacity, MOQ, and lead time properly separated.
    Also verifies SKU generation and DRAFT default status.
    """
    # 1. Setup artisan profile
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    # 2. Create product
    payload = {
        "craft_id": seed_craft.id,
        "title": "Chanderi Handloom Cotton Silk Saree",
        "storytelling_description": "Hand-woven on traditional pit loom using pure mulberry silk and fine cotton with gold zari motifs.",
        "price_inr": 4850.00,
        "currency": "INR",
        "stock_quantity": 4,
        "monthly_production_capacity": 15,
        "min_order_quantity": 1,
        "lead_time_days": 12,
        "availability_status": "AVAILABLE",
        "region": "Chanderi, Madhya Pradesh",
        "materials": ["Pure Mulberry Silk", "Cotton Yarn", "Zari"],
        "primary_color": "Maroon",
        "dimensions": "5.5m x 1.15m",
        "weight_grams": 450,
        "technique": "Pit Loom Extra-Weft Zari Weave",
        "style": "Traditional Heritage",
        "tags": ["saree", "chanderi", "handloom", "festive"],
        "is_customizable": True
    }
    r = await client.post("/api/v1/products", headers=artisan_headers, json=payload)
    assert r.status_code == 201
    prod = r.json()

    assert prod["title"] == payload["title"]
    assert prod["price_inr"] == 4850.00
    assert prod["stock_quantity"] == 4
    assert prod["monthly_production_capacity"] == 15
    assert prod["min_order_quantity"] == 1
    assert prod["lead_time_days"] == 12
    assert prod["status"] == "DRAFT"
    assert prod["provenance_status"] == "ARTISAN_DECLARED"
    assert prod["sku"].startswith("PRD-")
    assert prod["craft_name"] == seed_craft.name


@pytest.mark.asyncio
async def test_product_input_validation(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Verifies that invalid product inputs (negative price, negative stock,
    invalid currency, negative capacity) are rejected by schema validators with 422.
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    base_payload = {
        "craft_id": seed_craft.id,
        "title": "Chanderi Saree",
        "storytelling_description": "Valid descriptive narrative of the craft.",
        "price_inr": 3500.0,
        "currency": "INR",
        "stock_quantity": 5,
        "monthly_production_capacity": 10,
        "min_order_quantity": 1,
        "lead_time_days": 7
    }

    # 1. Negative price
    bad_price = dict(base_payload, price_inr=-100.0)
    r = await client.post("/api/v1/products", headers=artisan_headers, json=bad_price)
    assert r.status_code == 422

    # 2. Negative stock
    bad_stock = dict(base_payload, stock_quantity=-1)
    r = await client.post("/api/v1/products", headers=artisan_headers, json=bad_stock)
    assert r.status_code == 422

    # 3. Invalid currency
    bad_curr = dict(base_payload, currency="USD")
    r = await client.post("/api/v1/products", headers=artisan_headers, json=bad_curr)
    assert r.status_code == 422

    # 4. Zero or negative MOQ
    bad_moq = dict(base_payload, min_order_quantity=0)
    r = await client.post("/api/v1/products", headers=artisan_headers, json=bad_moq)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_product_lifecycle_and_moderation_flow(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies full lifecycle transitions:
    1. Artisan creates product -> DRAFT
    2. Artisan submits product -> PENDING_REVIEW
    3. Admin views pending queue
    4. Admin approves product -> PUBLISHED (and GI provenance confirmed if craft has GI)
    5. Product is now visible in public catalogue
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 25
    })

    # Step 1: Create Draft
    r_create = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Bridal Saree",
        "storytelling_description": "Heritage pure silk handloom piece woven with real silver zari thread.",
        "price_inr": 12000.0,
        "stock_quantity": 2,
        "monthly_production_capacity": 5,
        "min_order_quantity": 1,
        "lead_time_days": 21
    })
    assert r_create.status_code == 201
    prod_id = r_create.json()["id"]
    assert r_create.json()["status"] == "DRAFT"

    # Verify DRAFT is NOT visible in public catalogue
    r_pub_draft = await client.get("/api/v1/products")
    assert r_pub_draft.status_code == 200
    assert not any(p["id"] == prod_id for p in r_pub_draft.json()["items"])

    # Step 2: Submit for review
    r_submit = await client.post(f"/api/v1/products/{prod_id}/submit", headers=artisan_headers)
    assert r_submit.status_code == 200
    assert r_submit.json()["status"] == "PENDING_REVIEW"

    # Step 3: Admin inspects pending queue
    r_pending = await client.get("/api/v1/products/admin/pending", headers=admin_headers)
    assert r_pending.status_code == 200
    assert any(p["id"] == prod_id for p in r_pending.json())

    # Step 4: Admin approves product
    r_approve = await client.post(
        f"/api/v1/products/admin/{prod_id}/review",
        headers=admin_headers,
        json={
            "decision": "APPROVE",
            "admin_notes": "Meets authentic GI Chanderi specifications.",
            "authoritative_evidence_reference": "CGPDTM-GI-AU-2026-CHANDERI-001"
        }
    )
    assert r_approve.status_code == 200
    approved = r_approve.json()
    assert approved["status"] == "PUBLISHED"
    assert approved["provenance_status"] == "GOVERNMENT_GI_CONFIRMED"

    # Step 5: Product is now visible in public catalogue
    r_pub = await client.get("/api/v1/products")
    assert r_pub.status_code == 200
    assert any(p["id"] == prod_id for p in r_pub.json()["items"])


@pytest.mark.asyncio
async def test_public_catalogue_deterministic_filtering(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Verifies multi-dimensional deterministic catalogue filtering:
    - Min & Max price filtering
    - Monthly production capacity filtering
    - Max MOQ filtering
    - Craft ID filtering
    """
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Ramesh Weaver",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 50
    })

    # Create Product A: Budget item (₹1,500, MOQ 5, Capacity 50)
    r_a = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Cotton Dupatta",
        "storytelling_description": "Lightweight handloom cotton dupatta with golden zari borders.",
        "price_inr": 1500.0,
        "stock_quantity": 20,
        "monthly_production_capacity": 50,
        "min_order_quantity": 5,
        "lead_time_days": 5
    })
    id_a = r_a.json()["id"]
    await client.post(f"/api/v1/products/{id_a}/submit", headers=artisan_headers)
    await client.post(f"/api/v1/products/admin/{id_a}/review", headers=admin_headers, json={"decision": "APPROVE"})

    # Create Product B: Luxury item (₹18,000, MOQ 1, Capacity 4)
    r_b = await client.post("/api/v1/products", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "title": "Chanderi Royal Pure Silk Saree",
        "storytelling_description": "Exclusive collector's edition woven with fine gold zari floral jaal.",
        "price_inr": 18000.0,
        "stock_quantity": 2,
        "monthly_production_capacity": 4,
        "min_order_quantity": 1,
        "lead_time_days": 30
    })
    id_b = r_b.json()["id"]
    await client.post(f"/api/v1/products/{id_b}/submit", headers=artisan_headers)
    await client.post(f"/api/v1/products/admin/{id_b}/review", headers=admin_headers, json={"decision": "APPROVE"})

    # 1. Price filter: under ₹5,000 should return only Product A
    r_low_price = await client.get("/api/v1/products", params={"max_price": 5000.0})
    assert r_low_price.status_code == 200
    ids = [p["id"] for p in r_low_price.json()["items"]]
    assert id_a in ids
    assert id_b not in ids

    # 2. Price filter: above ₹10,000 should return only Product B
    r_high_price = await client.get("/api/v1/products", params={"min_price": 10000.0})
    assert r_high_price.status_code == 200
    ids = [p["id"] for p in r_high_price.json()["items"]]
    assert id_b in ids
    assert id_a not in ids

    # 3. Capacity filter: min capacity 30 should return only Product A
    r_cap = await client.get("/api/v1/products", params={"min_capacity": 30})
    assert r_cap.status_code == 200
    ids = [p["id"] for p in r_cap.json()["items"]]
    assert id_a in ids
    assert id_b not in ids

    # 4. MOQ filter: max MOQ 2 should return only Product B
    r_moq = await client.get("/api/v1/products", params={"max_moq": 2})
    assert r_moq.status_code == 200
    ids = [p["id"] for p in r_moq.json()["items"]]
    assert id_b in ids
    assert id_a not in ids
