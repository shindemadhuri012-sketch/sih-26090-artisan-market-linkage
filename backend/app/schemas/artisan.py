"""
SIH 26090: Artisan Profile Schemas
Pydantic v2 schemas for private artisan profile CRUD and sanitized public views.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ArtisanProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=10)
    primary_craft_id: str = Field(..., description="UUID of primary craft from crafts catalog")
    cooperative_name: Optional[str] = Field(default=None, max_length=200)
    address_line: Optional[str] = Field(default=None)
    years_of_experience: int = Field(default=1, ge=0, le=80)
    monthly_production_capacity: int = Field(default=10, ge=1, le=100000)
    pehchan_id: Optional[str] = Field(default=None, max_length=50, description="Ministry of Textiles Pehchan Card Number")


class ArtisanProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    cooperative_name: Optional[str] = Field(default=None, max_length=200)
    address_line: Optional[str] = Field(default=None)
    pincode: Optional[str] = Field(default=None, min_length=6, max_length=10)
    years_of_experience: Optional[int] = Field(default=None, ge=0, le=80)
    monthly_production_capacity: Optional[int] = Field(default=None, ge=1, le=100000)
    pehchan_id: Optional[str] = Field(default=None, max_length=50)


class ArtisanProfileResponse(BaseModel):
    """Private profile response returned to the authenticated artisan owner."""
    id: str
    user_id: str
    full_name: str
    cooperative_name: Optional[str]
    state: str
    district: str
    pincode: str
    address_line: Optional[str]
    primary_craft_id: str
    years_of_experience: int
    monthly_production_capacity: int
    pehchan_id: Optional[str]
    verification_status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ArtisanPublicProfileResponse(BaseModel):
    """Sanitized public profile view (does not leak private address or personal phone)."""
    id: str
    full_name: str
    state: str
    district: str
    craft_name: Optional[str] = None
    years_of_experience: int
    verification_status: str

    model_config = {"from_attributes": True}
