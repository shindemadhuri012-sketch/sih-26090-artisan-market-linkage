"""
SIH 26090: Fair-Price Intelligence Schemas
Pydantic v2 schemas for transparent artisan cost breakdowns, source-backed market observations,
deterministic price analysis responses, and traceable explanations.
Strict Decimal enforcement for all financial and monetary values.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MaterialCostItem(BaseModel):
    """Line item for raw materials used in craft production."""
    material_name: str = Field(..., min_length=1, max_length=150, description="Name of the material (e.g. Mulberry Silk, Natural Indigo Dye)")
    quantity: Decimal = Field(..., gt=Decimal("0"), description="Quantity consumed")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement (e.g. meters, kg, grams, spools)")
    unit_cost_inr: Decimal = Field(..., ge=Decimal("0"), description="Unit cost in INR")
    total_cost_inr: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Total cost = quantity * unit_cost")
    source_type: str = Field(default="ARTISAN_ENTERED", description="ARTISAN_ENTERED, DOCUMENTED_INVOICE, COMMODITY_BOARD, SOURCE_BACKED")
    source_reference: Optional[str] = Field(default=None, max_length=255, description="Invoice number, supplier name, or receipt note")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_types = {"ARTISAN_ENTERED", "DOCUMENTED_INVOICE", "COMMODITY_BOARD", "SOURCE_BACKED"}
        v_upper = v.strip().upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid material source_type '{v}'. Allowed: {sorted(list(valid_types))}")
        return v_upper


class CostBreakdownCreate(BaseModel):
    """Payload to create or update an artisan's structured production cost breakdown."""
    materials: List[MaterialCostItem] = Field(default_factory=list, description="Itemized raw material lines")
    labor_calculation_method: str = Field(default="HOURLY_RATE", description="HOURLY_RATE or TOTAL_STATED")
    labor_hours: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Hours invested in producing the batch/unit")
    hourly_labor_rate: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Hourly labor rate in INR")
    total_labor_cost: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Artisan stated total labor cost if not using hourly rate")

    packaging_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), description="Packaging cost per batch/product")
    transport_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), description="Freight / logistics cost per batch/product")
    overhead_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), description="Documented overhead (rent, utilities, equipment depreciation)")
    overhead_allocation_basis: str = Field(default="PER_PRODUCT", description="PER_PRODUCT, PER_BATCH, MONTHLY_ALLOCATION, DOCUMENTED_PERCENTAGE")
    other_costs: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), description="Other documented incidental costs")
    other_costs_description: Optional[str] = Field(default=None, description="Explanation for other incidental costs")

    batch_quantity: int = Field(default=1, ge=1, description="Number of product units produced by this cost batch")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="Currency ISO code")
    current_selling_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Current price listed by artisan")
    desired_margin_percentage: Decimal = Field(default=Decimal("25.00"), ge=Decimal("0"), le=Decimal("500.00"), description="Target profit margin percentage (e.g. 25.00 for 25%)")

    @field_validator("labor_calculation_method")
    @classmethod
    def validate_labor_method(cls, v: str) -> str:
        valid_methods = {"HOURLY_RATE", "TOTAL_STATED"}
        v_upper = v.strip().upper()
        if v_upper not in valid_methods:
            raise ValueError(f"Invalid labor_calculation_method '{v}'. Allowed: {sorted(list(valid_methods))}")
        return v_upper

    @field_validator("overhead_allocation_basis")
    @classmethod
    def validate_overhead_basis(cls, v: str) -> str:
        valid_bases = {"PER_PRODUCT", "PER_BATCH", "MONTHLY_ALLOCATION", "DOCUMENTED_PERCENTAGE"}
        v_upper = v.strip().upper()
        if v_upper not in valid_bases:
            raise ValueError(f"Invalid overhead_allocation_basis '{v}'. Allowed: {sorted(list(valid_bases))}")
        return v_upper


