"""
SIH 26090: Product, Media, Attributes & Fair-Price Models
Defines Product (with pgvector embedding support), ProductMedia, ProductAttributes, and PriceAnalysis entities.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin, generate_uuid, utc_now
from backend.app.models.custom_types import EmbeddingVector


class Product(Base, TimestampMixin, ProvenanceMixin):
    """Craft product listed by an artisan with multimodal attributes and semantic embedding."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sku = Column(String(64), unique=True, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    storytelling_description = Column(Text, nullable=False)
    ai_generated_description = Column(Text, nullable=True)
    is_ai_description_confirmed = Column(Boolean, nullable=False, default=False)
    price_inr = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    stock_quantity = Column(Integer, nullable=False, default=1)
    monthly_production_capacity = Column(Integer, nullable=False, default=10)
    min_order_quantity = Column(Integer, nullable=False, default=1)
    lead_time_days = Column(Integer, nullable=False, default=7)
    estimated_production_days = Column(Integer, nullable=False, default=7)
    availability_status = Column(String(30), nullable=False, default="AVAILABLE", index=True)
    region = Column(String(100), nullable=True, index=True)
    materials = Column(JSON, default=list, nullable=False)
    primary_color = Column(String(50), nullable=True)
    dimensions = Column(String(100), nullable=True)
    weight_grams = Column(Integer, nullable=True)
    technique = Column(String(150), nullable=True)
    style = Column(String(100), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    is_customizable = Column(Boolean, nullable=False, default=False)

    # 768-dimensional semantic embedding for vector similarity search
    embedding = Column(EmbeddingVector(dim=768), nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="DRAFT",
        index=True,
        doc="DRAFT, PENDING_REVIEW, PUBLISHED, PAUSED, OUT_OF_STOCK, ARCHIVED, REJECTED"
    )
    provenance_status = Column(
        String(50),
        nullable=False,
        default="ARTISAN_DECLARED",
        doc="ARTISAN_DECLARED, SOURCE_BACKED, COMMUNITY_VERIFIED, GOVERNMENT_GI_CONFIRMED"
    )
    ai_metadata = Column(JSON, default=dict, nullable=False)
    admin_feedback = Column(Text, nullable=True)
    moderated_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    artisan = relationship("ArtisanProfile", back_populates="products")
    craft = relationship("Craft", back_populates="products")
    category = relationship("CraftCategory", foreign_keys=[category_id])
    moderator = relationship("User", foreign_keys=[moderated_by])
    media = relationship("ProductMedia", back_populates="product", cascade="all, delete-orphan")
    attributes = relationship("ProductAttributes", back_populates="product", uselist=False, cascade="all, delete-orphan")
    price_analyses = relationship("PriceAnalysis", back_populates="product", cascade="all, delete-orphan")
    ai_analyses = relationship("AIProductAnalysis", back_populates="product", cascade="all, delete-orphan")
    cost_breakdown = relationship("ProductCostBreakdown", back_populates="product", uselist=False, cascade="all, delete-orphan")


class ProductMedia(Base):
    """Photographs and voice note audio recordings associated with a product."""
    __tablename__ = "product_media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type = Column(String(20), nullable=False, default="IMAGE", doc="IMAGE, AUDIO_VOICE_NOTE, DOCUMENT")
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    storage_key = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    product = relationship("Product", back_populates="media")


class ProductAttributes(Base):
    """Structured technical specifications for a craft product."""
    __tablename__ = "product_attributes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    primary_material = Column(String(100), nullable=False)
    technique = Column(String(100), nullable=False)
    dimensions_cm = Column(JSON, nullable=True)
    weight_grams = Column(Integer, nullable=True)
    colors = Column(JSON, default=list, nullable=False)
    care_instructions = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)
    raw_attributes_json = Column(JSON, default=dict, nullable=False)

    # Relationship
    product = relationship("Product", back_populates="attributes")


