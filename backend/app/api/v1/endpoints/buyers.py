"""
SIH 26090: Buyer Profile API Endpoints
Provides private /me profile management for institutional and retail buyers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.buyer import BuyerProfile
from backend.app.schemas.buyer import (
    BuyerProfileCreate,
    BuyerProfileUpdate,
    BuyerProfileResponse
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.get("/me", response_model=BuyerProfileResponse)
async def get_my_buyer_profile(
    current_user: User = Depends(require_roles(["buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves authenticated buyer's procurement profile."""
    query = select(BuyerProfile).where(BuyerProfile.user_id == current_user.id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer profile has not been created yet. Complete profile at POST /api/v1/buyers/me."
        )

    return BuyerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        buyer_type=profile.buyer_type,
        gstin=profile.gstin,
        country=profile.country,
        state=profile.state,
        typical_order_volume=profile.typical_order_volume,
        is_verified_buyer=profile.is_verified_buyer,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat()
    )


@router.post("/me", response_model=BuyerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_my_buyer_profile(
    payload: BuyerProfileCreate,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Creates initial buyer procurement profile for authenticated user."""
    existing = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Buyer profile already exists. Use PUT /api/v1/buyers/me to update."
        )

    profile = BuyerProfile(
        user_id=current_user.id,
        company_name=payload.company_name,
        buyer_type=payload.buyer_type,
        gstin=payload.gstin,
        country=payload.country,
        state=payload.state,
        typical_order_volume=payload.typical_order_volume,
        is_verified_buyer=False,
        is_sample_or_demo=False,
        data_provenance_level="USER_DECLARED"
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    await record_audit_event(
        db=db,
        action="BUYER_PROFILE_CREATED",
        entity_type="BuyerProfile",
        entity_id=profile.id,
        actor_user_id=current_user.id,
        payload_after={"company_name": profile.company_name, "buyer_type": profile.buyer_type}
    )

    return BuyerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        buyer_type=profile.buyer_type,
        gstin=profile.gstin,
        country=profile.country,
        state=profile.state,
        typical_order_volume=profile.typical_order_volume,
        is_verified_buyer=profile.is_verified_buyer,
        created_at=profile.created_at.isoformat() if profile.created_at else "",
        updated_at=profile.updated_at.isoformat() if profile.updated_at else ""
    )


@router.put("/me", response_model=BuyerProfileResponse)
async def update_my_buyer_profile(
    payload: BuyerProfileUpdate,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Updates buyer procurement profile attributes."""
    query = select(BuyerProfile).where(BuyerProfile.user_id == current_user.id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer profile not found. Please create profile first."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)

    await record_audit_event(
        db=db,
        action="BUYER_PROFILE_UPDATED",
        entity_type="BuyerProfile",
        entity_id=profile.id,
        actor_user_id=current_user.id,
        payload_after=update_data
    )

    return BuyerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        buyer_type=profile.buyer_type,
        gstin=profile.gstin,
        country=profile.country,
        state=profile.state,
        typical_order_volume=profile.typical_order_volume,
        is_verified_buyer=profile.is_verified_buyer,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat()
    )
