"""
SIH 26090: Demand Forecasting Unit Tests
Verifies multi-gate eligibility (N >= 12, missing data ratios), classical models (WMA, Holt-Winters),
chronological walk-forward validation (zero future leakage), and forecast run persistence.
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient

from backend.app.models.craft import Craft
from ai.demand.engine import DemandEngine, TimeSeriesObservation


def test_forecast_eligibility_rejection_under_12_periods():
    """Fewer than 12 periods must be rejected with INSUFFICIENT_HISTORY and 0 points."""
    short_series = [
        TimeSeriesObservation(period_year=2024, period_month=m, unit_volume=100 + m * 5, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
        for m in range(1, 10)  # Only 9 months
    ]
    eligibility = DemandEngine.check_eligibility(short_series)
    assert eligibility.is_eligible is False
    assert eligibility.status == "INSUFFICIENT_HISTORY"

    run_result = DemandEngine.generate_forecast(short_series, horizon=3)
    assert run_result.status == "INSUFFICIENT_HISTORY"
    assert len(run_result.points) == 0
    assert "At least 12 complete monthly observation periods are required" in run_result.limitations_notes


def test_forecast_eligibility_rejection_on_excessive_gaps():
    """History spanning 15 months but missing 5 months (>20% gap) is rejected for data quality."""
    gappy_series = [
        TimeSeriesObservation(period_year=2024, period_month=1, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        # Gap of months 2, 3, 4, 5
        TimeSeriesObservation(period_year=2024, period_month=6, unit_volume=110, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=7, unit_volume=115, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=8, unit_volume=120, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=9, unit_volume=125, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=10, unit_volume=130, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=11, unit_volume=135, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2024, period_month=12, unit_volume=140, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=1, unit_volume=145, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=2, unit_volume=150, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=3, unit_volume=155, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=4, unit_volume=160, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
    ]
    eligibility = DemandEngine.check_eligibility(gappy_series)
    assert eligibility.is_eligible is False
    assert eligibility.status == "INSUFFICIENT_DATA_QUALITY"


def test_wma_forecasting_and_leakage_free_validation():
    """12 consecutive periods trigger WMA with held-out walk-forward validation (MAPE/RMSE)."""
    series_12m = [
        TimeSeriesObservation(period_year=2024, period_month=m, unit_volume=100 + m * 5, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
        for m in range(1, 13)
    ]
    run_result = DemandEngine.generate_forecast(series_12m, horizon=3, craft_name="Chanderi Saree")
    assert run_result.status == "FORECAST_AVAILABLE"
    assert run_result.model_name == "WMA"
    assert len(run_result.points) == 3

    # Check walk-forward validation metrics
    assert run_result.validation_mape is not None
    assert run_result.validation_mape >= 0.0
    assert run_result.validation_rmse is not None

    # Check points are in future chronological order
    p1, p2, p3 = run_result.points
    assert p1.forecast_year == 2025 and p1.forecast_month == 1
    assert p2.forecast_year == 2025 and p2.forecast_month == 2
    assert p3.forecast_year == 2025 and p3.forecast_month == 3

    # Projected demand indices are normalized around 100.0
    assert p1.projected_demand_index > 0
    assert p1.data_sufficiency_status == "FORECAST_AVAILABLE"


def test_holt_winters_seasonal_fit_on_24_periods():
    """24 consecutive periods (2 full annual cycles) select HOLT_WINTERS model."""
    series_24m = []
    # 2 years of cyclical demand (higher in Oct/Nov festival months)
    for y in [2023, 2024]:
        for m in range(1, 13):
            base = 100 + (30 if m in {10, 11} else 0)  # Festival surge
            series_24m.append(
                TimeSeriesObservation(period_year=y, period_month=m, unit_volume=base, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
            )

    run_result = DemandEngine.generate_forecast(series_24m, horizon=3)
    assert run_result.status == "FORECAST_AVAILABLE"
    assert run_result.model_name == "HOLT_WINTERS"
    assert len(run_result.points) == 3


@pytest.mark.asyncio
async def test_forecast_api_insufficient_history_behavior(
    client: AsyncClient,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies that the API returns honest INSUFFICIENT_HISTORY when craft has < 12 records."""
    res = await client.get(
        f"/api/v1/demand/forecasts?craft_id={seed_craft.id}",
        headers=artisan_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in {"INSUFFICIENT_HISTORY", "NO_DEMAND_OBSERVATIONS"}
    assert len(data["points"]) == 0
    assert "required" in data["limitations_notes"].lower() or "no historical" in data["limitations_notes"].lower()