class ProductCostBreakdown(Base):
    """
    Detailed cost structure provided by an artisan for a craft product.
    Includes materials line items, labor, overhead, packaging, transport, and desired margin.
    """
    __tablename__ = "product_cost_breakdowns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # Material line items: list of {material_name, quantity, unit, unit_cost_inr, total_cost_inr, source_type, source_reference}
    materials = Column(JSON, default=list, nullable=False)
    total_material_cost = Column(Numeric(12, 2), nullable=False, default=0.00)

    # Labor calculation
    labor_calculation_method = Column(String(30), nullable=False, default="HOURLY_RATE", doc="HOURLY_RATE, TOTAL_STATED")
    labor_hours = Column(Numeric(6, 2), nullable=True)
    hourly_labor_rate = Column(Numeric(8, 2), nullable=True)
    total_labor_cost = Column(Numeric(12, 2), nullable=False, default=0.00)

    # Additional direct costs
    packaging_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    transport_cost = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Documented overhead
    overhead_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    overhead_allocation_basis = Column(
        String(40),
        nullable=False,
        default="PER_PRODUCT",
        doc="PER_PRODUCT, PER_BATCH, MONTHLY_ALLOCATION, DOCUMENTED_PERCENTAGE"
    )
    other_costs = Column(Numeric(10, 2), nullable=False, default=0.00)
    other_costs_description = Column(Text, nullable=True)

    # Batch / Unit parameters
    batch_quantity = Column(Integer, nullable=False, default=1)
    currency = Column(String(3), nullable=False, default="INR")
    current_selling_price = Column(Numeric(10, 2), nullable=True)
    desired_margin_percentage = Column(Numeric(5, 2), nullable=False, default=25.00)

    # Precalculated cost baselines (CALCULATED from inputs)
    total_production_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    cost_baseline_unit_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    cost_baseline_recommended_price = Column(Numeric(12, 2), nullable=False, default=0.00)

    provenance_status = Column(String(40), nullable=False, default="ARTISAN_PROVIDED")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="cost_breakdown")
    artisan = relationship("ArtisanProfile")
    price_analyses = relationship("PriceAnalysis", back_populates="cost_breakdown")


class PriceAnalysis(Base):
    """
    Transparent cost breakdown, market evidence synthesis, and fair price range evaluated by the Fair-Price Engine.
    Preserves calculation version, inputs snapshot, comparable observations, and step-by-step explanations.
    """
    __tablename__ = "price_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    cost_breakdown_id = Column(String(36), ForeignKey("product_cost_breakdowns.id", ondelete="SET NULL"), nullable=True, index=True)

    # Calculation version tracking
    engine_version = Column(String(50), nullable=False, default="FAIR_PRICE_ENGINE_V1")
    currency = Column(String(3), nullable=False, default="INR")

    # Base cost fields (retained for backward compatibility)
    raw_material_cost = Column(Numeric(10, 2), nullable=False)
    labor_hours = Column(Numeric(6, 2), nullable=False)
    skill_level_hourly_rate = Column(Numeric(8, 2), nullable=False)
    consumables_overhead_cost = Column(Numeric(10, 2), nullable=False)
    packaging_logistics_cost = Column(Numeric(10, 2), nullable=False)
    calculated_total_cost = Column(Numeric(10, 2), nullable=False)
    fair_margin_percentage = Column(Numeric(5, 2), nullable=False, default=25.0)

    # Pricing recommendations
    recommended_floor_price = Column(Numeric(10, 2), nullable=False)
    recommended_fair_retail_price = Column(Numeric(10, 2), nullable=False)
    fair_price_min = Column(Numeric(10, 2), nullable=True)
    fair_price_max = Column(Numeric(10, 2), nullable=True)
    fair_price_recommended = Column(Numeric(10, 2), nullable=True)

    # Market evidence status and metrics
    evidence_status = Column(
        String(50),
        nullable=False,
        default="COST_ONLY_BASELINE",
        doc="SUFFICIENT_MARKET_EVIDENCE, INSUFFICIENT_MARKET_EVIDENCE, COST_ONLY_BASELINE, NOT_COMPARABLE"
    )
    market_sample_size = Column(Integer, nullable=False, default=0)
    market_median_price = Column(Numeric(10, 2), nullable=True)
    market_min_price = Column(Numeric(10, 2), nullable=True)
    market_max_price = Column(Numeric(10, 2), nullable=True)
    market_iqr_low = Column(Numeric(10, 2), nullable=True)
    market_iqr_high = Column(Numeric(10, 2), nullable=True)
    market_benchmark_reference = Column(Text, nullable=True)
    confidence_indicator = Column(
        String(30),
        nullable=False,
        default="USER_SELF_REPORTED",
        doc="HIGH_EVIDENCE, MODERATE_EVIDENCE, INSUFFICIENT_EVIDENCE, USER_SELF_REPORTED"
    )

    # Traceability & snapshots
    input_snapshot_json = Column(JSON, default=dict, nullable=False)
    comparable_observations_json = Column(JSON, default=list, nullable=False)
    explanation_steps = Column(JSON, default=list, nullable=False)
    limitations_notes = Column(JSON, default=list, nullable=False)

    # Provenance and Artisan Confirmation
    provenance_state = Column(
        String(50),
        nullable=False,
        default="CALCULATED",
        doc="ARTISAN_PROVIDED, SOURCE_BACKED, AI_SUGGESTED, CALCULATED, HUMAN_CONFIRMED"
    )
    is_confirmed_by_artisan = Column(Boolean, nullable=False, default=False)
    confirmed_price_inr = Column(Numeric(10, 2), nullable=True)
    artisan_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="price_analyses")
    cost_breakdown = relationship("ProductCostBreakdown", back_populates="price_analyses")
    artisan = relationship("ArtisanProfile")

