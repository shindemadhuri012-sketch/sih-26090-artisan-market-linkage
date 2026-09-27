"""
SIH 26090: Smart Matching Endpoints
Provides match execution, candidate ranking, scorecard retrieval, and explainability exploration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.buyer import BuyerProfile, BuyerRequirement, Match, MatchExplanation
from backend.app.models.product import Product
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft
from backend.app.schemas.matching import MatchScorecardResponse
from backend.app.services.matching_service import MatchingService

router = APIRouter(prefix="/matches", tags=["Smart Matching Engine"])


async def _get_current_buyer_profile(current_user: User, db: AsyncSession) -> BuyerProfile:
    res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found.")
    return profile


def _format_match_scorecard(match: Match) -> MatchScorecardResponse:
    prod = match.product
    artisan = match.artisan
    craft = prod.craft if prod and prod.craft else (artisan.primary_craft if artisan else None)
    exp = match.explanation

    return MatchScorecardResponse(
        id=match.id,
        requirement_id=match.requirement_id,
        artisan_id=match.artisan_id,
        product_id=match.product_id,
        composite_score=match.composite_score,
        semantic_similarity=match.semantic_similarity,
        craft_compatibility=match.craft_compatibility,
        material_compatibility=match.material_compatibility,
        technique_compatibility=match.technique_compatibility,
        capacity_compatibility=match.capacity_compatibility,
        price_compatibility=match.price_compatibility,
        lead_time_compatibility=match.lead_time_compatibility,
        provenance_bonus=match.provenance_bonus,
        rank=match.rank,
        status=match.status,
        data_sufficiency_state=match.data_sufficiency_state,
        engine_version=match.engine_version,
        product_title=prod.title if prod else None,
        product_sku=prod.sku if prod else None,
        product_price_inr=prod.price_inr if prod else None,
        artisan_name=artisan.full_name if artisan else None,
        artisan_state=artisan.state if artisan else None,
        artisan_district=artisan.district if artisan else None,
        craft_name=craft.name if craft else None,
        positive_reasons=exp.positive_reasons if exp else [],
        limitations=exp.limitations if exp else [],
        summary_explanation=exp.summary_explanation if exp else None,
        capacity_justification=exp.capacity_justification if exp else None,
        price_justification=exp.price_justification if exp else None,
        provenance_justification=exp.provenance_justification if exp else None,
        created_at=match.created_at.isoformat() if match.created_at else ""
    )


@router.post("/requirements/{requirement_id}/run", response_model=List[MatchScorecardResponse])
async def execute_matching_run(
    requirement_id: str,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Executes two-stage hybrid matching for a buyer requirement.
    Evaluates hard constraints, vector semantic retrieval, and multi-criteria scoring.
    """
    profile = await _get_current_buyer_profile(current_user, db)
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
    if req.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    created_matches = await MatchingService.run_matches(db, req, limit=limit)

    # Re-query with eager relationships loaded
    match_ids = [m.id for m in created_matches]
    if not match_ids:
        return []

    detail_query = (
        select(Match)
        .options(
            selectinload(Match.product).selectinload(Product.craft),
            selectinload(Match.artisan),
            selectinload(Match.explanation)
        )
        .where(Match.id.in_(match_ids))
        .order_by(Match.rank.asc())
    )
    detail_res = await db.execute(detail_query)
    full_matches = detail_res.scalars().all()

    return [_format_match_scorecard(m) for m in full_matches]


@router.get("/requirements/{requirement_id}", response_model=List[MatchScorecardResponse])
async def list_matches_for_requirement(
    requirement_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_roles(["buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists ranked matches with scorecards for a buyer requirement."""
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")

    user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role)
    if user_role == "buyer":
        profile = await _get_current_buyer_profile(current_user, db)
        if req.buyer_id != profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    query = (
        select(Match)
        .options(
            selectinload(Match.product).selectinload(Product.craft),
            selectinload(Match.artisan),
            selectinload(Match.explanation)
        )
        .where(
            and_(
                Match.requirement_id == requirement_id,
                Match.is_dismissed_by_buyer == False
            )
        )
        .order_by(Match.rank.asc())
        .offset(skip)
        .limit(limit)
    )
    m_res = await db.execute(query)
    matches = m_res.scalars().all()
    return [_format_match_scorecard(m) for m in matches]


@router.get("/{match_id}", response_model=MatchScorecardResponse)
async def get_match_detail(
    match_id: str,
    current_user: User = Depends(require_roles(["buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves detailed scorecard and full explainability factors for a specific match."""
    query = (
        select(Match)
        .options(
            selectinload(Match.product).selectinload(Product.craft),
            selectinload(Match.artisan),
            selectinload(Match.explanation),
            selectinload(Match.requirement)
        )
        .where(Match.id == match_id)
    )
    res = await db.execute(query)
    match = res.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

    user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role)
    if user_role == "buyer":
        profile = await _get_current_buyer_profile(current_user, db)
        if match.requirement.buyer_id != profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this match.")

    return _format_match_scorecard(match)


@router.post("/{match_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_match_candidate(
    match_id: str,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Dismisses a match from buyer's active view."""
    profile = await _get_current_buyer_profile(current_user, db)
    query = (
        select(Match)
        .options(selectinload(Match.requirement))
        .where(Match.id == match_id)
    )
    res = await db.execute(query)
    match = res.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
    if match.requirement.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this match.")

    match.is_dismissed_by_buyer = True
    await db.flush()
    return None
