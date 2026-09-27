"""
SIH 26090: Governance & Provenance Auditing API Endpoints
Provides factual dashboard metrics, neutral review signals,
field-level provenance history, and cryptographic chain verification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.services.governance_service import GovernanceService
from backend.app.services.provenance_service import ProvenanceService
from backend.app.schemas.governance import (
    GovernanceDashboardResponse,
    GovernanceFlagCreate,
    GovernanceFlagResponse,
    GovernanceFlagListResponse,
    GovernanceFlagResolveRequest,
    ProvenanceTimelineResponse,
    ProvenanceEventResponse,
    ProvenanceChainVerifyResponse
)

router = APIRouter(prefix="/governance", tags=["Governance & Provenance"])


@router.get("/dashboard", response_model=GovernanceDashboardResponse)
async def get_governance_dashboard(
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Administrator view: Returns factual platform governance metrics.
    Excludes arbitrary trust scores; focuses on factual workloads and review signals.
    """
    metrics = await GovernanceService.get_dashboard_metrics(db)
    return GovernanceDashboardResponse(**metrics)


@router.get("/flags", response_model=GovernanceFlagListResponse)
async def list_governance_flags(
    entity_type: Optional[str] = Query(None, description="Product, ArtisanProfile, CraftPassport, MarketPriceObservation"),
    severity: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH"),
    status_filter: Optional[str] = Query(None, alias="status", description="OPEN, UNDER_INVESTIGATION, RESOLVED_VALIDATED, RESOLVED_CORRECTED, RESOLVED_ACTIONED, DISMISSED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lists neutral review signals across platform entities with pagination and filtering.
    """
    items, total = await GovernanceService.list_flags(
        db=db,
        entity_type=entity_type,
        severity=severity,
        status=status_filter,
        page=page,
        page_size=page_size
    )
    return GovernanceFlagListResponse(
        items=[
            GovernanceFlagResponse(
                id=f.id,
                entity_type=f.entity_type,
                entity_id=f.entity_id,
                flag_type=f.flag_type,
                severity=f.severity,
                status=f.status,
                details_json=f.details_json,
                flagged_by_user_id=f.flagged_by_user_id,
                assigned_to_user_id=f.assigned_to_user_id,
                resolution_notes=f.resolution_notes,
                resolved_by_user_id=f.resolved_by_user_id,
                resolved_at=f.resolved_at.isoformat() if f.resolved_at else None,
                created_at=f.created_at.isoformat()
            )
            for f in items
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/flags", response_model=GovernanceFlagResponse, status_code=status.HTTP_201_CREATED)
async def raise_governance_flag(
    payload: GovernanceFlagCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Creates a neutral administrative review signal on an entity.
    """
    flag = await GovernanceService.raise_flag(
        db=db,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        flag_type=payload.flag_type,
        severity=payload.severity,
        details_json=payload.details_json,
        flagged_by_user=current_user
    )
    return GovernanceFlagResponse(
        id=flag.id,
        entity_type=flag.entity_type,
        entity_id=flag.entity_id,
        flag_type=flag.flag_type,
        severity=flag.severity,
        status=flag.status,
        details_json=flag.details_json,
        flagged_by_user_id=flag.flagged_by_user_id,
        assigned_to_user_id=flag.assigned_to_user_id,
        resolution_notes=flag.resolution_notes,
        resolved_by_user_id=flag.resolved_by_user_id,
        resolved_at=flag.resolved_at.isoformat() if flag.resolved_at else None,
        created_at=flag.created_at.isoformat()
    )


@router.post("/flags/{flag_id}/resolve", response_model=GovernanceFlagResponse)
async def resolve_governance_flag(
    flag_id: str,
    payload: GovernanceFlagResolveRequest,
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Resolves an open review signal with an explicit moderator explanation.
    """
    try:
        flag = await GovernanceService.resolve_flag(
            db=db,
            flag_id=flag_id,
            decision=payload.decision,
            resolution_notes=payload.resolution_notes,
            current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return GovernanceFlagResponse(
        id=flag.id,
        entity_type=flag.entity_type,
        entity_id=flag.entity_id,
        flag_type=flag.flag_type,
        severity=flag.severity,
        status=flag.status,
        details_json=flag.details_json,
        flagged_by_user_id=flag.flagged_by_user_id,
        assigned_to_user_id=flag.assigned_to_user_id,
        resolution_notes=flag.resolution_notes,
        resolved_by_user_id=flag.resolved_by_user_id,
        resolved_at=flag.resolved_at.isoformat() if flag.resolved_at else None,
        created_at=flag.created_at.isoformat()
    )


@router.get("/provenance/timeline/{entity_type}/{entity_id}", response_model=ProvenanceTimelineResponse)
async def get_provenance_timeline(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(require_roles(["admin", "super_admin", "moderator"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves chronological, field-level change history for an entity.
    """
    events = await ProvenanceService.get_entity_timeline(db, entity_type=entity_type, entity_id=entity_id)
    return ProvenanceTimelineResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        total_events=len(events),
        events=[
            ProvenanceEventResponse(
                id=ev.id,
                entity_type=ev.entity_type,
                entity_id=ev.entity_id,
                field_name=ev.field_name,
                previous_value_json=ev.previous_value_json,
                new_value_json=ev.new_value_json,
                provenance_state=ev.provenance_state,
                actor_user_id=ev.actor_user_id,
                actor_role=ev.actor_role,
                change_reason=ev.change_reason,
                source_id=ev.source_id,
                source_url=ev.source_url,
                evidence_reference=ev.evidence_reference,
                ai_model_version=ev.ai_model_version,
                prompt_version=ev.prompt_version,
                human_confirmation_status=ev.human_confirmation_status,
                event_hash=ev.event_hash,
                previous_event_hash=ev.previous_event_hash,
                sequence_number=ev.sequence_number,
                created_at=ev.created_at.isoformat()
            )
            for ev in events
        ]
    )


@router.get("/provenance/verify-chain/{entity_type}/{entity_id}", response_model=ProvenanceChainVerifyResponse)
async def verify_provenance_chain(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cryptographic verification: Validates hash-chain integrity from genesis to latest sequence.
    Detects any payload tampering, sequence breaks, or unauthorized row modifications.
    """
    result = await ProvenanceService.verify_provenance_chain(db, entity_type=entity_type, entity_id=entity_id)
    return ProvenanceChainVerifyResponse(**result)
