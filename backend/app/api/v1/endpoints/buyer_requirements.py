"""
SIH 26090: Buyer Requirements & AI Understanding Endpoints
Provides procurement brief creation, AI-assisted extraction staging, and human confirmation workflows.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.buyer import BuyerProfile, BuyerRequirement
from backend.app.models.requirement_understanding import RequirementUnderstanding
from backend.app.schemas.matching import (
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
    BuyerRequirementResponse,
    RequirementUnderstandingResponse,
    RequirementUnderstandingConfirmRequest
)
from backend.app.services.matching_service import MatchingService

router = APIRouter(prefix="/buyer-requirements", tags=["Buyer Requirements & RFQs"])


async def _get_current_buyer_profile(current_user: User, db: AsyncSession) -> BuyerProfile:
    res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer profile not found. Please complete profile at POST /api/v1/buyers/me."
        )
    return profile


def _format_requirement_response(req: BuyerRequirement) -> BuyerRequirementResponse:
    return BuyerRequirementResponse(
        id=req.id,
        buyer_id=req.buyer_id,
        title=req.title,
        raw_text=req.raw_text,
        target_craft_id=req.target_craft_id,
        target_category_id=req.target_category_id,
        required_quantity=req.required_quantity,
        target_unit_price_inr=req.target_unit_price_inr,
        max_budget_inr=req.max_budget_inr,
        deadline_date=req.deadline_date.isoformat() if req.deadline_date else "",
        requires_gi_certification=req.requires_gi_certification,
        desired_materials=req.desired_materials or [],
        desired_techniques=req.desired_techniques or [],
        desired_motifs=req.desired_motifs or [],
        preferred_region=req.preferred_region,
        max_acceptable_moq=req.max_acceptable_moq,
        max_lead_time_days=req.max_lead_time_days,
        requires_customization=req.requires_customization,
        quality_specifications=req.quality_specifications,
        packaging_requirements=req.packaging_requirements,
        destination_state=req.destination_state,
        destination_pincode=req.destination_pincode,
        currency=req.currency or "INR",
        status=req.status,
        has_embedding=bool(req.embedding is not None),
        embedding_model_version=req.embedding_model_version,
        data_provenance_level=req.data_provenance_level or "USER_DECLARED",
        provenance_state=req.provenance_state or "HUMAN_CONFIRMED",
        created_at=req.created_at.isoformat() if req.created_at else "",
        updated_at=req.updated_at.isoformat() if req.updated_at else ""
    )


@router.post("", response_model=BuyerRequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_buyer_requirement(
    payload: BuyerRequirementCreate,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Creates a new procurement brief / RFQ."""
    profile = await _get_current_buyer_profile(current_user, db)
    req = await MatchingService.create_requirement(db=db, buyer_id=profile.id, payload=payload)
    return _format_requirement_response(req)


@router.get("", response_model=List[BuyerRequirementResponse])
async def list_my_buyer_requirements(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists authenticated buyer's procurement requirements."""
    profile = await _get_current_buyer_profile(current_user, db)
    query = select(BuyerRequirement).where(BuyerRequirement.buyer_id == profile.id)
    if status_filter:
        query = query.where(BuyerRequirement.status == status_filter.upper())
    query = query.order_by(BuyerRequirement.created_at.desc()).offset(skip).limit(limit)

    res = await db.execute(query)
    reqs = res.scalars().all()
    return [_format_requirement_response(r) for r in reqs]


@router.get("/{requirement_id}", response_model=BuyerRequirementResponse)
async def get_buyer_requirement_detail(
    requirement_id: str,
    current_user: User = Depends(require_roles(["buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves requirement detail with strict IDOR ownership enforcement."""
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")

    user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role)
    if user_role == "buyer":
        profile = await _get_current_buyer_profile(current_user, db)
        if req.buyer_id != profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    return _format_requirement_response(req)


@router.put("/{requirement_id}", response_model=BuyerRequirementResponse)
async def update_buyer_requirement(
    requirement_id: str,
    payload: BuyerRequirementUpdate,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Updates requirement specifications."""
    profile = await _get_current_buyer_profile(current_user, db)
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
    if req.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(req, field, val)

    await db.flush()
    await MatchingService.generate_and_store_embedding(db, req)
    return _format_requirement_response(req)


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_buyer_requirement(
    requirement_id: str,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancels/closes a procurement requirement."""
    profile = await _get_current_buyer_profile(current_user, db)
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
    if req.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    req.status = "CANCELLED"
    await db.flush()
    return None


@router.post("/{requirement_id}/understand", response_model=RequirementUnderstandingResponse)
async def extract_ai_requirement_understanding(
    requirement_id: str,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Parses unstructured brief into staged structured attribute suggestions.
    Strictly preserves staging isolation.
    """
    profile = await _get_current_buyer_profile(current_user, db)
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
    if req.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    understanding = await MatchingService.extract_requirement_understanding(db, req, profile.id)
    return RequirementUnderstandingResponse(
        id=understanding.id,
        requirement_id=understanding.requirement_id,
        buyer_id=understanding.buyer_id,
        raw_input_text=understanding.raw_input_text,
        extracted_fields=understanding.extracted_fields_json,
        confidence_scores=understanding.confidence_scores_json,
        provider=understanding.provider,
        model_name=understanding.model_name,
        prompt_version=understanding.prompt_version,
        status=understanding.status,
        is_confirmed_by_buyer=understanding.is_confirmed_by_buyer,
        confirmed_fields=understanding.confirmed_fields_json,
        confirmed_at=understanding.confirmed_at.isoformat() if understanding.confirmed_at else None,
        created_at=understanding.created_at.isoformat()
    )


@router.post("/{requirement_id}/understand/confirm", response_model=BuyerRequirementResponse)
async def confirm_ai_requirement_understanding(
    requirement_id: str,
    payload: RequirementUnderstandingConfirmRequest,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Human confirmation workflow: promotes staged suggestions into canonical requirement.
    """
    profile = await _get_current_buyer_profile(current_user, db)
    res = await db.execute(select(BuyerRequirement).where(BuyerRequirement.id == requirement_id))
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
    if req.buyer_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this requirement.")

    # Find latest staged understanding
    und_res = await db.execute(
        select(RequirementUnderstanding)
        .where(
            and_(
                RequirementUnderstanding.requirement_id == requirement_id,
                RequirementUnderstanding.status == "SUGGESTED"
            )
        )
        .order_by(RequirementUnderstanding.created_at.desc())
    )
    understanding = und_res.scalars().first()
    if not understanding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending staged understanding found for this requirement. Run /understand first."
        )

    confirmed_req = await MatchingService.confirm_requirement_understanding(
        db=db,
        understanding=understanding,
        requirement=req,
        overrides=payload.overrides
    )
    return _format_requirement_response(confirmed_req)
