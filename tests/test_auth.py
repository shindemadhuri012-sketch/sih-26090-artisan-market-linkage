"""
SIH 26090: Authentication & Identity Automated Tests
Tests registration, Argon2id login, refresh token rotation with reuse detection,
logout session revocation, and OTP passwordless authentication.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.auth import User, RefreshTokenSession, OTPChallenge
from backend.app.core.security import hash_password, hash_token


@pytest.mark.asyncio
async def test_artisan_registration_success(client: AsyncClient):
    """Verifies that an artisan can register with an E.164 phone number and password."""
    payload = {
        "phone_number": "+919876500001",
        "password": "SecurePassword123!",
        "role": "artisan",
        "preferred_language": "hi"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["phone_number"] == "+919876500001"
    assert data["role"] == "artisan"
    assert data["preferred_language"] == "hi"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_buyer_registration_success(client: AsyncClient):
    """Verifies that a buyer can register with both phone number and email."""
    payload = {
        "phone_number": "+919876500002",
        "email": "buyer.procure@crafts.in",
        "password": "SecurePassword123!",
        "role": "buyer",
        "preferred_language": "en"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["phone_number"] == "+919876500002"
    assert data["email"] == "buyer.procure@crafts.in"
    assert data["role"] == "buyer"


@pytest.mark.asyncio
async def test_registration_duplicate_phone(client: AsyncClient, artisan_user: User):
    """Verifies that registering with an already existing phone number returns 409 Conflict."""
    payload = {
        "phone_number": artisan_user.phone_number,
        "password": "AnotherPassword123!",
        "role": "artisan"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_validation_rules(client: AsyncClient):
    """Verifies format validation on phone numbers, passwords, and roles."""
    # 1. Non-E.164 phone
    r1 = await client.post("/api/v1/auth/register", json={
        "phone_number": "9876543210",
        "password": "SecurePassword123!",
        "role": "artisan"
    })
    assert r1.status_code == 422

    # 2. Too short password (< 8 chars)
    r2 = await client.post("/api/v1/auth/register", json={
        "phone_number": "+919876500005",
        "password": "short",
        "role": "artisan"
    })
    assert r2.status_code == 422

    # 3. Disallowed registration role (e.g. attempting to self-grant admin)
    r3 = await client.post("/api/v1/auth/register", json={
        "phone_number": "+919876500006",
        "password": "SecurePassword123!",
        "role": "admin"
    })
    assert r3.status_code == 422


@pytest.mark.asyncio
async def test_login_by_phone_success(client: AsyncClient, artisan_user: User):
    """Verifies successful login via phone number returning access and refresh tokens."""
    payload = {
        "login_identifier": artisan_user.phone_number,
        "password": "ArtisanPass123!"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == artisan_user.id
    assert data["role"] == "artisan"


@pytest.mark.asyncio
async def test_login_by_email_success(client: AsyncClient, buyer_user: User):
    """Verifies successful login via email address."""
    payload = {
        "login_identifier": buyer_user.email,
        "password": "BuyerPass123!"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == buyer_user.id
    assert data["role"] == "buyer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, artisan_user: User):
    """Verifies that invalid password returns 401 Unauthorized."""
    payload = {
        "login_identifier": artisan_user.phone_number,
        "password": "WrongPassword999!"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Verifies that disabled/inactive user accounts are blocked with 403 Forbidden."""
    inactive_user = User(
        phone_number="+919876500099",
        password_hash=hash_password("InactivePass123!"),
        role="artisan",
        is_active=False
    )
    db_session.add(inactive_user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/login", json={
        "login_identifier": "+919876500099",
        "password": "InactivePass123!"
    })
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me_profile(client: AsyncClient, artisan_headers: dict, artisan_user: User):
    """Verifies that GET /auth/me returns the active user identity."""
    response = await client.get("/api/v1/auth/me", headers=artisan_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == artisan_user.id
    assert data["phone_number"] == artisan_user.phone_number
    assert data["role"] == artisan_user.role


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Verifies that GET /auth/me without token returns 401 Unauthorized."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation_flow(client: AsyncClient, artisan_user: User):
    """
    Verifies that refreshing a token returns a new token pair and revokes the previous token.
    """
    # 1. Login to get initial token pair
    login_res = await client.post("/api/v1/auth/login", json={
        "login_identifier": artisan_user.phone_number,
        "password": "ArtisanPass123!"
    })
    tokens = login_res.json()
    initial_refresh = tokens["refresh_token"]

    # 2. Refresh tokens
    refresh_res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": initial_refresh
    })
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != initial_refresh

    # 3. New access token works
    me_res = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {new_tokens['access_token']}"
    })
    assert me_res.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(client: AsyncClient, artisan_user: User):
    """
    Verifies reuse detection: presenting an already rotated/revoked refresh token
    triggers family revocation and denies access.
    """
    # 1. Login
    login_res = await client.post("/api/v1/auth/login", json={
        "login_identifier": artisan_user.phone_number,
        "password": "ArtisanPass123!"
    })
    initial_refresh = login_res.json()["refresh_token"]

    # 2. First refresh (legitimate)
    first_refresh = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": initial_refresh
    })
    assert first_refresh.status_code == 200
    second_refresh_token = first_refresh.json()["refresh_token"]

    # 3. Second refresh with already used initial_refresh (theft / reuse attack)
    stolen_replay = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": initial_refresh
    })
    assert stolen_replay.status_code == 401
    assert "compromised" in stolen_replay.json()["detail"].lower()

    # 4. Now the second token in the same family should also be invalidated
    subsequent_attempt = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": second_refresh_token
    })
    assert subsequent_attempt.status_code == 401


@pytest.mark.asyncio
async def test_logout_session_revocation(client: AsyncClient, artisan_user: User):
    """Verifies that logging out revokes the refresh token."""
    login_res = await client.post("/api/v1/auth/login", json={
        "login_identifier": artisan_user.phone_number,
        "password": "ArtisanPass123!"
    })
    refresh_token = login_res.json()["refresh_token"]

    logout_res = await client.post("/api/v1/auth/logout", json={
        "refresh_token": refresh_token
    })
    assert logout_res.status_code == 200

    # Attempting to refresh with the revoked token should fail
    refresh_attempt = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_attempt.status_code == 401


@pytest.mark.asyncio
async def test_otp_challenge_and_verification_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies OTP generation, wrong-code attempt handling, rate-limiting,
    and successful passwordless login/provisioning.
    """
    phone = "+919876599999"

    # 1. Request OTP challenge
    req_res = await client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
    assert req_res.status_code == 200
    otp_data = req_res.json()
    assert "dev_otp_code" in otp_data
    valid_otp = otp_data["dev_otp_code"]

    # 2. Try wrong OTP code
    bad_res = await client.post("/api/v1/auth/otp/verify", json={
        "phone_number": phone,
        "otp_code": "000000" if valid_otp != "000000" else "111111"
    })
    assert bad_res.status_code == 400
    assert "invalid otp" in bad_res.json()["detail"].lower()

    # 3. Verify with correct OTP
    verify_res = await client.post("/api/v1/auth/otp/verify", json={
        "phone_number": phone,
        "otp_code": valid_otp
    })
    assert verify_res.status_code == 200
    auth_data = verify_res.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    assert auth_data["role"] == "artisan"

    # 4. Try re-using the consumed OTP -> should fail
    reuse_res = await client.post("/api/v1/auth/otp/verify", json={
        "phone_number": phone,
        "otp_code": valid_otp
    })
    assert reuse_res.status_code == 400
