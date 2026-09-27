"""
SIH 26090: Buyer Profile Schemas
Pydantic v2 schemas for institutional and retail buyer profile management.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BuyerProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    buyer_type: str = Field(
        ...,
        description="RETAIL_CURATOR, INSTITUTIONAL_GIFTING, GOVERNMENT_GEM, EXPORT_AGGREGATOR"
    )
    gstin: Optional[str] = Field(default=None, max_length=20)
    country: str = Field(default="India", max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    typical_order_volume: Optional[str] = Field(default=None, max_length=50)

    @field_validator("buyer_type")
    @classmethod
    def validate_buyer_type(cls, v: str) -> str:
        valid_types = {"RETAIL_CURATOR", "INSTITUTIONAL_GIFTING", "GOVERNMENT_GEM", "EXPORT_AGGREGATOR"}
        v_upper = v.strip().upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid buyer_type. Must be one of: {sorted(list(valid_types))}")
        return v_upper


class BuyerProfileUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    buyer_type: Optional[str] = Field(default=None)
    gstin: Optional[str] = Field(default=None, max_length=20)
    state: Optional[str] = Field(default=None, max_length=100)
    typical_order_volume: Optional[str] = Field(default=None, max_length=50)

    @field_validator("buyer_type")
    @classmethod
    def validate_buyer_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        valid_types = {"RETAIL_CURATOR", "INSTITUTIONAL_GIFTING", "GOVERNMENT_GEM", "EXPORT_AGGREGATOR"}
        v_upper = v.strip().upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid buyer_type. Must be one of: {sorted(list(valid_types))}")
        return v_upper


class BuyerProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    buyer_type: str
    gstin: Optional[str]
    country: str
    state: Optional[str]
    typical_order_volume: Optional[str]
    is_verified_buyer: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
