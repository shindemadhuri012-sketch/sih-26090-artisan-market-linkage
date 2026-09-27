"""
SIH 26090: Verification Workflow Schemas
Pydantic v2 schemas for artisan KYC submission and administrator verification reviews.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class VerificationSubmitRequest(BaseModel):
    document_type: str = Field(
        ...,
        description="PEHCHAN_CARD, AADHAAR, GI_AUTHORIZED_USER_CERT, COOPERATIVE_MEMBERSHIP"
    )
    document_url: str = Field(..., description="Secure storage URL or pre-signed key of uploaded proof")

    @field_validator("document_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        valid_types = {"PEHCHAN_CARD", "AADHAAR", "GI_AUTHORIZED_USER_CERT", "COOPERATIVE_MEMBERSHIP"}
        v_upper = v.strip().upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid document_type. Must be one of: {sorted(list(valid_types))}")
        return v_upper


class VerificationReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVE, REJECT, REQUEST_CORRECTION")
    admin_notes: str = Field(..., min_length=5, description="Audited review commentary explaining the decision")
    rejection_reason: Optional[str] = Field(default=None, description="Detailed explanation if rejected")
    authoritative_registry_reference: Optional[str] = Field(default=None, description="Official government gazette or CGPDTM AU registry reference. Required to grant AUTHORITY_VERIFIED.")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        valid_decisions = {"APPROVE", "REJECT", "REQUEST_CORRECTION"}
        v_upper = v.strip().upper()
        if v_upper not in valid_decisions:
            raise ValueError(f"Invalid decision. Must be one of: {sorted(list(valid_decisions))}")
        return v_upper


class VerificationResponse(BaseModel):
    id: str
    artisan_id: str
    verifier_user_id: Optional[str]
    document_type: str
    document_url: str
    verification_status: str
    rejection_reason: Optional[str]
    admin_notes: Optional[str]
    decision_date: Optional[str]
    verified_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}
