"""
SIH 26090: Artisan-Craft Association API Endpoints
Provides many-to-many relationship management between artisans and crafts,
tracking skill tiers (MASTER_CRAFTSMAN, SKILLED, APPRENTICE) and master techniques.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile, ArtisanCraft
from backend.app.models.craft import Craft
from backend.app.schemas.craft import ArtisanCraftLinkRequest, ArtisanCraftResponse
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/artisans/me/crafts", tags=["Artisan Crafts Association"])


@router.get("", response_model=List[ArtisanCraftResponse])
async def list_my_craft_specializations(
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists all crafts practiced by the authenticated artisan with skill tiers and experience."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan profile not found. Please create profile first."
        )

    stmt = (
        select(ArtisanCraft)
        .options(selectinload(ArtisanCraft.craft))
        .where(ArtisanCraft.artisan_id == artisan.id)
        .order_by(ArtisanCraft.is_primary.desc(), ArtisanCraft.created_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        ArtisanCraftResponse(
            id=r.id,
            artisan_id=r.artisan_id,
            craft_id=r.craft_id,
            craft_name=r.craft.name if r.craft else None,
            skill_level=r.skill_level,
            years_of_experience=r.years_of_experience,
            is_primary=r.is_primary,
            technique=r.technique,
            evidence_url=r.evidence_url,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else ""
        )
        for r in records
    ]


@router.post("", response_model=ArtisanCraftResponse, status_code=status.HTTP_201_CREATED)
async def link_craft_to_artisan(
    payload: ArtisanCraftLinkRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Associates an authentic craft with the authenticated artisan profile."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan profile not found. Please create profile first."
        )

    # Verify craft exists
    craft_res = await db.execute(select(Craft).where(Craft.id == payload.craft_id))
    craft = craft_res.scalar_one_or_none()
    if not craft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specified craft_id '{payload.craft_id}' does not exist in master directory."
        )

    # Check if already linked
    existing = await db.execute(
        select(ArtisanCraft).where(
            and_(
                ArtisanCraft.artisan_id == artisan.id,
                ArtisanCraft.craft_id == payload.craft_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already registered this craft specialization."
        )

    assoc = ArtisanCraft(
        artisan_id=artisan.id,
        craft_id=payload.craft_id,
        skill_level=payload.skill_level,
        years_of_experience=payload.years_of_experience,
        is_primary=payload.is_primary,
        technique=payload.technique,
        evidence_url=payload.evidence_url,
        status="ACTIVE"
    )
    db.add(assoc)
    await db.flush()
    await db.refresh(assoc)

    await record_audit_event(
        db=db,
        action="ARTISAN_CRAFT_LINKED",
        entity_type="ArtisanCraft",
        entity_id=assoc.id,
        actor_user_id=current_user.id,
        payload_after={"craft_name": craft.name, "skill_level": payload.skill_level}
    )

    return ArtisanCraftResponse(
        id=assoc.id,
        artisan_id=assoc.artisan_id,
        craft_id=assoc.craft_id,
        craft_name=craft.name,
        skill_level=assoc.skill_level,
        years_of_experience=assoc.years_of_experience,
        is_primary=assoc.is_primary,
        technique=assoc.technique,
        evidence_url=assoc.evidence_url,
        status=assoc.status,
        created_at=assoc.created_at.isoformat() if assoc.created_at else ""
    )


@router.delete("/{craft_id}", status_code=status.HTTP_200_OK)
async def unlink_craft_from_artisan(
    craft_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Unlinks a craft specialization from the authenticated artisan profile."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = select(ArtisanCraft).where(
        and_(
            ArtisanCraft.artisan_id == artisan.id,
            ArtisanCraft.craft_id == craft_id
        )
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Craft association not found.")

    await db.delete(record)
    await db.flush()

    await record_audit_event(
        db=db,
        action="ARTISAN_CRAFT_UNLINKED",
        entity_type="ArtisanCraft",
        entity_id=record.id,
        actor_user_id=current_user.id,
        payload_after={"craft_id": craft_id}
    )

    return {"message": "Craft association unlinked successfully."}
