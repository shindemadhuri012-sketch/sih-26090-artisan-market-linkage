"""
SIH 26090: Requirement Understanding Tests
Verifies AI extraction staging isolation, unconfirmed suggestion isolation, and buyer confirmation workflow.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

from backend.app.models.auth import User


@pytest.mark.asyncio
async def test_ai_understanding_staging_isolation(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    seed_craft: dict
):
    # Setup profile
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "FabIndia Staging Test", "buyer_type": "RETAIL_CURATOR"},
        headers=buyer_headers
    )

    deadline = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
    raw_brief = (
        f"We require 250 pieces of authentic Chanderi Silk Saree with pure zari embroidery. "
        f"Budget is under ₹1500 per unit. Must be certified geographical indication."
    )
    r_res = await client.post(
        "/api/v1/buyer-requirements",
        json={
            "title": "Autumn Festive Collection RFQ",
            "raw_text": raw_brief,
            "required_quantity": 1,  # Intentional placeholder before AI understanding
            "deadline_date": deadline
        },
        headers=buyer_headers
    )
    assert r_res.status_code == 201
    req_id = r_res.json()["id"]

    # 1. Trigger AI Understanding
    u_res = await client.post(f"/api/v1/buyer-requirements/{req_id}/understand", headers=buyer_headers)
    assert u_res.status_code == 200
    und_data = u_res.json()
    assert und_data["status"] == "SUGGESTED"
    assert und_data["is_confirmed_by_buyer"] is False
    extracted = und_data["extracted_fields"]

    # Staging extracted quantity 250, target price 1500, GI true, materials silk/zari
    assert extracted.get("required_quantity") == 250
    assert extracted.get("target_unit_price_inr") == 1500.0
    assert extracted.get("requires_gi_certification") is True
    assert "silk" in [m.lower() for m in extracted.get("desired_materials", [])]

    # 2. Strict Staging Isolation Check: Canonical requirement MUST NOT be mutated yet
    req_check = await client.get(f"/api/v1/buyer-requirements/{req_id}", headers=buyer_headers)
    assert req_check.json()["required_quantity"] == 1  # Still original placeholder!
    assert req_check.json()["target_unit_price_inr"] is None


@pytest.mark.asyncio
async def test_buyer_confirmation_workflow(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    seed_craft: dict
):
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "FabIndia Confirmation Test", "buyer_type": "RETAIL_CURATOR"},
        headers=buyer_headers
    )

    deadline = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
    r_res = await client.post(
        "/api/v1/buyer-requirements",
        json={
            "title": "Corporate Gifting Brief",
            "raw_text": "Need 300 Chanderi Silk Saree stoles for summit by next month under ₹2000 each.",
            "required_quantity": 1,
            "deadline_date": deadline
        },
        headers=buyer_headers
    )
    req_id = r_res.json()["id"]

    # Extract
    await client.post(f"/api/v1/buyer-requirements/{req_id}/understand", headers=buyer_headers)

    # Confirm with an override
    conf_res = await client.post(
        f"/api/v1/buyer-requirements/{req_id}/understand/confirm",
        json={"overrides": {"required_quantity": 350, "preferred_region": "Madhya Pradesh"}},
        headers=buyer_headers
    )
    assert conf_res.status_code == 200
    confirmed_req = conf_res.json()

    # Canonical fields are now updated
    assert confirmed_req["required_quantity"] == 350
    assert confirmed_req["preferred_region"] == "Madhya Pradesh"
    assert float(confirmed_req["target_unit_price_inr"]) == 2000.00
    assert confirmed_req["target_craft_id"] == seed_craft.id
