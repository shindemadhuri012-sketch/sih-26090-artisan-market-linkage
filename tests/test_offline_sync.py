"""
SIH 26090: Offline Sync Unit Tests
Verifies batch mutation replay, server-side authorization & IDOR defense,
idempotency key protection against duplicate writes, and concurrency conflict detection.
"""

from datetime import datetime, timezone, timedelta
import uuid
import pytest
from httpx import AsyncClient

from backend.app.models.auth import User
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_offline_product_creation_and_idempotency(
    client: AsyncClient,
    artisan_user: User,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that an artisan can queue an offline product creation and that idempotency blocks duplicates."""
    # Setup artisan profile
    await client.post(
        "/api/v1/artisans/me",
        json={
            "full_name": "Ramesh Weaver",
            "state": "Madhya Pradesh",
            "district": "Ashoknagar",
            "pincode": "473446",
            "primary_craft_id": seed_craft.id
        },
        headers=artisan_headers
    )

    client_mutation_id = str(uuid.uuid4())
    idempotency_key = f"IDEMPOTENT-TEST-{uuid.uuid4().hex}"

    batch_payload = {
        "mutations": [
            {
                "client_mutation_id": client_mutation_id,
                "idempotency_key": idempotency_key,
                "entity_type": "PRODUCT",
                "entity_id": str(uuid.uuid4()),  # Temporary client UUID
                "operation_type": "CREATE",
                "payload": {
                    "craft_id": seed_craft.id,
                    "title": "Offline Created Chanderi Stole",
                    "price_inr": "1850.00",
                    "stock_quantity": 15,
                    "monthly_production_capacity": 50,
                    "materials": ["Chanderi Silk", "Zari"],
                    "techniques": ["Handloom Weaving"]
                },
                "client_created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    # First Submission: Must be COMMITTED
    res1 = await client.post("/api/v1/sync/batch", json=batch_payload, headers=artisan_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["committed"] == 1
    assert data1["conflicts"] == 0
    assert data1["rejected"] == 0

    first_result = data1["results"][0]
    assert first_result["status"] == "COMMITTED"
    assert first_result["idempotency_key"] == idempotency_key
    server_prod_id = first_result["server_entity_id"]
    assert server_prod_id is not None

    # Verify product exists in DRAFT status
    get_res = await client.get(f"/api/v1/products/{server_prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Offline Created Chanderi Stole"
    assert get_res.json()["status"] == "DRAFT"

    # Second Submission (Replay with same idempotency_key): Must return ALREADY_PROCESSED and NOT duplicate
    res2 = await client.post("/api/v1/sync/batch", json=batch_payload, headers=artisan_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    second_result = data2["results"][0]
    assert second_result["status"] == "ALREADY_PROCESSED"
    assert second_result["server_entity_id"] == server_prod_id


@pytest.mark.asyncio
async def test_offline_update_conflict_detection(
    client: AsyncClient,
    artisan_user: User,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that an offline update against a stale server state returns CONFLICT."""
    # Setup profile & product
    await client.post(
        "/api/v1/artisans/me",
        json={
            "full_name": "Mahesh Weaver",
            "state": "Madhya Pradesh",
            "district": "Ashoknagar",
            "pincode": "473446",
            "primary_craft_id": seed_craft.id
        },
        headers=artisan_headers
    )
    p_res = await client.post(
        "/api/v1/products",
        json={
            "craft_id": seed_craft.id,
            "title": "Initial Product Title",
            "price_inr": "1200.00",
            "stock_quantity": 10,
            "monthly_production_capacity": 30,
            "storytelling_description": "Handcrafted traditional artisanal textile."
        },
        headers=artisan_headers
    )
    product_id = p_res.json()["id"]

    # Server update occurs (simulating an edit from another device)
    await client.put(
        f"/api/v1/products/{product_id}",
        json={"title": "Updated from Web Console"},
        headers=artisan_headers
    )

    # Client now tries to sync an offline mutation with an old client_base_updated_at (2 hours ago)
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    mutation_payload = {
        "mutations": [
            {
                "client_mutation_id": str(uuid.uuid4()),
                "idempotency_key": f"IDEM-CONFLICT-{uuid.uuid4().hex}",
                "entity_type": "PRODUCT",
                "entity_id": product_id,
                "operation_type": "UPDATE",
                "payload": {
                    "title": "Offline Conflicting Edit",
                    "client_base_updated_at": stale_timestamp
                },
                "client_created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    res = await client.post("/api/v1/sync/batch", json=mutation_payload, headers=artisan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["conflicts"] == 1
    result = data["results"][0]
    assert result["status"] == "CONFLICT"
    assert "modified on the server" in result["error_message"].lower()
    assert result["conflict_details"] is not None


@pytest.mark.asyncio
async def test_offline_sync_idor_protection(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that an artisan cannot sync an update for a product owned by another artisan."""
    # Register Artisan 2
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": "+919876543291",
            "email": "artisan2@test.in",
            "password": "ArtisanTwoPass123!",
            "role": "artisan"
        }
    )
    assert reg_res.status_code == 201
    log_res = await client.post(
        "/api/v1/auth/login",
        json={"login_identifier": "+919876543291", "password": "ArtisanTwoPass123!"}
    )
    a2_headers = {"Authorization": f"Bearer {log_res.json()['access_token']}"}

    # Artisan 2 creates profile and product
    await client.post(
        "/api/v1/artisans/me",
        json={"full_name": "Artisan Two", "state": "Odisha", "district": "Puri", "pincode": "752001", "primary_craft_id": seed_craft.id},
        headers=a2_headers
    )
    p2 = await client.post(
        "/api/v1/products",
        json={
            "craft_id": seed_craft.id,
            "title": "Artisan Two Product",
            "price_inr": "2500.00",
            "storytelling_description": "Handcrafted traditional artisanal textile."
        },
        headers=a2_headers
    )
    p2_id = p2.json()["id"]

    # Setup Artisan 1 profile
    await client.post(
        "/api/v1/artisans/me",
        json={"full_name": "Artisan One", "state": "Rajasthan", "district": "Jaipur", "pincode": "302001", "primary_craft_id": seed_craft.id},
        headers=artisan_headers
    )

    # Artisan 1 attempts to sync an update for Artisan 2's product
    tampered_batch = {
        "mutations": [
            {
                "client_mutation_id": str(uuid.uuid4()),
                "idempotency_key": f"IDEM-IDOR-{uuid.uuid4().hex}",
                "entity_type": "PRODUCT",
                "entity_id": p2_id,
                "operation_type": "UPDATE",
                "payload": {"title": "Hacked Title"},
                "client_created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    res = await client.post("/api/v1/sync/batch", json=tampered_batch, headers=artisan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["rejected"] == 1
    assert "Forbidden" in data["results"][0]["error_message"]
