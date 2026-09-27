"""
SIH 26090: Health & Readiness API Endpoints
Provides system diagnostic probes for cloud load balancers and deployment monitoring.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_async_db
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health & System Diagnostics"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def liveness_check():
    """Basic liveness probe verifying FastAPI event loop responsiveness."""
    return HealthResponse(
        status="ok",
        environment=settings.APP_ENV,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        components={"api": "healthy"}
    )


@router.get("/ready", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_async_db)):
    """Deep readiness probe verifying database connectivity and pgvector extension status."""
    db_status = {"connected": False, "pgvector_available": False}
    components = {"api": "healthy"}

    try:
        # Check basic DB connectivity
        result = await db.execute(text("SELECT 1;"))
        if result.scalar() == 1:
            db_status["connected"] = True

        # Check pgvector extension availability if connected to Postgres
        if "postgresql" in settings.DATABASE_URL:
            ext_check = await db.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            )
            db_status["pgvector_available"] = ext_check.scalar() is not None
        else:
            db_status["pgvector_available"] = False
            db_status["note"] = "Non-PostgreSQL dialect active (sqlite/fallback)"
    except Exception as e:
        db_status["connected"] = False
        db_status["error"] = str(e)
        components["database"] = "degraded"

    # Check Redis connectivity if configured
    redis_status = {"configured": bool(settings.REDIS_URL), "connected": False}
    if settings.REDIS_URL:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            await r.ping()
            await r.aclose()
            redis_status["connected"] = True
            components["redis"] = "healthy"
        except Exception as e:
            redis_status["connected"] = False
            redis_status["error"] = str(e)
            components["redis"] = "degraded"

    overall_status = "ok" if db_status["connected"] else "degraded"

    return HealthResponse(
        status=overall_status,
        environment=settings.APP_ENV,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        components=components
    )
