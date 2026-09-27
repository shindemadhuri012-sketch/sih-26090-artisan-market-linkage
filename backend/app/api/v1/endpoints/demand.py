"""
SIH 26090: Demand Intelligence Endpoints
Provides real-data demand observations, deterministic aggregations,
empirical trend analysis, and time-series forecast projections.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.market import DemandObservation
from backend.app.models.forecast import DemandForecastRun
from backend.app.schemas.demand import (
    DemandObservationCreate,
    DemandObservationResponse,
    DemandSummaryResponse,
    DemandTrendResponse,
    DemandForecastResponse
)
from backend.app.services.demand_service import DemandService

router = APIRouter(prefix="/demand", tags=["Demand Intelligence & Analytics"])


def _format_observation_response(obs: DemandObservation) -> DemandObservationResponse:
    return DemandObservationResponse(
        id=obs.id,
        craft_id=obs.craft_id,
        craft_category_id=obs.craft_category_id,
        geography_state=obs.geography_state,
        observation_period_start=obs.observation_period_start.isoformat(),
        observation_period_end=obs.observation_period_end.isoformat(),
        total_enquiries=obs.total_enquiries,
        fulfilled_orders=obs.fulfilled_orders,
        unit_volume=obs.unit_volume,
        monetary_volume_inr=obs.monetary_volume_inr,
        average_realized_price=obs.average_realized_price,
        seasonal_festival_tag=obs.seasonal_festival_tag,
        signal_tier=obs.signal_tier,
        observation_type=obs.observation_type,
        data_quality_status=obs.data_quality_status,
        is_sample_or_demo=obs.is_sample_or_demo,
        data_provenance_level=obs.data_provenance_level or "VERIFIED_EXTERNAL_SOURCE",
        created_at=obs.observation_period_start.isoformat()
    )


@router.post("/observations", response_model=DemandObservationResponse, status_code=status.HTTP_201_CREATED)
async def record_demand_observation(
    payload: DemandObservationCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Admin-only endpoint for ingesting verified real-data demand observations."""
    obs = await DemandService.create_observation(db=db, payload=payload, actor_id=current_user.id)
    return _format_observation_response(obs)


@router.get("/observations", response_model=List[DemandObservationResponse])
async def list_demand_observations(
    craft_id: Optional[str] = Query(None),
    craft_category_id: Optional[str] = Query(None),
    geography_state: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["artisan", "buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists filtered historical demand observations with explicit provenance tags."""
    query = select(DemandObservation)
    if craft_id:
        query = query.where(DemandObservation.craft_id == craft_id)
    if craft_category_id:
        query = query.where(DemandObservation.craft_category_id == craft_category_id)
    if geography_state:
        query = query.where(DemandObservation.geography_state.ilike(geography_state.strip()))

    query = query.order_by(DemandObservation.observation_period_start.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    observations = res.scalars().all()
    return [_format_observation_response(o) for o in observations]


@router.get("/summary", response_model=DemandSummaryResponse)
async def get_demand_summary(
    craft_id: Optional[str] = Query(None),
    craft_category_id: Optional[str] = Query(None),
    geography_state: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["artisan", "buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Calculates deterministic aggregated demand volumes, enquiries, and orders."""
    return await DemandService.get_demand_summary(
        db=db,
        craft_id=craft_id,
        category_id=craft_category_id,
        state=geography_state
    )


@router.get("/trends", response_model=DemandTrendResponse)
async def get_demand_trends(
    craft_id: Optional[str] = Query(None),
    geography_state: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["artisan", "buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Evaluates empirical directional trend across monthly observation periods."""
    return await DemandService.get_demand_trends(
        db=db,
        craft_id=craft_id,
        state=geography_state
    )


@router.get("/forecasts", response_model=DemandForecastResponse)
async def get_demand_forecast(
    craft_id: Optional[str] = Query(None),
    geography_state: Optional[str] = Query(None),
    force_recompute: bool = Query(False),
    current_user: User = Depends(require_roles(["artisan", "buyer", "admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves or generates time-series forecast projections with multi-gate eligibility checks.
    Explicitly returns INSUFFICIENT_HISTORY if fewer than 12 complete months are recorded.
    """
    return await DemandService.get_or_run_forecast(
        db=db,
        craft_id=craft_id,
        state=geography_state,
        force_recompute=force_recompute
    )
