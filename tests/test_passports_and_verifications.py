"""
SIH 26090: Digital Craft Passport & Admin Verification Automated Tests
Tests passport issuance, QR code generation, cryptographic provenance hashes,
public verification resolving without PII, artisan document submissions, and audited admin review.
"""

import pytest
from httpx import AsyncClient
from backend.app.models.craft import Craft


@pytest.mark.asyncio
async def test_passport_lifecycle_and_public_verification(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """
    Tests passport issuance, QR generation, provenance hash,
    and public QR code resolution without authentication.
    """
    # 1. Issuance fails before artisan profile exists
    r_no_prof = await client.post("/api/v1/passports/", headers=artisan_headers, json={
        "craft_id": seed_craft.id
    })
    assert r_no_prof.status_code == 400
    assert "must create an artisan profile" in r_no_prof.json()["detail"].lower()

    # 2. Create artisan profile
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Kailash Weavers",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 50
    })

    # 3. Create Draft Passport
    passport_payload = {
        "craft_id": seed_craft.id,
        "authorized_user_gi_certificate": "GI-AU-2026-MP-001"
    }
    r_pass = await client.post("/api/v1/passports/", headers=artisan_headers, json=passport_payload)
    assert r_pass.status_code == 201
    p_data = r_pass.json()

    assert p_data["status"] == "DRAFT"
    assert p_data["passport_uuid"].startswith("CP-")
    assert p_data["qr_code_url"].startswith("data:image/png;base64,")
    assert len(p_data["provenance_hash"]) == 64  # SHA-256 hex
    assert p_data["craft_name"] == "Chanderi Silk Saree"
    public_id = p_data["passport_uuid"]
    passport_id = p_data["id"]

    # 4. List my passports
    r_my = await client.get("/api/v1/passports/my", headers=artisan_headers)
    assert r_my.status_code == 200
    assert len(r_my.json()) == 1
    assert r_my.json()[0]["id"] == passport_id

    # 5. Public verification endpoint (Guest / Buyer scan)
    r_public = await client.get(f"/api/v1/public/passports/{public_id}")
    assert r_public.status_code == 200
    pub_data = r_public.json()

    assert pub_data["passport_uuid"] == public_id
    assert pub_data["craft_name"] == "Chanderi Silk Saree"
    assert pub_data["origin_state"] == "Madhya Pradesh"
    assert pub_data["origin_district"] == "Ashoknagar"
    assert pub_data["has_gi_tag"] is True
    assert pub_data["gi_tag_number"] == "GI-007"
    assert pub_data["provenance_hash"] == p_data["provenance_hash"]
    assert pub_data["is_valid"] is True

    # Ensure no PII leakage in public verification
    assert "phone_number" not in pub_data
    assert "address_line" not in pub_data
    assert "bank_account" not in pub_data


@pytest.mark.asyncio
async def test_verification_workflow_and_admin_approval(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Tests complete verification workflow:
    1. Artisan creates profile and draft passport
    2. Artisan submits verification document (KYC / GI Certificate)
    3. Passports automatically shift to UNDER_REVIEW
    4. Admin lists pending verifications
    5. Admin reviews and APPROVES verification
    6. Artisan profile and passports transition to VERIFIED
    """
    # 1. Setup profile and passport
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Meera Devi",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 20
    })

    pass_res = await client.post("/api/v1/passports/", headers=artisan_headers, json={
        "craft_id": seed_craft.id,
        "authorized_user_gi_certificate": "GI-AU-2026-MP-002"
    })
    passport_id = pass_res.json()["id"]

    # 2. Artisan submits verification document
    verif_res = await client.post("/api/v1/verifications/submit", headers=artisan_headers, json={
        "document_type": "GI_AUTHORIZED_USER_CERT",
        "document_url": "https://storage.artisanlinkage.in/docs/gi_cert_002.pdf"
    })
    assert verif_res.status_code == 201
    verif_id = verif_res.json()["id"]
    assert verif_res.json()["verification_status"] == "SUBMITTED"

    # 3. Check passport moved to UNDER_REVIEW
    my_passports = await client.get("/api/v1/passports/my", headers=artisan_headers)
    assert my_passports.json()[0]["status"] == "UNDER_REVIEW"

    # 4. Admin checks pending verifications
    admin_list = await client.get("/api/v1/verifications/admin/pending", headers=admin_headers)
    assert admin_list.status_code == 200
    pending_ids = [item["id"] for item in admin_list.json()]
    assert verif_id in pending_ids

    # 5. Admin APPROVES verification
    review_res = await client.post(f"/api/v1/verifications/admin/{verif_id}/review", headers=admin_headers, json={
        "decision": "APPROVE",
        "admin_notes": "GI registry records validated and approved for Chanderi cluster."
    })
    assert review_res.status_code == 200
    assert review_res.json()["verification_status"] == "VERIFIED_APPROVED"
    assert review_res.json()["admin_notes"] == "GI registry records validated and approved for Chanderi cluster."

    # 6. Verify Artisan Profile updated
    art_prof = await client.get("/api/v1/artisans/me", headers=artisan_headers)
    assert art_prof.json()["verification_status"] == "GOVERNMENT_VERIFIED_GI"

    # 7. Verify Passport updated to VERIFIED
    updated_passports = await client.get("/api/v1/passports/my", headers=artisan_headers)
    assert updated_passports.json()[0]["status"] == "VERIFIED"
    assert updated_passports.json()[0]["verification_level"] == "GOVERNMENT_VERIFIED_GI"


@pytest.mark.asyncio
async def test_admin_rejection_workflow(
    client: AsyncClient,
    artisan_headers: dict,
    admin_headers: dict,
    seed_craft: Craft
):
    """
    Tests administrative rejection flow:
    1. Artisan submits verification
    2. Admin rejects with specific feedback note
    3. Associated passports transition to REJECTED
    4. Artisan can resubmit passport after rectification
    """
    # 1. Setup profile and passport
    await client.post("/api/v1/artisans/me", headers=artisan_headers, json={
        "full_name": "Resubmitting Artisan",
        "state": "Madhya Pradesh",
        "district": "Ashoknagar",
        "pincode": "473446",
        "primary_craft_id": seed_craft.id,
        "monthly_production_capacity": 10
    })

    pass_res = await client.post("/api/v1/passports/", headers=artisan_headers, json={
        "craft_id": seed_craft.id
    })
    passport_id = pass_res.json()["id"]

    # 2. Submit verification
    verif_res = await client.post("/api/v1/verifications/submit", headers=artisan_headers, json={
        "document_type": "PEHCHAN_CARD",
        "document_url": "https://storage.artisanlinkage.in/docs/pehchan_blurred.jpg"
    })
    verif_id = verif_res.json()["id"]

    # 3. Admin rejects due to illegible scan
    review_res = await client.post(f"/api/v1/verifications/admin/{verif_id}/review", headers=admin_headers, json={
        "decision": "REJECT",
        "rejection_reason": "Pehchan card image is unreadable. Please upload a high-resolution scan.",
        "admin_notes": "Illegible document scan."
    })
    assert review_res.status_code == 200
    assert review_res.json()["verification_status"] == "REJECTED"
    assert "unreadable" in review_res.json()["rejection_reason"]

    # 4. Check passport status updated to REJECTED
    passports = await client.get("/api/v1/passports/my", headers=artisan_headers)
    assert passports.json()[0]["status"] == "REJECTED"

    # 5. Artisan can resubmit the rejected passport
    resubmit_res = await client.post(f"/api/v1/passports/{passport_id}/submit", headers=artisan_headers)
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "SUBMITTED"
