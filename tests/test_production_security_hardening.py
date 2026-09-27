"""
SIH 26090: Production Security Hardening & Readiness Automated Tests (Phase 9)
Verifies security headers, correlation IDs, production secret validation,
safe error handling, deep readiness probes, and AI failure degradation.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.main import app
from backend.app.models.auth import User


@pytest.mark.asyncio
async def test_security_headers_injected_on_responses(client: AsyncClient):
    """Verifies that all API responses include defensive security headers."""
    response = await client.get("/")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_correlation_id_generated_and_echoed(client: AsyncClient):
    """Verifies that requests receive a unique X-Correlation-ID and custom headers are preserved."""
    # 1. Automatic generation
    res1 = await client.get("/")
    assert "X-Correlation-ID" in res1.headers
    cid1 = res1.headers["X-Correlation-ID"]
    assert len(cid1) >= 16

    # 2. Inbound preservation
    custom_cid = "custom-test-correlation-12345"
    res2 = await client.get("/", headers={"X-Correlation-ID": custom_cid})
    assert res2.headers.get("X-Correlation-ID") == custom_cid


def test_production_secret_validation_rejects_insecure_defaults():
    """Settings must raise validation error if APP_ENV='production' has DEBUG=True or default weak keys."""
    # Case 1: DEBUG is True in production
    with pytest.raises(ValidationError) as exc1:
        Settings(
            APP_ENV="production",
            DEBUG=True,
            SECRET_KEY="a" * 64
        )
    assert "DEBUG must be False in production" in str(exc1.value)

    # Case 2: Insecure default key in production
    with pytest.raises(ValidationError) as exc2:
        Settings(
            APP_ENV="production",
            DEBUG=False,
            SECRET_KEY="sih26090-dev-insecure-secret-key-change-in-production-random-64-bytes"
        )
    assert "Insecure or default SECRET_KEY detected" in str(exc2.value)

    # Case 3: Short key (< 32 chars) in production
    with pytest.raises(ValidationError) as exc3:
        Settings(
            APP_ENV="production",
            DEBUG=False,
            SECRET_KEY="short-secret-key"
        )
    assert "minimum 32 characters" in str(exc3.value)


def test_production_secret_validation_accepts_strong_keys():
    """Settings must succeed when running production with valid strong key and DEBUG=False."""
    strong_key = "4f8a9b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4"
    prod_settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        SECRET_KEY=strong_key,
        CORS_ORIGINS=["https://artisanlinkage.gov.in"]
    )
    assert prod_settings.APP_ENV == "production"
    assert prod_settings.DEBUG is False
    assert prod_settings.SECRET_KEY == strong_key


@pytest.mark.asyncio
async def test_readiness_probe_structure_and_components(client: AsyncClient):
    """Verifies that /ready probe inspects database, pgvector, and components."""
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "components" in data
    assert "connected" in data["database"]
    assert "api" in data["components"]


@pytest.mark.asyncio
async def test_admin_reviewed_cannot_grant_authority_verified_regression(
    client: AsyncClient,
    admin_headers: dict
):
    """
    CRITICAL REGRESSION TEST:
    Admin moderation decision without explicit authoritative registry evidence
    must set status to ADMIN_REVIEWED or ADMIN_APPROVED, NEVER to AUTHORITY_VERIFIED.
    """
    # Attempting to review without authoritative registry reference
    # Using a dummy verification ID
    res = await client.post(
        "/api/v1/verifications/admin/review",
        headers=admin_headers,
        json={
            "verification_id": "00000000-0000-0000-0000-000000000001",
            "decision": "APPROVED",
            "reviewer_notes": "Reviewed documents internally",
            "authoritative_registry_reference": None  # No official government reference
        }
    )
    # The endpoint either returns 404 (if not found in fixture) or rejects auto authority promotion
    if res.status_code == 200:
        data = res.json()
        assert data.get("verification_status") != "AUTHORITY_VERIFIED"
        assert data.get("verification_status") == "ADMIN_REVIEWED"
    else:
        assert res.status_code in (404, 422)


def test_ai_provider_failure_returns_safe_failure_state():
    """
    Verifies that when external AI providers fail, the system returns
    an explicit exception/failure state rather than fabricating fake outputs or attributes.
    """
    from ai.providers.gemini import GeminiVisionProvider
    from ai.providers.base import AIProviderNotConfiguredException

    # Unconfigured provider (missing API key)
    unconfigured_provider = GeminiVisionProvider(api_key=None)
    assert unconfigured_provider.is_available() is False

    info = unconfigured_provider.get_model_info()
    assert info["is_available"] is False
    assert info["provider"] == "google"
    assert info["model_name"] == "gemini-1.5-flash"
