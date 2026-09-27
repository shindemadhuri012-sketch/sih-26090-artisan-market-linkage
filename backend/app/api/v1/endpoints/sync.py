"""
SIH 26090: Offline Synchronization Endpoints
Provides batch replay endpoint for queued client mutations with idempotency.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.schemas.sync import SyncBatchRequest, SyncBatchResponse
from backend.app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Offline Sync Engine"])


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
async def process_sync_batch(
    payload: SyncBatchRequest,
    current_user: User = Depends(require_roles(["artisan", "buyer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submits a batch of offline-queued mutations for sequential replay:
    - Validates idempotency keys against previous execution records.
    - Re-verifies server-side authorization on every operation.
    - Detects concurrency conflicts against entity update timestamps.
    - Commits valid mutations atomically and logs audit receipts.
    """
    return await SyncService.process_sync_batch(
        db=db,
        current_user=current_user,
        batch_request=payload
    )
