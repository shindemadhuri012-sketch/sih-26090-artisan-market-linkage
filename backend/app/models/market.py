"""
SIH 26090: Enquiry, Order, Demand Observation & Demand Forecast Models
Defines commercial transaction linkage and real-data demand intelligence entities.
"""

from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin, generate_uuid, utc_now


class Enquiry(Base, TimestampMixin):
    """Direct commercial negotiation between buyer and artisan following a match (RFQ)."""
    __tablename__ = "enquiries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rfq_reference_number = Column(String(50), unique=True, nullable=True, index=True)
    buyer_id = Column(String(36), ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(String(36), ForeignKey("buyer_requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Commercial Terms
    message = Column(Text, nullable=False)
    proposed_quantity = Column(Integer, nullable=False)
    proposed_unit_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    
    # State Machine
    status = Column(
        String(30),
        nullable=False,
        default="SENT",
        index=True,
        doc="DRAFT, OPEN, SENT, VIEWED, RESPONDED, NEGOTIATION, ACCEPTED, DECLINED, EXPIRED, CANCELLED"
    )
    
    # Artisan Counter-Offer & Response
    artisan_response_message = Column(Text, nullable=True)
    counter_unit_price = Column(Numeric(10, 2), nullable=True)
    counter_lead_time_days = Column(Integer, nullable=True)
    decline_reason = Column(String(100), nullable=True)
    
    # Timestamps
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    buyer = relationship("BuyerProfile", back_populates="enquiries")
    artisan = relationship("ArtisanProfile", back_populates="enquiries")
    requirement = relationship("BuyerRequirement", back_populates="enquiries")
    product = relationship("Product")
    match = relationship("Match")
    order = relationship("Order", back_populates="enquiry", uselist=False, cascade="all, delete-orphan")


class Order(Base, TimestampMixin):
    """Fulfillment lifecycle and milestone tracking for confirmed transactions."""
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    enquiry_id = Column(String(36), ForeignKey("enquiries.id", ondelete="RESTRICT"), unique=True, nullable=False)
    order_reference_number = Column(String(50), unique=True, nullable=False, index=True)
    total_amount_inr = Column(Numeric(12, 2), nullable=False)
    artisan_realization_amount = Column(Numeric(12, 2), nullable=False)
    fulfillment_status = Column(
        String(30),
        nullable=False,
        default="CONFIRMED",
        index=True,
        doc="CONFIRMED, SAMPLE_APPROVED, IN_PRODUCTION, DISPATCHED, DELIVERED"
    )
    tracking_consignment_number = Column(String(100), nullable=True)

    # Relationship
    enquiry = relationship("Enquiry", back_populates="order")


class DemandObservation(Base, ProvenanceMixin):
    """Real historical market transaction points, festival cycles, and enquiry frequencies."""
    __tablename__ = "demand_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="CASCADE"), nullable=False, index=True)
    geography_state = Column(String(100), nullable=False, index=True)
    observation_period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    observation_period_end = Column(DateTime(timezone=True), nullable=False)
    total_enquiries = Column(Integer, nullable=False, default=0)
    fulfilled_orders = Column(Integer, nullable=False, default=0)
    average_realized_price = Column(Numeric(10, 2), nullable=True)
    seasonal_festival_tag = Column(String(50), nullable=True, doc="Diwali, Durga Puja, Wedding Season, Pongal")
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)

    # Extended Demand Intelligence Fields
    craft_category_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    signal_tier = Column(
        String(30),
        nullable=False,
        default="TRANSACTIONAL_CONFIRMED",
        index=True,
        doc="TRANSACTIONAL_CONFIRMED, PROCUREMENT_INTENT, EXTERNAL_BENCHMARK"
    )
    observation_type = Column(
        String(50),
        nullable=False,
        default="PLATFORM_NATIVE",
        doc="PLATFORM_NATIVE, GOVERNMENT_REGISTRY, COOPERATIVE_SALE, TRADE_FAIR"
    )
    unit_volume = Column(Integer, nullable=False, default=0)
    monetary_volume_inr = Column(Numeric(14, 2), nullable=True)
    ingestion_batch_id = Column(String(64), nullable=True, index=True)
    data_quality_status = Column(
        String(30),
        nullable=False,
        default="VERIFIED",
        doc="VERIFIED, ESTIMATED, UNVERIFIED, PROVISIONAL"
    )

    # Relationships
    craft = relationship("Craft", back_populates="demand_observations")
    craft_category = relationship("CraftCategory")
    data_source = relationship("DataSource")


class DemandForecast(Base):
    """Projected seasonal and regional craft demand with explicit data sufficiency indicator."""
    __tablename__ = "demand_forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_period_month = Column(Integer, nullable=False)
    forecast_period_year = Column(Integer, nullable=False)
    projected_demand_index = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    data_sufficiency_status = Column(
        String(40),
        nullable=False,
        default="INSUFFICIENT_HISTORICAL_DATA",
        doc="SUFFICIENT_DATA_AVAILABLE, INSUFFICIENT_HISTORICAL_DATA"
    )
    explanation_note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    craft = relationship("Craft")


class MarketPriceObservation(Base, ProvenanceMixin):
    """
    Source-backed, documented market price observations for authentic craft products.
    Tracks real external sources (e.g. TRIFED, CCIC, State Handicrafts registries),
    provenance, observation timestamp, and comparability descriptors.
    """
    __tablename__ = "market_price_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="CASCADE"), nullable=False, index=True)
    craft_category_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="SET NULL"), nullable=True, index=True)

    product_title = Column(String(255), nullable=True)
    observed_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")

    source_name = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=True)
    source_type = Column(
        String(50),
        nullable=False,
        default="GOVERNMENT",
        doc="GOVERNMENT, OFFICIAL_REGISTRY, OFFICIAL_MARKETPLACE, VERIFIED_ARTISAN, AUTHORIZED_SOURCE, OTHER_DOCUMENTED_SOURCE"
    )
    geography_state = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)

    observation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    original_source_id = Column(String(100), nullable=True)
    license_or_usage_info = Column(Text, nullable=True)

    # Technical attributes for comparability
    attributes_json = Column(JSON, default=dict, nullable=False)
    comparability_tags = Column(JSON, default=list, nullable=False)

    evidence_quality_status = Column(
        String(30),
        nullable=False,
        default="MEDIUM",
        doc="HIGH, MEDIUM, LOW, INSUFFICIENT"
    )
    verification_status = Column(
        String(30),
        nullable=False,
        default="DOCUMENTED",
        doc="DOCUMENTED, VERIFIED, PENDING_REVIEW, REJECTED"
    )
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    ingestion_batch_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    craft = relationship("Craft", back_populates="price_observations")
    craft_category = relationship("CraftCategory")
    data_source = relationship("DataSource")

