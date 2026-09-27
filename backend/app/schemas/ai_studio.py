"""
SIH 26090: AI Product Studio Pydantic Schemas
Strict schemas for AI analysis requests, suggestion responses, provenance metadata,
and human confirmation payloads.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AIAnalyzeRequest(BaseModel):
    """Request payload to initiate AI analysis on a product media asset."""
    media_id: str = Field(..., description="UUID of the ProductMedia asset to analyze")
    force_reanalyze: bool = Field(default=False, description="Bypass idempotency cache and re-run vision inference")
    provider_override: Optional[str] = Field(default=None, description="Optional provider override (e.g. mock for testing)")


class AISuggestionResponse(BaseModel):
    """Detailed response for a single field-level AI suggestion."""
    id: str
    analysis_id: str
    product_id: str
    field_name: str
    suggested_value: Any
    confidence: Optional[float] = None
    source_type: str
    human_confirmed: bool
    confirmed_value: Optional[Any] = None
    status: str
    artisan_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AIAnalysisResponse(BaseModel):
    """Response encapsulating an entire AI analysis run and its child suggestions."""
    id: str
    product_id: str
    media_id: Optional[str] = None
    media_checksum: Optional[str] = None
    provider: str
    model_name: str
    model_version: Optional[str] = None
    prompt_version: str
    status: str
    error_message: Optional[str] = None
    processing_duration_ms: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    suggestions: List[AISuggestionResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class FieldConfirmationItem(BaseModel):
    """Artisan confirmation decision for an individual suggested field."""
    field_name: str = Field(..., description="Target product attribute field name")
    action: str = Field(..., description="Decision action: ACCEPT, EDIT, or REJECT")
    custom_value: Optional[Any] = Field(default=None, description="Artisan edited value if action is EDIT")
    notes: Optional[str] = Field(default=None, description="Optional artisan rationale notes")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in {"ACCEPT", "EDIT", "REJECT"}:
            raise ValueError(f"Invalid confirmation action '{v}'. Must be ACCEPT, EDIT, or REJECT.")
        return v_upper


class AIConfirmRequest(BaseModel):
    """Batch confirmation request from an artisan reviewing AI suggestions."""
    confirmations: List[FieldConfirmationItem] = Field(
        ...,
        min_length=1,
        description="List of field-level decisions by the artisan"
    )
    apply_to_product: bool = Field(
        default=True,
        description="Whether to immediately apply confirmed attributes to the canonical Product listing"
    )


class AIRejectRequest(BaseModel):
    """Request to bulk-reject all suggestions for an analysis."""
    reason: Optional[str] = Field(default=None, description="Optional reason for rejecting AI suggestions")
