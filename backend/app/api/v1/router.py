"""
SIH 26090: API v1 Central Router
Aggregates all API v1 endpoints under a unified router.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    auth,
    artisans,
    buyers,
    passports,
    verifications,
    public,
    crafts,
    artisan_crafts,
    products,
    ai_studio,
    pricing,
    buyer_requirements,
    matches,
    rfqs,
    demand,
    sync,
    governance,
    moderation
)

api_v1_router = APIRouter()

# Register Phase 1 through Phase 8 Route Modules
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(artisans.router)
api_v1_router.include_router(buyers.router)
api_v1_router.include_router(passports.router)
api_v1_router.include_router(verifications.router)
api_v1_router.include_router(public.router)
api_v1_router.include_router(crafts.router)
api_v1_router.include_router(artisan_crafts.router)
api_v1_router.include_router(products.router)
api_v1_router.include_router(ai_studio.router)
api_v1_router.include_router(pricing.router)
api_v1_router.include_router(buyer_requirements.router)
api_v1_router.include_router(matches.router)
api_v1_router.include_router(rfqs.router)
api_v1_router.include_router(demand.router)
api_v1_router.include_router(sync.router)
api_v1_router.include_router(governance.router)
api_v1_router.include_router(moderation.router)


