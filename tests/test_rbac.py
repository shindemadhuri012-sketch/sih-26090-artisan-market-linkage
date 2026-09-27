"""
SIH 26090: RBAC & Object-Level Authorization Automated Tests
Verifies role separation (Artisan, Buyer, Admin), unauthenticated request rejection,
and IDOR defense preventing cross-user unauthorized access.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.auth import User
from backend.app.models.craft import Craft
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import CraftPassport


@pytest.mark.asyncio
async def test_artisan_forbidden_from_buyer_endpoints(client: AsyncClient, artisan_headers: dict):
    """Verifies that an artisan role user cannot access buyer private endpoints."""
    response = await client.get("/api/v1/buyers/me", headers=artisan_headers)
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_buyer_forbidden_from_artisan_endpoints(client: AsyncClient, buyer_headers: dict):
    """Verifies that a buyer role user cannot access artisan private endpoints."""
    response = await client.get("/api/v1/artisans/me", headers=buyer_headers)
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_artisan_forbidden_from_admin_review(client: AsyncClient, artisan_headers: dict):
    """Verifies that an artisan cannot access admin review pending list."""
    response = await client.get("/api/v1/verifications/admin/pending", headers=artisan_headers)
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_buyer_forbidden_from_admin_review(client: AsyncClient, buyer_headers: dict):
    """Verifies that a buyer cannot access admin review pending list."""
    response = await client.get("/api/v1/verifications/admin/pending", headers=buyer_headers)
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_authorized_for_admin_review(client: AsyncClient, admin_headers: dict):
    """Verifies that an admin user can access the pending review list."""
    response = await client.get("/api/v1/verifications/admin/pending", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Verifies that missing Authorization Bearer token returns 401 Unauthorized."""
    r1 = await client.get("/api/v1/artisans/me")
    assert r1.status_code == 401

    r2 = await client.get("/api/v1/buyers/me")
    assert r2.status_code == 401

    r3 = await client.get("/api/v1/passports/my")
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_tampered_jwt_token_rejected(client: AsyncClient):
    """Verifies that forged or modified JWT access token returns 401 Unauthorized."""
    tampered_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.signature"}
    response = await client.get("/api/v1/auth/me", headers=tampered_headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_idor_defense_cross_artisan_passport_submission(
    client: AsyncClient,
    artisan_headers: dict,
    other_artisan_headers: dict,
    artisan_user: User,
    other_artisan_user: User,
    seed_craft: Craft
):
    """
    IDOR Security Test:
    Artisan 1 creates an artisan profile and draft passport.
    Artisan 2 attempts to submit Artisan 1's passport for review.
    The platform must reject with 403 Forbidden.
    """
    # 1. Artisan 1 creates profile
    p1 = await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Artisan One",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 15
    })
    assert p1.status_code == 201

    # 2. Artisan 1 creates craft passport
    pass_res = await client.post("/api/v1/passports/", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "authorized_user_gi_certificate": "GI-AUTH-001"
    })
    assert pass_res.status_code == 201
    passport_id = pass_res.json()["id"]

    # 3. Artisan 2 creates own profile
    p2 = await client.post("/api/v1/artisans/me", headers=other_artisan_headers, json={
        "full_name": "Artisan Two",
        "state": "Rajasthan",
        "district": "Jaipur",
        "pincode": "302001",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 30
    })
    assert p2.status_code == 201

    # 4. Artisan 2 tries to submit Artisan 1's passport -> MUST BE FORBIDDEN (IDOR)
    idor_res = await client.post(f"/api/v1/passports/{passport_id}/submit", headers=other_artisan_headers)
    assert idor_res.status_code == 403
    assert "do not own" in idor_res.json()["detail"].lower()
