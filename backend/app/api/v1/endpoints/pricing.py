"""
SIH 26090: Fair-Price Intelligence API Endpoints
Provides authenticated artisan endpoints for cost structure management,
deterministic FAIR_PRICE_ENGINE_V1 analysis execution, historical analysis auditing,
artisan price confirmation, and authorized market evidence retrieval/ingestion.
Strict server-side IDOR protection on all artisan operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.schemas.pricing import (
    CostBreakdownCreate,
    CostBreakdownResponse,
    MarketPriceObservationCreate,
    MarketPriceObservationResponse,
    PriceAnalysisResponse,
    PriceConfirmationRequest
)
from backend.app.services import pricing_service

router = APIRouter(tags=["Fair-Price Intelligence"])


# ==========================================
# ARTISAN COST STRUCTURE MANAGEMENT
# ==========================================

@router.post(
    "/products/{product_id}/pricing/costs",
    response_model=CostBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Save or update product cost breakdown"
)
async def update_product_costs(
    product_id: str,
    payload: CostBreakdownCreate,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Saves or updates the structured cost breakdown for an artisan's craft product.
    Calculates itemized materials, labor (hourly or stated), packaging, transport,
    overhead allocation, and cost baseline price using exact Decimal arithmetic.
    """
    breakdown = await pricing_service.save_or_update_cost_breakdown(
        db=db,
        product_id=product_id,
        user_id=current_user.id,
        payload=payload
    )
    return breakdown


@router.get(
    "/products/{product_id}/pricing/costs",
    response_model=CostBreakdownResponse,
    summary="Get current product cost breakdown"
)
async def get_product_costs(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves the structured cost breakdown for the given product.
    Enforces server-side product ownership verification.
    """
    breakdown = await pricing_service.get_cost_breakdown(
        db=db,
        product_id=product_id,
        user_id=current_user.id
    )
    if not breakdown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cost breakdown found for product '{product_id}'."
        )
    return breakdown


# ==========================================
# FAIR PRICE ENGINE ANALYSIS
# ==========================================

@router.post(
    "/products/{product_id}/pricing/analyze",
    response_model=PriceAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run FAIR_PRICE_ENGINE_V1 deterministic analysis"
)
async def analyze_product_pricing(
    product_id: str,
    payload: Optional[CostBreakdownCreate] = None,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Executes FAIR_PRICE_ENGINE_V1 for the given product.
    Synthesizes artisan production costs and comparable source-backed market observations.
    Strictly outputs COST_ONLY_BASELINE if valid market observations are fewer than 3 (N < 3).
    Persists a versioned, reproducible PriceAnalysis record with full step-by-step mathematical explanation.
    """
    analysis = await pricing_service.run_price_analysis(
        db=db,
        product_id=product_id,
        user_id=current_user.id,
        custom_cost_input=payload
    )
    return pricing_service.format_analysis_response(analysis)


@router.get(
    "/products/{product_id}/pricing/analysis",
    response_model=PriceAnalysisResponse,
    summary="Get latest price analysis for product"
)
async def get_latest_analysis(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves the latest generated PriceAnalysis for the specified product.
    """
    analysis = await pricing_service.get_latest_price_analysis(
        db=db,
        product_id=product_id,
        user_id=current_user.id
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price analysis found for product '{product_id}'."
        )
    return pricing_service.format_analysis_response(analysis)


@router.get(
    "/products/{product_id}/pricing/history",
    response_model=List[PriceAnalysisResponse],
    summary="Get historical price analyses for product"
)
async def get_analysis_history(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves historical, versioned PriceAnalysis records for the product.
    Ensures complete chronological auditability without overwriting past analyses.
    """
    analyses = await pricing_service.get_price_analysis_history(
        db=db,
        product_id=product_id,
        user_id=current_user.id
    )
    return [pricing_service.format_analysis_response(a) for a in analyses]


@router.post(
    "/products/{product_id}/pricing/confirm",
    response_model=PriceAnalysisResponse,
    summary="Artisan confirms fair price and optionally updates product listing"
)
async def confirm_pricing(
    product_id: str,
    payload: PriceConfirmationRequest,
    analysis_id: Optional[str] = Query(default=None, description="Optional specific PriceAnalysis ID to confirm"),
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Explicit artisan review and confirmation of a generated price recommendation.
    Promotes analysis state to HUMAN_CONFIRMED (does NOT imply government certification).
    Optionally updates the canonical product.price_inr.
    Audits the confirmation event.
    """
    target_analysis_id = analysis_id
    if not target_analysis_id:
        latest = await pricing_service.get_latest_price_analysis(db=db, product_id=product_id, user_id=current_user.id)
        if not latest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price analysis available to confirm for product '{product_id}'."
            )
        target_analysis_id = latest.id

    confirmed_analysis = await pricing_service.confirm_price_analysis(
        db=db,
        analysis_id=target_analysis_id,
        user_id=current_user.id,
        payload=payload
    )
    return pricing_service.format_analysis_response(confirmed_analysis)


# ==========================================
# SOURCE-BACKED MARKET EVIDENCE
# ==========================================

@router.get(
    "/pricing/market-evidence",
    response_model=List[MarketPriceObservationResponse],
    summary="Query documented market price observations"
)
async def list_market_evidence(
    craft_id: Optional[str] = Query(default=None, description="Filter by craft ID"),
    state: Optional[str] = Query(default=None, description="Filter by state of origin/observation"),
    quality: Optional[str] = Query(default=None, description="Filter by quality rating (HIGH, MEDIUM, LOW)"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lists source-backed market price observations with full provenance references.
    """
    observations = await pricing_service.list_market_price_observations(
        db=db,
        craft_id=craft_id,
        state=state,
        quality=quality,
        limit=limit
    )
    return observations


@router.post(
    "/pricing/market-evidence",
    response_model=MarketPriceObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest source-backed market observation (Admin only)"
)
async def ingest_market_evidence(
    payload: MarketPriceObservationCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authorized ingestion of documented, source-backed market price observations.
    Preserves authoritative source URLs, observation dates, and technical attributes.
    """
    obs = await pricing_service.ingest_market_price_observation(
        db=db,
        payload=payload
    )
    return obs
