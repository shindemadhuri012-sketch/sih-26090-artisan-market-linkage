"""
SIH 26090: Governance & Moderation Schemas
Pydantic v2 schemas for review signals, moderation decisions,
tamper-evident audit timelines, and governance dashboards.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator


class GovernanceFlagCreate(BaseModel):
    entity_type: str = Field(..., description="Product, ArtisanProfile, CraftPassport, MarketPriceObservation")
    entity_id: str = Field(...)
    flag_type: str = Field(..., description="MISSING_PROVENANCE, PRICE_ANOMALY_REVIEW, UNSUPPORTED_CLAIM, EXPIRED_EVIDENCE, DUPLICATE_SOURCE, STALE_MARKET_DATA, SAMPLE_EXPOSURE")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    details_json: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid severity. Allowed: {sorted(list(allowed))}")
        return v.upper()


class GovernanceFlagResolveRequest(BaseModel):
    decision: str = Field(..., description="RESOLVED_VALIDATED, RESOLVED_CORRECTED, RESOLVED_ACTIONED, DISMISSED")
    resolution_notes: str = Field(..., min_length=5, description="Clear explanation of the resolution action")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"RESOLVED_VALIDATED", "RESOLVED_CORRECTED", "RESOLVED_ACTIONED", "DISMISSED"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid decision. Allowed: {sorted(list(allowed))}")
        return v.upper()


class GovernanceFlagResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    flag_type: str
    severity: str
    status: str
    details_json: Dict[str, Any]
    flagged_by_user_id: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class GovernanceFlagListResponse(BaseModel):
    items: List[GovernanceFlagResponse]
    total: int
    page: int
    page_size: int


class ModerationDecisionRequest(BaseModel):
    entity_type: str = Field(..., description="PRODUCT, ARTISAN, VERIFICATION, PASSPORT")
    entity_id: str = Field(...)
    decision: str = Field(..., description="APPROVE, REJECT, REQUEST_CHANGES, SUSPEND, RESTORE")
    reason_category: Optional[str] = Field(default=None, description="QUALITY_DEFICIENCY, AUTHENTICITY_VERIFIED, INCORRECT_ATTRIBUTES, POLICY_VIOLATION, OTHER")
    moderator_notes: Optional[str] = Field(default=None, description="Internal notes (never shown publicly)")
    feedback_to_user: Optional[str] = Field(default=None, description="Actionable feedback delivered to artisan/resource owner")
    evidence_reference: Optional[str] = Field(default=None, description="Official registry ID or gazette reference. Required to grant authority verification.")
    idempotency_key: Optional[str] = Field(default=None, description="Client UUID protecting against double-click/network retry")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"APPROVE", "REJECT", "REQUEST_CHANGES", "SUSPEND", "RESTORE"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid decision. Allowed: {sorted(list(allowed))}")
        return v.upper()


class ModerationActionResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    previous_status: Optional[str] = None
    new_status: str
    decision: str
    moderator_user_id: Optional[str] = None
    reason_category: Optional[str] = None
    moderator_notes: Optional[str] = None
    feedback_to_user: Optional[str] = None
    evidence_reference: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class ModerationQueueItemResponse(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    artisan_id: Optional[str] = None
    artisan_name: Optional[str] = None
    craft_name: Optional[str] = None
    price_inr: Optional[str] = None
    status: str
    submitted_at: str


class ModerationQueueListResponse(BaseModel):
    items: List[ModerationQueueItemResponse]
    total: int
    page: int
    page_size: int


class ProvenanceEventResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    field_name: str
    previous_value_json: Any = None
    new_value_json: Any
    provenance_state: str
    actor_user_id: Optional[str] = None
    actor_role: str
    change_reason: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    evidence_reference: Optional[str] = None
    ai_model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    human_confirmation_status: bool
    event_hash: str
    previous_event_hash: str
    sequence_number: int
    created_at: str

    model_config = {"from_attributes": True}


class ProvenanceTimelineResponse(BaseModel):
    entity_type: str
    entity_id: str
    total_events: int
    events: List[ProvenanceEventResponse]


class ProvenanceChainVerifyResponse(BaseModel):
    entity_type: str
    entity_id: str
    is_valid: bool
    total_events: int
    latest_sequence: Optional[int] = None
    tampered_event_id: Optional[str] = None
    tamper_reason: Optional[str] = None
    message: str


class GovernanceDashboardResponse(BaseModel):
    pending_product_reviews: int
    pending_verification_reviews: int
    pending_passport_reviews: int
    open_flags_total: int
    open_flags_by_severity: Dict[str, int]
    ai_suggestions_awaiting_review: int
    active_demo_records_count: int
