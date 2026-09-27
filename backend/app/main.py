"""
SIH 26090: FastAPI Application Entrypoint
Initializes FastAPI application instance, registers middleware, and mounts API routers.
"""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.telemetry import logger
from backend.app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for application startup and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    yield
    logger.info(f"Shutting down {settings.APP_NAME} gracefully...")


def create_application() -> FastAPI:
    """Application factory for FastAPI service."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered platform linking Indian artisans directly with enterprise, "
            "institutional, and retail buyers through intelligent product digitization, "
            "fair-price intelligence, craft provenance, and explainable matching."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security Headers, Correlation Tracking & Request Sizing Middleware
    @app.middleware("http")
    async def security_and_telemetry_middleware(request: Request, call_next):
        # 1. Request Correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # 2. Maximum Request Body Size Check (15MB Limit Defense)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_BODY_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Request payload exceeds allowed limit (15MB).",
                    "correlation_id": correlation_id
                }
            )

        # 3. Process Request
        response = await call_next(request)

        # 4. Attach Correlation ID to Response
        response.headers["X-Correlation-ID"] = correlation_id

        # 5. Inject Defensive Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: https: http:; "
            "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        )
        if settings.APP_ENV.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    # Global Unhandled Exception Sanitization Handler (Masks internal stack traces in production)
    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", "UNKNOWN")
        logger.error(
            f"Unhandled server error [{correlation_id}] on {request.method} {request.url.path}: {exc}",
            exc_info=True
        )
        if settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc), "correlation_id": correlation_id}
            )
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal server error. Reference ID: {correlation_id}",
                "correlation_id": correlation_id
            }
        )

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "docs": "/docs" if settings.DEBUG else "disabled",
            "health": f"{settings.API_V1_PREFIX}/health"
        }

    return app


app = create_application()
