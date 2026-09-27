"""
SIH 26090: Buyer Requirement API Tests
Tests requirement creation, retrieval, updates, cancellation, and IDOR protection.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

from backend.app.models.auth import User
from backend.app.models.buyer import BuyerProfile


@pytest.mark.asyncio
async def test_create_and_get_buyer_requirement(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    seed_craft: dict
):
    # 1. Create buyer profile first
    p_res = await client.post(
        "/api/v1/buyers/me",
        json={
            "company_name": "FabIndia Procurement Corp",
            "buyer_type": "RETAIL_CURATOR",
            "state": "Delhi"
        },
        headers=buyer_headers
    )
    assert p_res.status_code == 201

    # 2. Create requirement
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    req_payload = {
        "title": "500 Chanderi Silk Scarves for Autumn Gifting",
        "raw_text": "Looking for 500 handloom Chanderi silk stoles with pure zari borders. Target budget ₹1,200 per piece.",
        "target_craft_id": seed_craft.id,
        "required_quantity": 500,
        "target_unit_price_inr": 1200.00,
        "max_budget_inr": 600000.00,
        "deadline_date": deadline,
        "requires_gi_certification": True,
        "desired_materials": ["Silk", "Zari"],
        "desired_techniques": ["Handloom"],
        "preferred_region": "Madhya Pradesh",
        "requires_customization": True
    }

    r_res = await client.post("/api/v1/buyer-requirements", json=req_payload, headers=buyer_headers)
    assert r_res.status_code == 201
    data = r_res.json()
    assert data["title"] == req_payload["title"]
    assert data["required_quantity"] == 500
    assert data["currency"] == "INR"
    assert data["status"] == "OPEN"
    assert data["has_embedding"] is True
    req_id = data["id"]

    # 3. Retrieve detail
    get_res = await client.get(f"/api/v1/buyer-requirements/{req_id}", headers=buyer_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == req_id


@pytest.mark.asyncio
async def test_update_and_cancel_buyer_requirement(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict
):
    # Setup profile
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "Curators Inc", "buyer_type": "RETAIL_CURATOR"},
        headers=buyer_headers
    )

    deadline = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    req_payload = {
        "title": "100 Paithani Borders",
        "raw_text": "Need 100 Paithani borders for boutique collection.",
        "required_quantity": 100,
        "deadline_date": deadline
    }
    r_res = await client.post("/api/v1/buyer-requirements", json=req_payload, headers=buyer_headers)
    assert r_res.status_code == 201
    req_id = r_res.json()["id"]

    # Update
    u_res = await client.put(
        f"/api/v1/buyer-requirements/{req_id}",
        json={"required_quantity": 150, "preferred_region": "Maharashtra"},
        headers=buyer_headers
    )
    assert u_res.status_code == 200
    assert u_res.json()["required_quantity"] == 150
    assert u_res.json()["preferred_region"] == "Maharashtra"

    # Cancel
    del_res = await client.delete(f"/api/v1/buyer-requirements/{req_id}", headers=buyer_headers)
    assert del_res.status_code == 204

    # Verify cancelled
    chk = await client.get(f"/api/v1/buyer-requirements/{req_id}", headers=buyer_headers)
    assert chk.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_buyer_requirement_idor_protection(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    admin_headers: dict
):
    # Buyer 1 setup
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "Buyer One Ltd", "buyer_type": "EXPORT_AGGREGATOR"},
        headers=buyer_headers
    )

    deadline = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    r_res = await client.post(
        "/api/v1/buyer-requirements",
        json={"title": "Private Brief", "raw_text": "Confidential corporate gift RFQ.", "required_quantity": 50, "deadline_date": deadline},
        headers=buyer_headers
    )
    req_id = r_res.json()["id"]

    # Register second buyer
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": "+919876543299",
            "email": "buyer2@test.in",
            "password": "BuyerTwoPass123!",
            "role": "buyer"
        }
    )
    assert reg_res.status_code == 201
    log_res = await client.post(
        "/api/v1/auth/login",
        json={"login_identifier": "+919876543299", "password": "BuyerTwoPass123!"}
    )
    assert log_res.status_code == 200
    b2_token = log_res.json()["access_token"]
    b2_headers = {"Authorization": f"Bearer {b2_token}"}

    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "Buyer Two Ltd", "buyer_type": "RETAIL_CURATOR"},
        headers=b2_headers
    )

    # Buyer 2 attempts to read Buyer 1 requirement
    get_res = await client.get(f"/api/v1/buyer-requirements/{req_id}", headers=b2_headers)
    assert get_res.status_code == 403
    assert "Forbidden" in get_res.json()["detail"]

    # Admin CAN read requirement
    admin_get = await client.get(f"/api/v1/buyer-requirements/{req_id}", headers=admin_headers)
    assert admin_get.status_code == 200
