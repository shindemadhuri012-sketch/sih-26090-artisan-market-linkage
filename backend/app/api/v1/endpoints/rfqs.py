"""
SIH 26090: RFQ & Commercial Negotiation Endpoints
Provides multi-party RFQ dispatch, viewing, counter-offers, and commercial agreement lifecycle.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.buyer import BuyerProfile, BuyerRequirement, Match
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.market import Enquiry
from backend.app.models.product import Product
from backend.app.schemas.matching import (
    RFQCreateRequest,
    RFQResponseRequest,
    RFQBuyerDecisionRequest,
    RFQResponse
)
from backend.app.services.rfq_service import RFQService

router = APIRouter(prefix="/rfqs", tags=["Commercial RFQ & Enquiry Linkage"])


def _format_rfq_response(enquiry: Enquiry) -> RFQResponse:
    prod = enquiry.product
    buyer = enquiry.buyer
    artisan = enquiry.artisan

    return RFQResponse(
        id=enquiry.id,
        rfq_reference_number=enquiry.rfq_reference_number,
        buyer_id=enquiry.buyer_id,
        artisan_id=enquiry.artisan_id,
        requirement_id=enquiry.requirement_id,
        product_id=enquiry.product_id,
        match_id=enquiry.match_id,
        message=enquiry.message,
        proposed_quantity=enquiry.proposed_quantity,
        proposed_unit_price=enquiry.proposed_unit_price,
        currency=enquiry.currency or "INR",
        status=enquiry.status,
        artisan_response_message=enquiry.artisan_response_message,
        counter_unit_price=enquiry.counter_unit_price,
        counter_lead_time_days=enquiry.counter_lead_time_days,
        decline_reason=enquiry.decline_reason,
        product_title=prod.title if prod else None,
        buyer_company_name=buyer.company_name if buyer else None,
        artisan_name=artisan.full_name if artisan else None,
        viewed_at=enquiry.viewed_at.isoformat() if enquiry.viewed_at else None,
        responded_at=enquiry.responded_at.isoformat() if enquiry.responded_at else None,
        expires_at=enquiry.expires_at.isoformat() if enquiry.expires_at else None,
        created_at=enquiry.created_at.isoformat() if enquiry.created_at else "",
        updated_at=enquiry.updated_at.isoformat() if enquiry.updated_at else ""
    )


@router.post("", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq_enquiry(
    payload: RFQCreateRequest,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Creates and dispatches an RFQ to an artisan."""
    b_res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    buyer_profile = b_res.scalar_one_or_none()
    if not buyer_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found.")

    # Validate target artisan exists
    a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.id == payload.artisan_id))
    if not a_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target artisan profile not found.")

    enquiry = await RFQService.create_rfq(db, buyer_profile.id, payload)

    # Re-query with eager relationships
    q = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.id == enquiry.id)
    )
    res = await db.execute(q)
    full_enquiry = res.scalar_one()
    return _format_rfq_response(full_enquiry)


@router.get("/sent", response_model=List[RFQResponse])
async def list_sent_rfqs(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists RFQs dispatched by the authenticated buyer."""
    b_res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    buyer_profile = b_res.scalar_one_or_none()
    if not buyer_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found.")

    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.buyer_id == buyer_profile.id)
    )
    if status_filter:
        query = query.where(Enquiry.status == status_filter.upper())
    query = query.order_by(Enquiry.created_at.desc()).offset(skip).limit(limit)

    res = await db.execute(query)
    enquiries = res.scalars().all()
    return [_format_rfq_response(e) for e in enquiries]


@router.get("/incoming", response_model=List[RFQResponse])
async def list_incoming_rfqs(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists RFQs received by the authenticated artisan."""
    a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan_profile = a_res.scalar_one_or_none()
    if not artisan_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.artisan_id == artisan_profile.id)
    )
    if status_filter:
        query = query.where(Enquiry.status == status_filter.upper())
    query = query.order_by(Enquiry.created_at.desc()).offset(skip).limit(limit)

    res = await db.execute(query)
    enquiries = res.scalars().all()
    return [_format_rfq_response(e) for e in enquiries]


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq_detail(
    rfq_id: str,
    current_user: User = Depends(require_roles(["buyer", "artisan", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves RFQ details with strict party-to-transaction IDOR verification."""
    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.id == rfq_id)
    )
    res = await db.execute(query)
    enquiry = res.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")

    # Party-to-transaction verification
    user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role)
    if user_role == "buyer":
        b_res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
        buyer = b_res.scalar_one_or_none()
        if not buyer or enquiry.buyer_id != buyer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not party to this RFQ.")
    elif user_role == "artisan":
        a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
        artisan = a_res.scalar_one_or_none()
        if not artisan or enquiry.artisan_id != artisan.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not party to this RFQ.")

    return _format_rfq_response(enquiry)


@router.post("/{rfq_id}/view", response_model=RFQResponse)
async def mark_rfq_viewed(
    rfq_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Marks RFQ as VIEWED when opened by the recipient artisan."""
    a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = a_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.id == rfq_id)
    )
    res = await db.execute(query)
    enquiry = res.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")
    if enquiry.artisan_id != artisan.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: RFQ is not addressed to you.")

    updated = await RFQService.mark_rfq_viewed(db, enquiry, artisan.id)
    return _format_rfq_response(updated)


@router.post("/{rfq_id}/respond", response_model=RFQResponse)
async def artisan_respond_to_rfq(
    rfq_id: str,
    payload: RFQResponseRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Artisan responds to RFQ with ACCEPT, DECLINE, or COUNTER_OFFER."""
    a_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = a_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan profile not found.")

    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.id == rfq_id)
    )
    res = await db.execute(query)
    enquiry = res.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")
    if enquiry.artisan_id != artisan.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: RFQ is not addressed to you.")

    if enquiry.status in {"ACCEPTED", "DECLINED", "CANCELLED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to RFQ with terminal status '{enquiry.status}'."
        )

    updated = await RFQService.artisan_respond(db, enquiry, artisan.id, payload)
    return _format_rfq_response(updated)


@router.post("/{rfq_id}/buyer-decision", response_model=RFQResponse)
async def buyer_decision_on_counter_offer(
    rfq_id: str,
    payload: RFQBuyerDecisionRequest,
    current_user: User = Depends(require_roles(["buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Buyer accepts or declines an artisan counter-offer."""
    b_res = await db.execute(select(BuyerProfile).where(BuyerProfile.user_id == current_user.id))
    buyer = b_res.scalar_one_or_none()
    if not buyer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found.")

    query = (
        select(Enquiry)
        .options(selectinload(Enquiry.product), selectinload(Enquiry.buyer), selectinload(Enquiry.artisan))
        .where(Enquiry.id == rfq_id)
    )
    res = await db.execute(query)
    enquiry = res.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")
    if enquiry.buyer_id != buyer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this RFQ.")

    if enquiry.status != "NEGOTIATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot make decision on RFQ with status '{enquiry.status}'. Only NEGOTIATION is valid."
        )

    try:
        updated = await RFQService.buyer_decision(db, enquiry, buyer.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _format_rfq_response(updated)
