"""
SIH 26090: Craft Passport Schemas
Pydantic v2 schemas for digital Craft Passport creation, status checks, and public QR verification.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CraftPassportCreate(BaseModel):
    craft_id: str = Field(..., description="UUID of craft from master catalog")
    authorized_user_gi_certificate: Optional[str] = Field(
        default=None,
        description="Official GI Authorized User certificate number or reference"
    )


class CraftPassportResponse(BaseModel):
    id: str
    artisan_id: str
    craft_id: str
    craft_name: Optional[str] = None
    passport_uuid: str
    qr_code_url: str
    authorized_user_gi_certificate: Optional[str]
    verification_level: str
    status: str
    issued_at: str
    expires_at: Optional[str]
    provenance_hash: str

    model_config = {"from_attributes": True}


class PublicPassportVerificationResponse(BaseModel):
    """
    Sanitized public verification response rendered when scanning a Craft Passport QR code.
    Reveals only intentionally public authenticity credentials; zero personal contact details.
    """
    passport_uuid: str
    status: str
    verification_level: str
    issued_at: str
    artisan_public_name: str
    craft_name: str
    origin_state: str
    origin_district: str
    gi_tag_number: Optional[str]
    has_gi_tag: bool
    cultural_heritage_description: str
    traditional_raw_materials: List[str]
    provenance_hash: Optional[str] = None
    is_valid: bool = True
    provenance_metadata: Optional[Dict[str, Any]] = None
