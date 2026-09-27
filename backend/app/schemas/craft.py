"""
SIH 26090: Craft, Category & Artisan Association Schemas
Pydantic v2 schemas for master craft catalogue, hierarchical categories, and artisan-craft linkage.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CraftCategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Category name (e.g. Handloom Textiles, Metalcraft)")
    description: Optional[str] = Field(default=None, description="Category overview and classification context")
    icon_url: Optional[str] = Field(default=None, description="SVG or PNG icon URL")
    parent_id: Optional[str] = Field(default=None, description="Parent category UUID for hierarchical categorization")


class CraftCategoryCreate(CraftCategoryBase):
    pass


class CraftCategoryResponse(CraftCategoryBase):
    id: str
    created_at: str

    model_config = {"from_attributes": True}


class CraftCategoryTreeResponse(CraftCategoryResponse):
    subcategories: List[CraftCategoryResponse] = []

    model_config = {"from_attributes": True}


class CraftBase(BaseModel):
    category_id: str = Field(..., description="UUID of parent craft category")
    name: str = Field(..., min_length=2, max_length=150, description="Official master craft name")
    gi_tag_number: Optional[str] = Field(default=None, max_length=50, description="Official GI registration tag number")
    has_gi_tag: bool = Field(default=False, description="Whether craft holds registered Geographical Indication")
    origin_state: str = Field(..., max_length=100, description="State of traditional origin")
    origin_district: str = Field(..., max_length=100, description="District cluster of traditional origin")
    region: Optional[str] = Field(default=None, max_length=100, description="Geographic zone (Central India, Western India, etc.)")
    cultural_heritage_description: str = Field(..., min_length=10, description="Context, history, and craft lineage")
    traditional_technique: Optional[str] = Field(default=None, description="Description of traditional artisanal technique")
    traditional_raw_materials: List[str] = Field(default_factory=list, description="Authentic traditional materials used")
    is_active: bool = Field(default=True, description="Whether craft is currently active in master directory")


class CraftCreate(CraftBase):
    pass


class CraftUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    gi_tag_number: Optional[str] = None
    has_gi_tag: Optional[bool] = None
    origin_state: Optional[str] = None
    origin_district: Optional[str] = None
    region: Optional[str] = None
    cultural_heritage_description: Optional[str] = None
    traditional_technique: Optional[str] = None
    traditional_raw_materials: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CraftResponse(CraftBase):
    id: str
    normalized_name: Optional[str] = None
    category_name: Optional[str] = None
    data_source_id: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class CraftListResponse(BaseModel):
    items: List[CraftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ArtisanCraftLinkRequest(BaseModel):
    craft_id: str = Field(..., description="UUID of craft from master catalog")
    skill_level: str = Field(default="SKILLED", description="MASTER_CRAFTSMAN, SKILLED, APPRENTICE")
    years_of_experience: int = Field(default=1, ge=0, le=100, description="Years practicing this specific craft")
    is_primary: bool = Field(default=False, description="Whether this is the artisan's primary craft specialization")
    technique: Optional[str] = Field(default=None, max_length=150, description="Specific technique practiced (e.g. Zari brocade, Pit loom)")
    evidence_url: Optional[str] = Field(default=None, description="URL of supporting certificate, portfolio, or award")

    @field_validator("skill_level")
    @classmethod
    def validate_skill(cls, v: str) -> str:
        valid_tiers = {"MASTER_CRAFTSMAN", "SKILLED", "APPRENTICE"}
        v_upper = v.strip().upper()
        if v_upper not in valid_tiers:
            raise ValueError(f"Invalid skill_level. Allowed: {sorted(list(valid_tiers))}")
        return v_upper


class ArtisanCraftResponse(BaseModel):
    id: str
    artisan_id: str
    craft_id: str
    craft_name: Optional[str] = None
    skill_level: str
    years_of_experience: int
    is_primary: bool
    technique: Optional[str] = None
    evidence_url: Optional[str] = None
    status: str
    created_at: str

    model_config = {"from_attributes": True}
