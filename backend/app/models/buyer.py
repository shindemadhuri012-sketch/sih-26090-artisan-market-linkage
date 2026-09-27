"""
SIH 26090: Buyer Profile, Requirement (RFQ) & Explainable Match Models
Defines BuyerProfile, BuyerRequirement (with pgvector embedding), Match, and MatchExplanation entities.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin, generate_uuid, utc_now
from backend.app.models.custom_types import EmbeddingVector


class BuyerProfile(Base, TimestampMixin, ProvenanceMixin):
    """Institutional, retail curator, government, or export procurement profile."""
    __tablename__ = "buyer_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    buyer_type = Column(
        String(50),
        nullable=False,
        doc="RETAIL_CURATOR, INSTITUTIONAL_GIFTING, GOVERNMENT_GEM, EXPORT_AGGREGATOR"
    )
    gstin = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False, default="India")
    state = Column(String(100), nullable=True)
    typical_order_volume = Column(String(50), nullable=True)
    is_verified_buyer = Column(Boolean, nullable=False, default=False)

    # Relationships
    user = relationship("User", back_populates="buyer_profile")
    requirements = relationship("BuyerRequirement", back_populates="buyer", cascade="all, delete-orphan")
    enquiries = relationship("Enquiry", back_populates="buyer")


class BuyerRequirement(Base, TimestampMixin):
    """Formal procurement brief or Request for Quotation (RFQ) submitted for intelligent matching."""
    __tablename__ = "buyer_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    buyer_id = Column(String(36), ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    target_craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="SET NULL"), nullable=True, index=True)
    target_category_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    required_quantity = Column(Integer, nullable=False)
    target_unit_price_inr = Column(Numeric(10, 2), nullable=True)
    max_budget_inr = Column(Numeric(12, 2), nullable=True)
    deadline_date = Column(DateTime(timezone=True), nullable=False)
    requires_gi_certification = Column(Boolean, nullable=False, default=False)
    material_constraints = Column(JSON, default=list, nullable=False)
    desired_materials = Column(JSON, default=list, nullable=False)
    desired_techniques = Column(JSON, default=list, nullable=False)
    desired_motifs = Column(JSON, default=list, nullable=False)
    preferred_region = Column(String(100), nullable=True)
    max_acceptable_moq = Column(Integer, nullable=True)
    max_lead_time_days = Column(Integer, nullable=True)
    requires_customization = Column(Boolean, nullable=False, default=False)
    quality_specifications = Column(Text, nullable=True)
    packaging_requirements = Column(Text, nullable=True)
    destination_state = Column(String(100), nullable=True)
    destination_pincode = Column(String(10), nullable=True)
    currency = Column(String(3), nullable=False, default="INR")

    # 768-dimensional semantic embedding for matching
    embedding = Column(EmbeddingVector(dim=768), nullable=True)
    embedding_model_version = Column(String(50), nullable=True, default="gemini-embedding-2")

    status = Column(
        String(30),
        nullable=False,
        default="OPEN",
        index=True,
        doc="OPEN, MATCHED, IN_ENQUIRY, FULFILLED, CLOSED, CANCELLED"
    )
    data_provenance_level = Column(String(50), nullable=False, default="USER_DECLARED")
    provenance_state = Column(String(30), nullable=False, default="HUMAN_CONFIRMED")

    # Relationships
    buyer = relationship("BuyerProfile", back_populates="requirements")
    target_craft = relationship("Craft")
    target_category = relationship("CraftCategory")
    matches = relationship("Match", back_populates="requirement", cascade="all, delete-orphan")
    enquiries = relationship("Enquiry", back_populates="requirement")
    understandings = relationship("RequirementUnderstanding", back_populates="requirement", cascade="all, delete-orphan")


class Match(Base, TimestampMixin):
    """Multi-stage evaluated match linking a buyer requirement to an artisan profile or product."""
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    requirement_id = Column(String(36), ForeignKey("buyer_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Engine Version & Sufficiency
    engine_version = Column(String(50), nullable=False, default="MATCHING_ENGINE_V1")
    data_sufficiency_state = Column(
        String(30),
        nullable=False,
        default="MATCHABLE",
        index=True,
        doc="MATCHABLE, PARTIALLY_MATCHABLE, INSUFFICIENT_INFORMATION"
    )

    # Component Scores [0.0000 - 1.0000]
    composite_score = Column(Float, nullable=False, index=True)
    semantic_similarity = Column(Float, nullable=False, default=0.0)
    craft_compatibility = Column(Float, nullable=False, default=0.0)
    material_compatibility = Column(Float, nullable=False, default=0.0)
    technique_compatibility = Column(Float, nullable=False, default=0.0)
    capacity_compatibility = Column(Float, nullable=False, default=0.0)
    price_compatibility = Column(Float, nullable=False, default=0.0)
    lead_time_compatibility = Column(Float, nullable=False, default=0.0)
    provenance_bonus = Column(Float, nullable=False, default=0.0)
    
    rank = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="PROPOSED", index=True, doc="PROPOSED, VIEWED, ENQUIRED, DISMISSED")
    is_dismissed_by_buyer = Column(Boolean, nullable=False, default=False)

    # Relationships
    requirement = relationship("BuyerRequirement", back_populates="matches")
    artisan = relationship("ArtisanProfile", back_populates="matches")
    product = relationship("Product")
    explanation = relationship("MatchExplanation", back_populates="match", uselist=False, cascade="all, delete-orphan")


class MatchExplanation(Base):
    """Decomposed, transparent justification matrix explaining why a match was scored."""
    __tablename__ = "match_explanations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary_explanation = Column(Text, nullable=False)
    capacity_justification = Column(Text, nullable=False)
    price_justification = Column(Text, nullable=False)
    provenance_justification = Column(Text, nullable=False)
    factors_json = Column(JSON, nullable=False)
    
    # Grounded Explanations
    positive_reasons = Column(JSON, default=list, nullable=False)
    limitations = Column(JSON, default=list, nullable=False)
    unmatched_fields = Column(JSON, default=list, nullable=False)
    missing_fields = Column(JSON, default=list, nullable=False)

    # Relationship
    match = relationship("Match", back_populates="explanation")
