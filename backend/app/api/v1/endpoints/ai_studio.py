"""
SIH 26090: AI Product Studio API Endpoints
Authenticated artisan endpoints for multimodal image understanding, suggestion retrieval,
and field-level human confirmation.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.schemas.ai_studio import (
    AIAnalyzeRequest,
    AIAnalysisResponse,
    AIConfirmRequest,
    AIRejectRequest
)
from ai.product_studio.service import AIProductStudioService

router = APIRouter(tags=["AI Product Studio"])


@router.post(
    "/products/{product_id}/ai/analyze",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_201_CREATED
)
async def analyze_product_image(
    product_id: str,
    payload: AIAnalyzeRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Initiates multimodal AI vision understanding on a specified product photograph.
    Extracts structured craft attribute suggestions into an isolated staging layer.
    Enforces server-side artisan ownership (IDOR defense).
    """
    return await AIProductStudioService.analyze_product_media(
        db=db,
        product_id=product_id,
        payload=payload,
        current_user=current_user
    )


@router.get(
    "/products/{product_id}/ai/analyses",
    response_model=List[AIAnalysisResponse]
)
async def list_product_ai_analyses(
    product_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists all historical AI analysis runs for the authenticated artisan's product."""
    return await AIProductStudioService.list_product_analyses(
        db=db,
        product_id=product_id,
        current_user=current_user
    )


@router.get(
    "/products/{product_id}/ai/analyses/{analysis_id}",
    response_model=AIAnalysisResponse
)
async def get_product_ai_analysis(
    product_id: str,
    analysis_id: str,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves a single AI analysis run with its field-level suggestions and provenance."""
    return await AIProductStudioService.get_analysis_by_id(
        db=db,
        product_id=product_id,
        analysis_id=analysis_id,
        current_user=current_user
    )


@router.post(
    "/products/{product_id}/ai/analyses/{analysis_id}/confirm",
    response_model=AIAnalysisResponse
)
async def confirm_ai_suggestions(
    product_id: str,
    analysis_id: str,
    payload: AIConfirmRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Processes human confirmation decisions (ACCEPT, EDIT, REJECT) for AI suggestions.
    Only confirmed attributes may be applied to the canonical Product listing.
    """
    return await AIProductStudioService.confirm_suggestions(
        db=db,
        product_id=product_id,
        analysis_id=analysis_id,
        payload=payload,
        current_user=current_user
    )


@router.post(
    "/products/{product_id}/ai/analyses/{analysis_id}/reject",
    response_model=AIAnalysisResponse
)
async def reject_ai_analysis(
    product_id: str,
    analysis_id: str,
    payload: AIRejectRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Bulk rejects all suggestions for an analysis run."""
    return await AIProductStudioService.reject_analysis(
        db=db,
        product_id=product_id,
        analysis_id=analysis_id,
        payload=payload,
        current_user=current_user
    )
