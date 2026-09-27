"""
SIH 26090: Central Model Registry
Exports all 23 declarative SQLAlchemy 2.0 ORM entities.
"""

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin
from backend.app.models.auth import User, Role, AuditLog, Notification, RefreshTokenSession, OTPChallenge
from backend.app.models.provenance import DataSource, DataImport
from backend.app.models.craft import CraftCategory, Craft, CraftPassport
from backend.app.models.artisan import ArtisanProfile, ArtisanCraft, Verification
from backend.app.models.product import Product, ProductMedia, ProductAttributes, PriceAnalysis, ProductCostBreakdown
from backend.app.models.ai_studio import AIProductAnalysis, AIProductSuggestion
from backend.app.models.buyer import BuyerProfile, BuyerRequirement, Match, MatchExplanation
from backend.app.models.requirement_understanding import RequirementUnderstanding
from backend.app.models.market import Enquiry, Order, DemandObservation, DemandForecast, MarketPriceObservation
from backend.app.models.forecast import DemandForecastRun, DemandForecastPoint
from backend.app.models.sync import SyncOperation
from backend.app.models.governance import GovernanceFlag, ModerationAction, ProvenanceEvent

__all__ = [
    "Base",
    "TimestampMixin",
    "ProvenanceMixin",
    "User",
    "Role",
    "AuditLog",
    "Notification",
    "RefreshTokenSession",
    "OTPChallenge",
    "DataSource",
    "DataImport",
    "CraftCategory",
    "Craft",
    "CraftPassport",
    "ArtisanProfile",
    "ArtisanCraft",
    "Verification",
    "Product",
    "ProductMedia",
    "ProductAttributes",
    "PriceAnalysis",
    "ProductCostBreakdown",
    "AIProductAnalysis",
    "AIProductSuggestion",
    "BuyerProfile",
    "BuyerRequirement",
    "RequirementUnderstanding",
    "Match",
    "MatchExplanation",
    "Enquiry",
    "Order",
    "DemandObservation",
    "DemandForecast",
    "DemandForecastRun",
    "DemandForecastPoint",
    "MarketPriceObservation",
    "SyncOperation",
    "GovernanceFlag",
    "ModerationAction",
    "ProvenanceEvent",
]
