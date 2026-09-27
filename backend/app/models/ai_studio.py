"""
SIH 26090: AI Product Studio Database Models
Defines AIProductAnalysis and AIProductSuggestion entities for staging,
immutable provenance, and human-in-the-loop review.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now


class AIProductAnalysis(Base):
    """
    Staged record of an AI multimodal analysis run on a product media asset.
    Stores immutable input provenance, model metadata, and job lifecycle status.
    """
    __tablename__ = "ai_product_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    media_id = Column(String(36), ForeignKey("product_media.id", ondelete="SET NULL"), nullable=True, index=True)
    media_checksum = Column(String(64), nullable=True)

    provider = Column(String(50), nullable=False, doc="google, mock, none")
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), nullable=False, default="product_vision_v1")

    idempotency_key = Column(String(128), nullable=True, index=True)
    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
        doc="PENDING, PROCESSING, COMPLETED, FAILED, REJECTED, CONFIRMED"
    )
    error_message = Column(Text, nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)

    input_parameters = Column(JSON, default=dict, nullable=False)
    raw_response = Column(JSON, default=dict, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="ai_analyses")
    media = relationship("ProductMedia")
    suggestions = relationship("AIProductSuggestion", back_populates="analysis", cascade="all, delete-orphan")


class AIProductSuggestion(Base):
    """
    Fine-grained, field-level suggestion produced by an AI analysis run.
    Strictly isolated in a staging layer until reviewed and confirmed by an artisan.
    """
    __tablename__ = "ai_product_suggestions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("ai_product_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    field_name = Column(String(100), nullable=False, index=True)
    suggested_value = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True, doc="Actual calibrated model confidence score or NULL. Never fabricated.")
    source_type = Column(
        String(50),
        nullable=False,
        default="AI_SUGGESTED",
        doc="AI_SUGGESTED, HUMAN_CONFIRMED, REJECTED"
    )
    human_confirmed = Column(Boolean, nullable=False, default=False)
    confirmed_value = Column(JSON, nullable=True, doc="Artisan-reviewed or edited value. Preserves suggested_value intact.")

    status = Column(
        String(30),
        nullable=False,
        default="AI_SUGGESTED",
        index=True,
        doc="AI_SUGGESTED, HUMAN_CONFIRMED, REJECTED"
    )
    artisan_notes = Column(Text, nullable=True)

    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    analysis = relationship("AIProductAnalysis", back_populates="suggestions")
    product = relationship("Product")
    reviewer = relationship("User")


# Compound index for fast querying by product and status
Index("idx_ai_suggestions_product_status", AIProductSuggestion.product_id, AIProductSuggestion.status)
