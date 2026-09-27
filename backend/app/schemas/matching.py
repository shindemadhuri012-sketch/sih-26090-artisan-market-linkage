"""
SIH 26090: Matching & RFQ Linkage Schemas
Pydantic v2 DTOs for buyer requirements, AI understanding, matches, and RFQs.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class BuyerRequirementCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    raw_text: str = Field(..., min_length=10, description="Full natural language brief or RFQ description")
    target_craft_id: Optional[str] = Field(default=None)
    target_category_id: Optional[str] = Field(default=None)
    required_quantity: int = Field(..., ge=1, description="Required order volume in units")
    target_unit_price_inr: Optional[Decimal] = Field(default=None, ge=0)
    max_budget_inr: Optional[Decimal] = Field(default=None, ge=0)
    deadline_date: datetime = Field(..., description="Target delivery deadline (ISO 8601)")
    requires_gi_certification: bool = Field(default=False)
    desired_materials: List[str] = Field(default_factory=list)
    desired_techniques: List[str] = Field(default_factory=list)
    desired_motifs: List[str] = Field(default_factory=list)
    preferred_region: Optional[str] = Field(default=None, max_length=100)
    max_acceptable_moq: Optional[int] = Field(default=None, ge=1)
    max_lead_time_days: Optional[int] = Field(default=None, ge=1)
    requires_customization: bool = Field(default=False)
    quality_specifications: Optional[str] = Field(default=None)
    packaging_requirements: Optional[str] = Field(default=None)
    destination_state: Optional[str] = Field(default=None, max_length=100)
    destination_pincode: Optional[str] = Field(default=None, max_length=10)


class BuyerRequirementUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    raw_text: Optional[str] = Field(default=None, min_length=10)
    target_craft_id: Optional[str] = None
    target_category_id: Optional[str] = None
    required_quantity: Optional[int] = Field(default=None, ge=1)
    target_unit_price_inr: Optional[Decimal] = Field(default=None, ge=0)
    max_budget_inr: Optional[Decimal] = Field(default=None, ge=0)
    deadline_date: Optional[datetime] = None
    requires_gi_certification: Optional[bool] = None
    desired_materials: Optional[List[str]] = None
    desired_techniques: Optional[List[str]] = None
    desired_motifs: Optional[List[str]] = None
    preferred_region: Optional[str] = None
    max_acceptable_moq: Optional[int] = None
    max_lead_time_days: Optional[int] = None
    requires_customization: Optional[bool] = None
    quality_specifications: Optional[str] = None
    packaging_requirements: Optional[str] = None
    destination_state: Optional[str] = None
    destination_pincode: Optional[str] = None
    status: Optional[str] = None


class BuyerRequirementResponse(BaseModel):
    id: str
    buyer_id: str
    title: str
    raw_text: str
    target_craft_id: Optional[str] = None
    target_category_id: Optional[str] = None
    required_quantity: int
    target_unit_price_inr: Optional[Decimal] = None
    max_budget_inr: Optional[Decimal] = None
    deadline_date: str
    requires_gi_certification: bool
    desired_materials: List[str]
    desired_techniques: List[str]
    desired_motifs: List[str]
    preferred_region: Optional[str] = None
    max_acceptable_moq: Optional[int] = None
    max_lead_time_days: Optional[int] = None
    requires_customization: bool
    quality_specifications: Optional[str] = None
    packaging_requirements: Optional[str] = None
    destination_state: Optional[str] = None
    destination_pincode: Optional[str] = None
    currency: str
    status: str
    has_embedding: bool
    embedding_model_version: Optional[str] = None
    data_provenance_level: str
    provenance_state: str
    created_at: str
    updated_at: str


class RequirementUnderstandingResponse(BaseModel):
    id: str
    requirement_id: str
    buyer_id: str
    raw_input_text: str
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, Any]
    provider: str
    model_name: str
    prompt_version: str
    status: str
    is_confirmed_by_buyer: bool
    confirmed_fields: Optional[Dict[str, Any]] = None
    confirmed_at: Optional[str] = None
    created_at: str


class RequirementUnderstandingConfirmRequest(BaseModel):
    overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional manual overrides for extracted parameters prior to canonical adoption"
    )


class MatchScorecardResponse(BaseModel):
    id: str
    requirement_id: str
    artisan_id: str
    product_id: Optional[str] = None
    composite_score: float
    semantic_similarity: float
    craft_compatibility: float
    material_compatibility: float
    technique_compatibility: float
    capacity_compatibility: float
    price_compatibility: float
    lead_time_compatibility: float
    provenance_bonus: float
    rank: int
    status: str
    data_sufficiency_state: str
    engine_version: str
    product_title: Optional[str] = None
    product_sku: Optional[str] = None
    product_price_inr: Optional[Decimal] = None
    artisan_name: Optional[str] = None
    artisan_state: Optional[str] = None
    artisan_district: Optional[str] = None
    craft_name: Optional[str] = None
    positive_reasons: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    summary_explanation: Optional[str] = None
    capacity_justification: Optional[str] = None
    price_justification: Optional[str] = None
    provenance_justification: Optional[str] = None
    created_at: str


class RFQCreateRequest(BaseModel):
    requirement_id: Optional[str] = None
    product_id: Optional[str] = None
    match_id: Optional[str] = None
    artisan_id: str
    proposed_quantity: int = Field(..., ge=1)
    proposed_unit_price: Decimal = Field(..., ge=0)
    message: str = Field(..., min_length=5)


class RFQResponseRequest(BaseModel):
    action: str = Field(..., description="ACCEPT, DECLINE, COUNTER_OFFER")
    counter_unit_price: Optional[Decimal] = Field(default=None, ge=0)
    counter_lead_time_days: Optional[int] = Field(default=None, ge=1)
    artisan_response_message: Optional[str] = None
    decline_reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in {"ACCEPT", "DECLINE", "COUNTER_OFFER"}:
            raise ValueError("action must be ACCEPT, DECLINE, or COUNTER_OFFER")
        return v_upper


class RFQBuyerDecisionRequest(BaseModel):
    action: str = Field(..., description="ACCEPT, DECLINE")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in {"ACCEPT", "DECLINE"}:
            raise ValueError("action must be ACCEPT or DECLINE")
        return v_upper


class RFQResponse(BaseModel):
    id: str
    rfq_reference_number: Optional[str] = None
    buyer_id: str
    artisan_id: str
    requirement_id: Optional[str] = None
    product_id: Optional[str] = None
    match_id: Optional[str] = None
    message: str
    proposed_quantity: int
    proposed_unit_price: Decimal
    currency: str
    status: str
    artisan_response_message: Optional[str] = None
    counter_unit_price: Optional[Decimal] = None
    counter_lead_time_days: Optional[int] = None
    decline_reason: Optional[str] = None
    product_title: Optional[str] = None
    buyer_company_name: Optional[str] = None
    artisan_name: Optional[str] = None
    viewed_at: Optional[str] = None
    responded_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str
    updated_at: str
