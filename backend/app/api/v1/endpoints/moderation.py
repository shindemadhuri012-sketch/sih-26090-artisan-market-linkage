"""
SIH 26090: Unified Moderation API Endpoints
Provides multi-entity review queues, idempotent moderation decisions,
and transparent feedback mechanisms.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.services.moderation_service import ModerationService
from backend.app.schemas.governance import (
    ModerationDecisionRequest,
    ModerationActionResponse,
    ModerationQueueListResponse,
    ModerationQueueItemResponse
)

router = APIRouter(prefix="/moderation", tags=["Moderation"])


@router.get("/queue", response_model=ModerationQueueListResponse)
async def get_moderation_queue(
    entity_type: str = Query("PRODUCT", description="PRODUCT, VERIFICATION, PASSPORT"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Administrator / Moderator view: lists pending submissions across product listings,
    artisan credentials, and craft passports.
    """
    items, total = await ModerationService.list_queue(
        db=db,
        entity_type=entity_type,
        page=page,
        page_size=page_size
    )
    return ModerationQueueListResponse(
        items=[ModerationQueueItemResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/review", response_model=ModerationActionResponse)
async def process_moderation_review(
    payload: ModerationDecisionRequest,
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Executes an administrative review decision (APPROVE, REJECT, REQUEST_CHANGES).
    Idempotent: Duplicate submissions with the same idempotency_key return previous action.
    """
    try:
        action = await ModerationService.process_decision(
            db=db,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            decision=payload.decision,
            reason_category=payload.reason_category,
            moderator_notes=payload.moderator_notes,
            feedback_to_user=payload.feedback_to_user,
            evidence_reference=payload.evidence_reference,
            idempotency_key=payload.idempotency_key,
            current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ModerationActionResponse(
        id=action.id,
        entity_type=action.entity_type,
        entity_id=action.entity_id,
        previous_status=action.previous_status,
        new_status=action.new_status,
        decision=action.decision,
        moderator_user_id=action.moderator_user_id,
        reason_category=action.reason_category,
        moderator_notes=action.moderator_notes,
        feedback_to_user=action.feedback_to_user,
        evidence_reference=action.evidence_reference,
        created_at=action.created_at.isoformat()
    )
