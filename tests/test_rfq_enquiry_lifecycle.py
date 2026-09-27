"""
SIH 26090: RFQ & Commercial Linkage Lifecycle Tests
Verifies RFQ creation, status transitions, counter-offers, buyer decisions, and party-to-transaction IDOR defense.
"""

import pytest
from httpx import AsyncClient

from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile


@pytest.mark.asyncio
async def test_create_and_list_rfq(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    artisan_user: User,
    artisan_headers: dict,
    seed_craft: dict
):
    # Setup buyer profile
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "FabIndia Commercial", "buyer_type": "RETAIL_CURATOR"},
        headers=buyer_headers
    )

    # Setup artisan profile
    art_prof_res = await client.post(
        "/api/v1/artisans/me",
        json={
            "full_name": "Devi Weaver",
            "state": "Madhya Pradesh",
            "district": "Ashoknagar",
            "pincode": "473446",
            "primary_craft_id": seed_craft.id,
            "years_of_experience": 15,
            "monthly_production_capacity": 80
        },
        headers=artisan_headers
    )
    artisan_profile_id = art_prof_res.json()["id"]

    # 1. Buyer creates RFQ
    rfq_payload = {
        "artisan_id": artisan_profile_id,
        "proposed_quantity": 40,
        "proposed_unit_price": 1800.00,
        "message": "Looking to place a commercial batch order for Chanderi stoles."
    }
    create_res = await client.post("/api/v1/rfqs", json=rfq_payload, headers=buyer_headers)
    assert create_res.status_code == 201
    rfq_data = create_res.json()
    assert rfq_data["status"] == "SENT"
    assert rfq_data["rfq_reference_number"].startswith("RFQ-")
    rfq_id = rfq_data["id"]

    # 2. Buyer lists sent RFQs
    b_list = await client.get("/api/v1/rfqs/sent", headers=buyer_headers)
    assert b_list.status_code == 200
    assert any(r["id"] == rfq_id for r in b_list.json())

    # 3. Artisan lists incoming RFQs
    a_list = await client.get("/api/v1/rfqs/incoming", headers=artisan_headers)
    assert a_list.status_code == 200
    assert any(r["id"] == rfq_id for r in a_list.json())


@pytest.mark.asyncio
async def test_artisan_view_and_counter_offer_workflow(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    artisan_user: User,
    artisan_headers: dict,
    seed_craft: dict
):
    # Setup profiles
    await client.post("/api/v1/buyers/me", json={"company_name": "FabIndia Workflow", "buyer_type": "RETAIL_CURATOR"}, headers=buyer_headers)
    art_prof = await client.post(
        "/api/v1/artisans/me",
        json={
            "full_name": "Gopal Weaver",
            "state": "Madhya Pradesh",
            "district": "Ashoknagar",
            "pincode": "473446",
            "primary_craft_id": seed_craft.id
        },
        headers=artisan_headers
    )
    artisan_id = art_prof.json()["id"]

    # Create RFQ
    rfq_res = await client.post(
        "/api/v1/rfqs",
        json={"artisan_id": artisan_id, "proposed_quantity": 25, "proposed_unit_price": 2000.00, "message": "Initial proposal"},
        headers=buyer_headers
    )
    rfq_id = rfq_res.json()["id"]

    # 1. Artisan marks VIEWED
    view_res = await client.post(f"/api/v1/rfqs/{rfq_id}/view", headers=artisan_headers)
    assert view_res.status_code == 200
    assert view_res.json()["status"] == "VIEWED"
    assert view_res.json()["viewed_at"] is not None

    # 2. Artisan responds with COUNTER_OFFER
    counter_payload = {
        "action": "COUNTER_OFFER",
        "counter_unit_price": 2300.00,
        "counter_lead_time_days": 21,
        "artisan_response_message": "Raw silk prices have increased; can offer at ₹2,300 with 3 weeks turnaround."
    }
    counter_res = await client.post(f"/api/v1/rfqs/{rfq_id}/respond", json=counter_payload, headers=artisan_headers)
    assert counter_res.status_code == 200
    data = counter_res.json()
    assert data["status"] == "NEGOTIATION"
    assert float(data["counter_unit_price"]) == 2300.00
    assert data["counter_lead_time_days"] == 21

    # 3. Buyer accepts counter-offer
    decision_res = await client.post(
        f"/api/v1/rfqs/{rfq_id}/buyer-decision",
        json={"action": "ACCEPT"},
        headers=buyer_headers
    )
    assert decision_res.status_code == 200
    final_data = decision_res.json()
    assert final_data["status"] == "ACCEPTED"
    assert final_data["proposed_unit_price"] == "2300.00"  # Agreed at counter price


@pytest.mark.asyncio
async def test_rfq_party_to_transaction_idor_defense(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    artisan_user: User,
    artisan_headers: dict,
    other_artisan_headers: dict,
    seed_craft: dict
):
    # Setup profiles
    await client.post("/api/v1/buyers/me", json={"company_name": "Secure Buyer", "buyer_type": "RETAIL_CURATOR"}, headers=buyer_headers)
    art_prof = await client.post(
        "/api/v1/artisans/me",
        json={"full_name": "Target Artisan", "state": "Madhya Pradesh", "district": "Ashoknagar", "pincode": "473446", "primary_craft_id": seed_craft.id},
        headers=artisan_headers
    )
    artisan_id = art_prof.json()["id"]

    # Create RFQ
    rfq_res = await client.post(
        "/api/v1/rfqs",
        json={"artisan_id": artisan_id, "proposed_quantity": 10, "proposed_unit_price": 1000.00, "message": "Confidential RFQ"},
        headers=buyer_headers
    )
    rfq_id = rfq_res.json()["id"]

    # Setup other artisan profile
    await client.post(
        "/api/v1/artisans/me",
        json={"full_name": "Third Party Artisan", "state": "Gujarat", "district": "Surat", "pincode": "395001", "primary_craft_id": seed_craft.id},
        headers=other_artisan_headers
    )

    # Other artisan attempts to read RFQ -> 403 Forbidden
    unauthorized_get = await client.get(f"/api/v1/rfqs/{rfq_id}", headers=other_artisan_headers)
    assert unauthorized_get.status_code == 403

    # Other artisan attempts to respond -> 403 Forbidden
    unauthorized_resp = await client.post(
        f"/api/v1/rfqs/{rfq_id}/respond",
        json={"action": "ACCEPT"},
        headers=other_artisan_headers
    )
    assert unauthorized_resp.status_code == 403
