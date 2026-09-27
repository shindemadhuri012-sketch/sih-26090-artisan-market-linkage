"""
SIH 26090: Demand Intelligence Schemas
Pydantic v2 schemas for demand observations, aggregations, trend analytics, and forecast outputs.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DemandObservationCreate(BaseModel):
    craft_id: str
    craft_category_id: Optional[str] = None
    geography_state: str = Field(..., max_length=100)
    observation_period_start: datetime
    observation_period_end: datetime
    total_enquiries: int = Field(0, ge=0)
    fulfilled_orders: int = Field(0, ge=0)
    unit_volume: int = Field(0, ge=0)
    monetary_volume_inr: Optional[Decimal] = Field(None, ge=0)
    average_realized_price: Optional[Decimal] = Field(None, ge=0)
    seasonal_festival_tag: Optional[str] = Field(None, max_length=50)
    signal_tier: str = Field("TRANSACTIONAL_CONFIRMED")
    observation_type: str = Field("PLATFORM_NATIVE")
    data_quality_status: str = Field("VERIFIED")
    data_source_id: Optional[str] = None
    ingestion_batch_id: Optional[str] = None
    is_sample_or_demo: bool = False

    @field_validator("observation_period_end")
    @classmethod
    def validate_period(cls, end_val: datetime, values: Any) -> datetime:
        start_val = values.data.get("observation_period_start")
        if start_val and end_val < start_val:
            raise ValueError("observation_period_end must be greater than or equal to observation_period_start")
        return end_val


class DemandObservationResponse(BaseModel):
    id: str
    craft_id: str
    craft_category_id: Optional[str] = None
    geography_state: str
    observation_period_start: str
    observation_period_end: str
    total_enquiries: int
    fulfilled_orders: int
    unit_volume: int
    monetary_volume_inr: Optional[Decimal] = None
    average_realized_price: Optional[Decimal] = None
    seasonal_festival_tag: Optional[str] = None
    signal_tier: str
    observation_type: str
    data_quality_status: str
    is_sample_or_demo: bool
    data_provenance_level: str
    created_at: Optional[str] = None


class DemandSummaryResponse(BaseModel):
    craft_id: Optional[str] = None
    craft_category_id: Optional[str] = None
    craft_name: Optional[str] = None
    geography_state: Optional[str] = None
    total_observations: int
    total_unit_volume: int
    total_monetary_volume_inr: Decimal
    total_enquiries: int
    total_fulfilled_orders: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    data_sufficiency_state: str


class DemandTrendResponse(BaseModel):
    craft_id: Optional[str] = None
    craft_name: Optional[str] = None
    geography_state: Optional[str] = None
    trend_status: str  # INCREASING, DECREASING, STABLE, INSUFFICIENT_DATA
    current_period_volume: Optional[int] = None
    previous_period_volume: Optional[int] = None
    absolute_change: Optional[int] = None
    percentage_change: Optional[float] = None
    rolling_average_3m: Optional[float] = None
    explanation: str
    observation_periods_count: int


class ForecastPointResponse(BaseModel):
    forecast_month: int
    forecast_year: int
    projected_demand_index: Optional[float] = None
    projected_unit_volume: Optional[int] = None
    uncertainty_lower: Optional[float] = None
    uncertainty_upper: Optional[float] = None
    data_sufficiency_status: str
    explanation_note: str


class DemandForecastResponse(BaseModel):
    run_id: Optional[str] = None
    craft_id: Optional[str] = None
    craft_name: Optional[str] = None
    geography_state: Optional[str] = None
    status: str
    model_name: str
    model_version: str
    training_start_date: Optional[str] = None
    training_end_date: Optional[str] = None
    observation_count: int
    validation_mape: Optional[float] = None
    validation_rmse: Optional[float] = None
    points: List[ForecastPointResponse]
    limitations_notes: str
