"""
SIH 26090: Public Verification API Endpoints
Provides open, unauthenticated public verification for digital Craft Passports (QR code target).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.models.craft import CraftPassport
from backend.app.schemas.passport import PublicPassportVerificationResponse

router = APIRouter(prefix="/public", tags=["Public Verification"])


@router.get("/passports/{public_id}", response_model=PublicPassportVerificationResponse)
async def verify_passport_publicly(
    public_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public QR verification endpoint.
    Exposes authentic craft credentials, GI registration, and artisan public name.
    Strictly omits private phone numbers, home addresses, or internal security tokens.
    """
    query = (
        select(CraftPassport)
        .options(
            selectinload(CraftPassport.craft),
            selectinload(CraftPassport.artisan)
        )
        .where(CraftPassport.passport_uuid == public_id.upper())
    )
    result = await db.execute(query)
    passport = result.scalar_one_or_none()

    if not passport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Craft Passport '{public_id}' is not recognized or does not exist."
        )

    craft = passport.craft
    artisan = passport.artisan

    return PublicPassportVerificationResponse(
        passport_uuid=passport.passport_uuid,
        status=passport.status,
        verification_level=passport.verification_level,
        issued_at=passport.issued_at.isoformat(),
        artisan_public_name=artisan.full_name if artisan else "Registered Artisan",
        craft_name=craft.name if craft else "Indian Traditional Craft",
        origin_state=craft.origin_state if craft else "India",
        origin_district=craft.origin_district if craft else "Cluster Hub",
        gi_tag_number=craft.gi_tag_number if craft else None,
        has_gi_tag=craft.has_gi_tag if craft else False,
        cultural_heritage_description=craft.cultural_heritage_description if craft else "",
        traditional_raw_materials=craft.traditional_raw_materials if craft else [],
        provenance_hash=passport.provenance_hash,
        is_valid=(passport.status != "REJECTED" and passport.status != "EXPIRED"),
        provenance_metadata=craft.provenance_metadata if craft else {}
    )
