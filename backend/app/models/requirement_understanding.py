"""
SIH 26090: Buyer Requirement Understanding Staging Model
Defines RequirementUnderstanding entity holding staged AI-extracted structured attributes
from natural language procurement briefs with strict provenance and buyer confirmation isolation.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid, utc_now


class RequirementUnderstanding(Base, TimestampMixin):
    """
    Staged record of AI extraction runs on buyer procurement briefs (RFQs).
    Preserves strict staging isolation: AI suggestions never overwrite canonical
    BuyerRequirement fields until explicitly reviewed and confirmed by the buyer.
    """
    __tablename__ = "requirement_understandings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    requirement_id = Column(String(36), ForeignKey("buyer_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Input text snapshot
    raw_input_text = Column(Text, nullable=False)
    
    # Extracted structured suggestions
    # Keys: target_craft_id, craft_name, category_name, desired_materials, desired_techniques,
    # desired_motifs, required_quantity, target_unit_price_inr, max_budget_inr,
    # deadline_date, requires_gi_certification, requires_customization, preferred_region
    extracted_fields_json = Column(JSON, default=dict, nullable=False)
    
    # Calibrated confidence scores (or null if uncalibrated)
    confidence_scores_json = Column(JSON, default=dict, nullable=False)
    
    # AI Execution Provenance
    provider = Column(String(50), nullable=False, default="gemini")
    model_name = Column(String(100), nullable=False, default="gemini-1.5-flash")
    prompt_version = Column(String(50), nullable=False, default="rfq_understanding_v1")
    
    # Staging Lifecycle & Human Confirmation
    status = Column(
        String(30),
        nullable=False,
        default="SUGGESTED",
        index=True,
        doc="SUGGESTED, CONFIRMED, REJECTED"
    )
    is_confirmed_by_buyer = Column(Boolean, nullable=False, default=False)
    confirmed_fields_json = Column(JSON, nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requirement = relationship("BuyerRequirement", back_populates="understandings")
    buyer = relationship("BuyerProfile")
