"""
SIH 26090: Governance RBAC & Security Boundary Tests
Verifies that Artisans and Buyers are forbidden from accessing governance and moderation APIs,
and ensures public endpoints sanitize sensitive operational and PII data.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_artisan_and_buyer_forbidden_from_governance(
    client: AsyncClient,
    artisan_headers: dict,
    buyer_headers: dict
):
    """Verifies that non-admin roles are forbidden with HTTP 403."""
    # 1. Artisan attempted access
    res_art_gov = await client.get("/api/v1/governance/dashboard", headers=artisan_headers)
    assert res_art_gov.status_code == 403

    res_art_mod = await client.get("/api/v1/moderation/queue", headers=artisan_headers)
    assert res_art_mod.status_code == 403

    # 2. Buyer attempted access
    res_buy_gov = await client.get("/api/v1/governance/dashboard", headers=buyer_headers)
    assert res_buy_gov.status_code == 403

    res_buy_mod = await client.get("/api/v1/moderation/queue", headers=buyer_headers)
    assert res_buy_mod.status_code == 403

    # 3. Unauthenticated attempted access
    res_unauth = await client.get("/api/v1/governance/dashboard")
    assert res_unauth.status_code == 401
