"""
SIH 26090: Artisan & Buyer Profile Automated Tests
Tests private /me profile CRUD, validation, conflict handling,
and public sanitized profile exposure ensuring zero private PII leakage.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_artisan_profile_lifecycle_and_sanitized_public_view(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Tests full artisan profile lifecycle:
    1. GET /artisans/me before creation returns 404
    2. POST with non-existent craft returns 400
    3. POST with valid craft creates profile (201)
    4. Duplicate POST returns 409
    5. GET /artisans/me returns full private profile
    6. PUT /artisans/me updates capacity and cooperative
    7. GET /artisans/{id}/public returns sanitized view without PII
    """
    # 1. 404 before creation
    r_empty = await client.get("/api/v1/artisans/me", headers=artisan_headers)
    assert r_empty.status_code == 404

    # 2. 400 with invalid craft
    r_bad_craft = await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Devi Lal",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": "non-existent-craft-id-000",
        "monthly_production_capacity": 25
    })
    assert r_bad_craft.status_code == 400

    # 3. 201 Created with valid data
    payload = {
        "full_name": "Devi Lal",
        "cooperative_name": "Chanderi Weavers Society",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "address_line": "House 42, Bunkar Colony, Chanderi",
        "primary_craft_id": seed_craft.id,
        "years_of_experience": 18,
        "monthly_production_capacity": 25,
        "pehchan_id": "PEHCHAN-MP-473446"
    }
    r_create = await client.post("/api/v1/artisans/me", headers=artisan_headers, json=payload)
    assert r_create.status_code == 201
    created_data = r_create.json()
    artisan_id = created_data["id"]
    assert created_data["full_name"] == "Devi Lal"
    assert created_data["cooperative_name"] == "Chanderi Weavers Society"
    assert created_data["verification_status"] == "PENDING"
    assert created_data["address_line"] == "House 42, Bunkar Colony, Chanderi"

    # 4. Duplicate POST returns 409
    r_dup = await client.post("/api/v1/artisans/me", headers=artisan_headers, json=payload)
    assert r_dup.status_code == 409

    # 5. GET /artisans/me
    r_get = await client.get("/api/v1/artisans/me", headers=artisan_headers)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == artisan_id

    # 6. PUT /artisans/me update
    r_update = await client.put("/api/v1/artisans/me", headers=artisan_headers, json={
        "monthly_production_capacity": 40,
        "cooperative_name": "Apex Chanderi Handloom Fed"
    })
    assert r_update.status_code == 200
    assert r_update.json()["monthly_production_capacity"] == 40
    assert r_update.json()["cooperative_name"] == "Apex Chanderi Handloom Fed"

    # 7. GET /artisans/{id}/public sanitized view
    r_pub = await client.get(f"/api/v1/artisans/{artisan_id}/public")
    assert r_pub.status_code == 200
    pub_data = r_pub.json()
    assert pub_data["id"] == artisan_id
    assert pub_data["full_name"] == "Devi Lal"
    assert pub_data["state"] == "Madhya Pradesh"
    assert pub_data["district"] == "Ashoknagar"
    assert pub_data["craft_name"] == "Chanderi Silk Saree"
    assert pub_data["years_of_experience"] == 18

    # Zero PII leakage verification:
    assert "address_line" not in pub_data
    assert "pincode" not in pub_data
    assert "pehchan_id" not in pub_data
    assert "phone_number" not in pub_data


@pytest.mark.asyncio
async def test_buyer_profile_lifecycle(client: AsyncClient, buyer_headers: dict):
    """
    Tests full buyer profile lifecycle:
    1. GET /buyers/me before creation returns 404
    2. POST creates buyer profile (201)
    3. Duplicate POST returns 409
    4. GET /buyers/me returns buyer profile
    5. PUT /buyers/me updates procurement requirements
    """
    # 1. 404 before creation
    r_empty = await client.get("/api/v1/buyers/me", headers=buyer_headers)
    assert r_empty.status_code == 404

    # 2. 201 Created
    payload = {
        "company_name": "FabIndia Sourcing Ltd",
        "buyer_type": "RETAIL_CURATOR",
        "gstin": "27AABCF1234F1Z5",
        "country": "India",
        "state": "Maharashtra",
        "typical_order_volume": "100-500 units"
    }
    r_create = await client.post("/api/v1/buyers/me", headers=buyer_headers, json=payload)
    assert r_create.status_code == 201
    buyer_data = r_create.json()
    assert buyer_data["company_name"] == "FabIndia Sourcing Ltd"
    assert buyer_data["buyer_type"] == "RETAIL_CURATOR"
    assert buyer_data["gstin"] == "27AABCF1234F1Z5"
    assert buyer_data["is_verified_buyer"] is False

    # 3. Duplicate POST returns 409
    r_dup = await client.post("/api/v1/buyers/me", headers=buyer_headers, json=payload)
    assert r_dup.status_code == 409

    # 4. GET /buyers/me
    r_get = await client.get("/api/v1/buyers/me", headers=buyer_headers)
    assert r_get.status_code == 200
    assert r_get.json()["company_name"] == "FabIndia Sourcing Ltd"

    # 5. PUT /buyers/me
    r_update = await client.put("/api/v1/buyers/me", headers=buyer_headers, json={
        "typical_order_volume": "500-2000 units"
    })
    assert r_update.status_code == 200
    assert r_update.json()["typical_order_volume"] == "500-2000 units"
