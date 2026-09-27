"""
SIH 26090: Product, Media & Moderation Schemas
Pydantic v2 schemas for artisan product management, inventory vs capacity separation,
media metadata validation, public catalogue views, and future AI suggestion contracts.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class AISuggestionContract(BaseModel):
    """
    Data Contract for future AI Product Studio suggestions.
    Represents AI recommendations alongside confidence scores and human confirmation flags.
    No AI inference is executed in Phase 3.
    """
    title_suggestion: Optional[str] = None
    description_suggestion: Optional[str] = None
    suggested_tags: List[str] = Field(default_factory=list)
    suggested_materials: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    model_name: Optional[str] = None
    timestamp: Optional[str] = None
    human_confirmed: bool = False


class ProductMediaCreate(BaseModel):
    media_type: str = Field(default="IMAGE", description="IMAGE, AUDIO_VOICE_NOTE, DOCUMENT")
    url: str = Field(..., description="HTTPS storage or mock object storage URL")
    thumbnail_url: Optional[str] = Field(default=None, description="HTTPS thumbnail URL")
    storage_key: Optional[str] = Field(default=None, max_length=255, description="Object storage S3/MinIO bucket key")
    original_filename: str = Field(..., min_length=1, max_length=255, description="Filename from client upload")
    file_size_bytes: int = Field(..., gt=0, le=10485760, description="File size in bytes (max 10MB)")
    mime_type: str = Field(..., max_length=50, description="MIME type of uploaded asset")
    checksum_sha256: Optional[str] = Field(default=None, max_length=64, description="SHA-256 digest of media file")
    width: Optional[int] = Field(default=None, gt=0, description="Image width in pixels")
    height: Optional[int] = Field(default=None, gt=0, description="Image height in pixels")
    sort_order: int = Field(default=0, ge=0, description="Display order sequence index")
    alt_text: Optional[str] = Field(default=None, max_length=255, description="Accessible descriptive alt text")
    is_primary: bool = Field(default=False, description="Whether this is the cover thumbnail asset")

    @field_validator("mime_type")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        allowed = {
            "image/jpeg", "image/png", "image/webp",
            "audio/mpeg", "audio/wav", "audio/ogg",
            "application/pdf"
        }
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"Disallowed MIME type '{v}'. Allowed types: {sorted(list(allowed))}")
        return v_clean

    @field_validator("original_filename")
    @classmethod
    def validate_filename_safety(cls, v: str) -> str:
        v_clean = v.strip()
        if re.search(r"[\/\\:\*\?\"<>\|]", v_clean) or ".." in v_clean:
            raise ValueError("Filename contains suspicious characters or path traversal elements.")
        return v_clean


class ProductMediaResponse(BaseModel):
    id: str
    product_id: str
    media_type: str
    url: str
    thumbnail_url: Optional[str] = None
    storage_key: Optional[str] = None
    original_filename: str
    file_size_bytes: int
    mime_type: str
    checksum_sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sort_order: int
    alt_text: Optional[str] = None
    is_primary: bool
    created_at: str

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    craft_id: str = Field(..., description="UUID of craft from master directory")
    category_id: Optional[str] = Field(default=None, description="Optional craft category UUID")
    title: str = Field(..., min_length=3, max_length=255, description="Product listing title")
    storytelling_description: str = Field(..., min_length=10, description="Detailed artisanal narrative and origin description")
    price_inr: float = Field(..., ge=0.0, description="Artisan-declared selling price in Indian Rupees (INR)")
    currency: str = Field(default="INR", description="Currency standard (INR)")
    stock_quantity: int = Field(default=1, ge=0, description="Current ready-to-ship finished inventory stock")
    monthly_production_capacity: int = Field(default=10, ge=0, description="Monthly sustainable production capacity")
    min_order_quantity: int = Field(default=1, ge=1, description="Minimum order quantity (MOQ) for procurement")
    lead_time_days: int = Field(default=7, ge=0, description="Production turnaround lead time in days")
    availability_status: str = Field(default="AVAILABLE", description="AVAILABLE, MADE_TO_ORDER, OUT_OF_STOCK")
    region: Optional[str] = Field(default=None, max_length=100, description="Cluster or geographic origin region")
    materials: List[str] = Field(default_factory=list, description="Authentic raw materials utilized")
    primary_color: Optional[str] = Field(default=None, max_length=50, description="Dominant aesthetic color")
    dimensions: Optional[str] = Field(default=None, max_length=100, description="Physical dimensions e.g. '200cm x 115cm'")
    weight_grams: Optional[int] = Field(default=None, ge=0, description="Net weight in grams")
    technique: Optional[str] = Field(default=None, max_length=150, description="Traditional craft technique applied")
    style: Optional[str] = Field(default=None, max_length=100, description="Aesthetic style (Traditional, Contemporary, Folk)")
    tags: List[str] = Field(default_factory=list, description="Keywords for search indexation")
    is_customizable: bool = Field(default=False, description="Whether custom order dimensions or bespoke motifs are accepted")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() != "INR":
            raise ValueError("Platform transactions currently accept only 'INR'.")
        return "INR"

    @field_validator("availability_status")
    @classmethod
    def validate_availability(cls, v: str) -> str:
        allowed = {"AVAILABLE", "MADE_TO_ORDER", "OUT_OF_STOCK"}
        v_upper = v.strip().upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid availability_status. Allowed: {sorted(list(allowed))}")
        return v_upper


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    storytelling_description: Optional[str] = Field(default=None, min_length=10)
    price_inr: Optional[float] = Field(default=None, ge=0.0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    monthly_production_capacity: Optional[int] = Field(default=None, ge=0)
    min_order_quantity: Optional[int] = Field(default=None, ge=1)
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    availability_status: Optional[str] = None
    region: Optional[str] = None
    materials: Optional[List[str]] = None
    primary_color: Optional[str] = None
    dimensions: Optional[str] = None
    weight_grams: Optional[int] = None
    technique: Optional[str] = None
    style: Optional[str] = None
    tags: Optional[List[str]] = None
    is_customizable: Optional[bool] = None

    @field_validator("availability_status")
    @classmethod
    def validate_availability(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"AVAILABLE", "MADE_TO_ORDER", "OUT_OF_STOCK"}
        v_upper = v.strip().upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid availability_status. Allowed: {sorted(list(allowed))}")
        return v_upper


class ProductResponse(ProductBase):
    id: str
    artisan_id: str
    sku: Optional[str] = None
    status: str
    provenance_status: str
    ai_metadata: Dict[str, Any] = Field(default_factory=dict)
    admin_feedback: Optional[str] = None
    craft_name: Optional[str] = None
    category_name: Optional[str] = None
    media: List[ProductMediaResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProductPublicResponse(BaseModel):
    """
    Sanitized public catalogue view for buyers and guests.
    Strictly omits private artisan phone, address, and Pehchan IDs.
    """
    id: str
    sku: Optional[str] = None
    title: str
    storytelling_description: str
    price_inr: float
    currency: str
    stock_quantity: int
    monthly_production_capacity: int
    min_order_quantity: int
    lead_time_days: int
    availability_status: str
    region: Optional[str] = None
    materials: List[str]
    primary_color: Optional[str] = None
    dimensions: Optional[str] = None
    weight_grams: Optional[int] = None
    technique: Optional[str] = None
    style: Optional[str] = None
    tags: List[str]
    is_customizable: bool
    status: str
    provenance_status: str
    craft_name: Optional[str] = None
    category_name: Optional[str] = None
    artisan_public_name: Optional[str] = None
    artisan_district: Optional[str] = None
    artisan_state: Optional[str] = None
    has_gi_tag: bool = False
    gi_tag_number: Optional[str] = None
    media: List[ProductMediaResponse] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: List[ProductPublicResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductModerationRequest(BaseModel):
    decision: str = Field(..., description="APPROVE, REJECT, REQUEST_CORRECTION")
    admin_notes: Optional[str] = Field(default=None, description="Audited feedback note from administrator")
    rejection_reason: Optional[str] = Field(default=None, description="Public reason if rejected")
    authoritative_evidence_reference: Optional[str] = Field(default=None, description="Official government gazette or CGPDTM AU registry reference. Required to grant authority verification.")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"APPROVE", "REJECT", "REQUEST_CORRECTION"}
        v_upper = v.strip().upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid decision. Allowed: {sorted(list(allowed))}")
        return v_upper
