"""
SIH 26090: Artisan Profile API Endpoints
Provides private /me profile management with object authorization and sanitized public profile views.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import get_current_active_user, require_roles
from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft
from backend.app.schemas.artisan import (
    ArtisanProfileCreate,
    ArtisanProfileUpdate,
    ArtisanProfileResponse,
    ArtisanPublicProfileResponse
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/artisans", tags=["Artisans"])


@router.get("/me", response_model=ArtisanProfileResponse)
async def get_my_artisan_profile(
    current_user: User = Depends(require_roles(["artisan", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves full private profile details for the authenticated artisan."""
    query = select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan profile has not been created yet. Please complete onboarding at POST /api/v1/artisans/me."
        )

    return ArtisanProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        cooperative_name=profile.cooperative_name,
        state=profile.state,
        district=profile.district,
        pincode=profile.pincode,
        address_line=profile.address_line,
        primary_craft_id=profile.primary_craft_id,
        years_of_experience=profile.years_of_experience,
        monthly_production_capacity=profile.monthly_production_capacity,
        pehchan_id=profile.pehchan_id,
        verification_status=profile.verification_status,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat()
    )


@router.post("/me", response_model=ArtisanProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_my_artisan_profile(
    payload: ArtisanProfileCreate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Creates initial artisan profile for authenticated user."""
    # Check if profile already exists
    existing = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artisan profile already exists. Use PUT /api/v1/artisans/me to update."
        )

    # Verify primary craft exists
    craft_res = await db.execute(select(Craft).where(Craft.id == payload.primary_craft_id))
    if not craft_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specified primary_craft_id '{payload.primary_craft_id}' does not exist in master catalog."
        )

    profile = ArtisanProfile(
        user_id=current_user.id,
        full_name=payload.full_name,
        cooperative_name=payload.cooperative_name,
        state=payload.state,
        district=payload.district,
        pincode=payload.pincode,
        address_line=payload.address_line,
        primary_craft_id=payload.primary_craft_id,
        years_of_experience=payload.years_of_experience,
        monthly_production_capacity=payload.monthly_production_capacity,
        pehchan_id=payload.pehchan_id,
        verification_status="PENDING",
        is_sample_or_demo=False,
        data_provenance_level="USER_DECLARED"
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    await record_audit_event(
        db=db,
        action="ARTISAN_PROFILE_CREATED",
        entity_type="ArtisanProfile",
        entity_id=profile.id,
        actor_user_id=current_user.id,
        payload_after={"full_name": profile.full_name, "district": profile.district}
    )

    return ArtisanProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        cooperative_name=profile.cooperative_name,
        state=profile.state,
        district=profile.district,
        pincode=profile.pincode,
        address_line=profile.address_line,
        primary_craft_id=profile.primary_craft_id,
        years_of_experience=profile.years_of_experience,
        monthly_production_capacity=profile.monthly_production_capacity,
        pehchan_id=profile.pehchan_id,
        verification_status=profile.verification_status,
        created_at=profile.created_at.isoformat() if profile.created_at else "",
        updated_at=profile.updated_at.isoformat() if profile.updated_at else ""
    )


@router.put("/me", response_model=ArtisanProfileResponse)
async def update_my_artisan_profile(
    payload: ArtisanProfileUpdate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Updates profile attributes for the authenticated artisan."""
    query = select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan profile not found. Please create profile first."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)

    await record_audit_event(
        db=db,
        action="ARTISAN_PROFILE_UPDATED",
        entity_type="ArtisanProfile",
        entity_id=profile.id,
        actor_user_id=current_user.id,
        payload_after=update_data
    )

    return ArtisanProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        cooperative_name=profile.cooperative_name,
        state=profile.state,
        district=profile.district,
        pincode=profile.pincode,
        address_line=profile.address_line,
        primary_craft_id=profile.primary_craft_id,
        years_of_experience=profile.years_of_experience,
        monthly_production_capacity=profile.monthly_production_capacity,
        pehchan_id=profile.pehchan_id,
        verification_status=profile.verification_status,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat()
    )


@router.get("/{artisan_id}/public", response_model=ArtisanPublicProfileResponse)
async def get_public_artisan_profile(
    artisan_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public sanitized profile view for buyers and guests.
    Strictly omits private telephone numbers, bank details, and home street address.
    """
    query = (
        select(ArtisanProfile)
        .options(selectinload(ArtisanProfile.primary_craft))
        .where(ArtisanProfile.id == artisan_id)
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan not found.")

    craft_title = profile.primary_craft.name if profile.primary_craft else None

    return ArtisanPublicProfileResponse(
        id=profile.id,
        full_name=profile.full_name,
        state=profile.state,
        district=profile.district,
        craft_name=craft_title,
        years_of_experience=profile.years_of_experience,
        verification_status=profile.verification_status
    )
