"""
SIH 26090: Digital Craft Passport API Endpoints
Provides Craft Passport issuance, state transitions, QR code generation,
and cryptographic provenance hashing.
"""

import base64
import hashlib
import io
import secrets
from datetime import datetime, timezone
from typing import List
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles, check_object_ownership
from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft, CraftPassport
from backend.app.schemas.passport import (
    CraftPassportCreate,
    CraftPassportResponse
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/passports", tags=["Craft Passports"])


def generate_qr_data_url(public_url: str) -> str:
    """Generates an embedded PNG Data URL containing the QR code for public verification."""
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#78350f", back_color="#fdfbf7")  # Amber branding
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@router.post("/", response_model=CraftPassportResponse, status_code=status.HTTP_201_CREATED)
async def create_draft_craft_passport(
    payload: CraftPassportCreate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Creates a new digital Craft Passport in DRAFT state for an authentic craft.
    Generates a non-sequential public passport identifier, cryptographic provenance hash,
    and a scannable QR verification link.
    """
    # 1. Fetch artisan profile
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create an artisan profile before issuing a Craft Passport."
        )

    # 2. Fetch craft from catalog
    craft_res = await db.execute(select(Craft).where(Craft.id == payload.craft_id))
    craft = craft_res.scalar_one_or_none()
    if not craft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Craft not found in catalog.")

    # 3. Generate non-sequential, unpredictable public passport UUID
    public_id = f"CP-{secrets.token_hex(8).upper()}"
    public_verification_url = f"https://artisanlinkage.in/passport/{public_id}"
    qr_data_url = generate_qr_data_url(public_verification_url)

    # 4. Generate Cryptographic Provenance Hash (Artisan + Craft + PublicID)
    provenance_payload = f"{artisan.id}:{craft.id}:{public_id}:{craft.gi_tag_number or 'NO_GI'}"
    provenance_hash = hashlib.sha256(provenance_payload.encode("utf-8")).hexdigest()

    verification_level = "GOVERNMENT_VERIFIED_GI" if craft.has_gi_tag and payload.authorized_user_gi_certificate else "SELF_DECLARED"

    passport = CraftPassport(
        artisan_id=artisan.id,
        craft_id=craft.id,
        passport_uuid=public_id,
        qr_code_url=qr_data_url,
        authorized_user_gi_certificate=payload.authorized_user_gi_certificate,
        verification_level=verification_level,
        status="DRAFT",
        provenance_hash=provenance_hash,
        is_sample_or_demo=False,
        data_provenance_level="USER_DECLARED"
    )
    db.add(passport)
    await db.flush()
    await db.refresh(passport)

    await record_audit_event(
        db=db,
        action="CRAFT_PASSPORT_CREATED",
        entity_type="CraftPassport",
        entity_id=passport.id,
        actor_user_id=current_user.id,
        payload_after={"passport_uuid": public_id, "status": "DRAFT", "craft_id": craft.id}
    )

    return CraftPassportResponse(
        id=passport.id,
        artisan_id=passport.artisan_id,
        craft_id=passport.craft_id,
        craft_name=craft.name,
        passport_uuid=passport.passport_uuid,
        qr_code_url=passport.qr_code_url,
        authorized_user_gi_certificate=passport.authorized_user_gi_certificate,
        verification_level=passport.verification_level,
        status=passport.status,
        issued_at=passport.issued_at.isoformat() if passport.issued_at else "",
        expires_at=passport.expires_at.isoformat() if passport.expires_at else None,
        provenance_hash=passport.provenance_hash
    )


@router.get("/my", response_model=List[CraftPassportResponse])
async def list_my_craft_passports(
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists all Craft Passports issued to the authenticated artisan."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        return []

    query = (
        select(CraftPassport)
        .options(selectinload(CraftPassport.craft))
        .where(CraftPassport.artisan_id == artisan.id)
        .order_by(CraftPassport.issued_at.desc())
    )
    result = await db.execute(query)
    passports = result.scalars().all()

    return [
        CraftPassportResponse(
            id=p.id,
            artisan_id=p.artisan_id,
            craft_id=p.craft_id,
            craft_name=p.craft.name if p.craft else None,
            passport_uuid=p.passport_uuid,
            qr_code_url=p.qr_code_url,
            authorized_user_gi_certificate=p.authorized_user_gi_certificate,
            verification_level=p.verification_level,
            status=p.status,
            issued_at=p.issued_at.isoformat(),
            expires_at=p.expires_at.isoformat() if p.expires_at else None,
            provenance_hash=p.provenance_hash
        )
        for p in passports
    ]


@router.post("/{passport_id}/submit", response_model=CraftPassportResponse)
async def submit_passport_for_review(
    passport_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Transitions a Craft Passport state from DRAFT to SUBMITTED for administrator review."""
    query = (
        select(CraftPassport)
        .options(selectinload(CraftPassport.craft))
        .where(CraftPassport.id == passport_id)
    )
    result = await db.execute(query)
    passport = result.scalar_one_or_none()

    if not passport:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Craft Passport not found.")

    # Object-level authorization: ensure current artisan owns this passport
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan or str(passport.artisan_id) != str(artisan.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not own this passport.")

    if passport.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit passport currently in state '{passport.status}'."
        )

    passport.status = "SUBMITTED"

    await record_audit_event(
        db=db,
        action="CRAFT_PASSPORT_SUBMITTED",
        entity_type="CraftPassport",
        entity_id=passport.id,
        actor_user_id=current_user.id,
        payload_after={"status": "SUBMITTED"}
    )

    return CraftPassportResponse(
        id=passport.id,
        artisan_id=passport.artisan_id,
        craft_id=passport.craft_id,
        craft_name=passport.craft.name if passport.craft else None,
        passport_uuid=passport.passport_uuid,
        qr_code_url=passport.qr_code_url,
        authorized_user_gi_certificate=passport.authorized_user_gi_certificate,
        verification_level=passport.verification_level,
        status=passport.status,
        issued_at=passport.issued_at.isoformat(),
        expires_at=passport.expires_at.isoformat() if passport.expires_at else None,
        provenance_hash=passport.provenance_hash
    )