class CostBreakdownResponse(BaseModel):
    """Complete cost breakdown response with calculated baselines."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    artisan_id: str
    materials: List[Dict[str, Any]]
    total_material_cost: Decimal
    labor_calculation_method: str
    labor_hours: Optional[Decimal] = None
    hourly_labor_rate: Optional[Decimal] = None
    total_labor_cost: Decimal
    packaging_cost: Decimal
    transport_cost: Decimal
    overhead_cost: Decimal
    overhead_allocation_basis: str
    other_costs: Decimal
    other_costs_description: Optional[str] = None
    batch_quantity: int
    currency: str
    current_selling_price: Optional[Decimal] = None
    desired_margin_percentage: Decimal
    total_production_cost: Decimal
    cost_baseline_unit_cost: Decimal
    cost_baseline_recommended_price: Decimal
    provenance_status: str
    created_at: datetime
    updated_at: datetime


class MarketPriceObservationCreate(BaseModel):
    """Schema for ingesting an authentic, source-backed market price observation."""
    craft_id: str
    craft_category_id: Optional[str] = None
    product_title: Optional[str] = Field(default=None, max_length=255)
    observed_price: Decimal = Field(..., gt=Decimal("0"), description="Documented observed retail or wholesale price")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    source_name: str = Field(..., min_length=2, max_length=255, description="Authoritative or documented source (e.g. Tribes India / TRIFED)")
    source_url: Optional[str] = Field(default=None, description="Direct URL or official catalogue link")
    source_type: str = Field(default="GOVERNMENT", description="GOVERNMENT, OFFICIAL_REGISTRY, OFFICIAL_MARKETPLACE, VERIFIED_ARTISAN, AUTHORIZED_SOURCE, OTHER_DOCUMENTED_SOURCE")
    geography_state: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    observation_date: datetime
    original_source_id: Optional[str] = Field(default=None, max_length=100)
    license_or_usage_info: Optional[str] = None
    attributes_json: Dict[str, Any] = Field(default_factory=dict)
    comparability_tags: List[str] = Field(default_factory=list)
    evidence_quality_status: str = Field(default="MEDIUM", description="HIGH, MEDIUM, LOW, INSUFFICIENT")
    verification_status: str = Field(default="DOCUMENTED", description="DOCUMENTED, VERIFIED, PENDING_REVIEW, REJECTED")
    data_source_id: Optional[str] = None
    is_sample_or_demo: bool = False
    ingestion_batch_id: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_types = {
            "GOVERNMENT", "OFFICIAL_REGISTRY", "OFFICIAL_MARKETPLACE",
            "VERIFIED_ARTISAN", "AUTHORIZED_SOURCE", "OTHER_DOCUMENTED_SOURCE"
        }
        v_upper = v.strip().upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid source_type '{v}'. Allowed: {sorted(list(valid_types))}")
        return v_upper

    @field_validator("evidence_quality_status")
    @classmethod
    def validate_quality_status(cls, v: str) -> str:
        valid_statuses = {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}
        v_upper = v.strip().upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Invalid evidence_quality_status '{v}'. Allowed: {sorted(list(valid_statuses))}")
        return v_upper


class MarketPriceObservationResponse(BaseModel):
    """Response representation for market price observations with full provenance."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    craft_id: str
    craft_category_id: Optional[str] = None
    product_title: Optional[str] = None
    observed_price: Decimal
    currency: str
    source_name: str
    source_url: Optional[str] = None
    source_type: str
    geography_state: Optional[str] = None
    region: Optional[str] = None
    observation_date: datetime
    retrieval_timestamp: datetime
    original_source_id: Optional[str] = None
    license_or_usage_info: Optional[str] = None
    attributes_json: Dict[str, Any]
    comparability_tags: List[str]
    evidence_quality_status: str
    verification_status: str
    data_source_id: Optional[str] = None
    data_provenance_level: str
    is_sample_or_demo: bool
    ingestion_batch_id: Optional[str] = None
    created_at: datetime


class PriceAnalysisResponse(BaseModel):
    """
    Transparent, explainable price analysis generated by FAIR_PRICE_ENGINE_V1.
    Strictly separates Cost Baseline, Market Evidence, and Fair Price Range.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    artisan_id: Optional[str] = None
    cost_breakdown_id: Optional[str] = None
    engine_version: str
    currency: str
    evidence_status: str

    # Structured conceptual layers
    cost_baseline: Dict[str, Any]
    market_evidence: Dict[str, Any]
    fair_price_analysis: Dict[str, Any]

    # Traceable explanation steps and limitations
    explanation_steps: List[Dict[str, Any]]
    limitations_notes: List[str]

    provenance_state: str
    is_confirmed_by_artisan: bool
    confirmed_price_inr: Optional[Decimal] = None
    artisan_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PriceConfirmationRequest(BaseModel):
    """Payload for an artisan to confirm or apply a recommended fair price to their product."""
    confirmed_price_inr: Decimal = Field(..., gt=Decimal("0"), description="The price confirmed by the artisan in INR")
    artisan_notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes explaining the confirmed price")
    apply_to_product: bool = Field(default=True, description="Whether to update product.price_inr directly with this confirmed price")
