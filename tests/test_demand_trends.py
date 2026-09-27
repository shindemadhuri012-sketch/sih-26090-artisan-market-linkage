"""
SIH 26090: Demand Trends Unit Tests
Verifies empirical percentage change calculation, 3-month moving average,
trend states (INCREASING, DECREASING, STABLE, INSUFFICIENT_DATA), and neutral language.
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient

from backend.app.models.craft import Craft
from ai.demand.engine import DemandEngine, TimeSeriesObservation


def test_trend_requires_at_least_three_periods():
    """Fewer than 3 observation periods must return INSUFFICIENT_DATA."""
    obs_list = [
        TimeSeriesObservation(period_year=2025, period_month=1, unit_volume=100, monetary_volume_inr=10000.0, enquiry_count=5, order_count=2),
        TimeSeriesObservation(period_year=2025, period_month=2, unit_volume=120, monetary_volume_inr=12000.0, enquiry_count=6, order_count=3)
    ]
    trend = DemandEngine.calculate_trend(obs_list)
    assert trend.status == "INSUFFICIENT_DATA"
    assert trend.percentage_change is None
    assert "At least 3 periods are required" in trend.explanation


def test_trend_increasing_decreasing_and_stable():
    """Verifies deterministic classification into INCREASING, DECREASING, and STABLE."""
    # 1. Increasing trend (+20%)
    inc_series = [
        TimeSeriesObservation(period_year=2025, period_month=1, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=2, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=3, unit_volume=120, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
    ]
    t_inc = DemandEngine.calculate_trend(inc_series)
    assert t_inc.status == "INCREASING"
    assert t_inc.percentage_change == 20.0
    assert t_inc.rolling_average_3m == round((100 + 100 + 120) / 3, 2)

    # 2. Decreasing trend (-15%)
    dec_series = [
        TimeSeriesObservation(period_year=2025, period_month=1, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=2, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=3, unit_volume=85, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
    ]
    t_dec = DemandEngine.calculate_trend(dec_series)
    assert t_dec.status == "DECREASING"
    assert t_dec.percentage_change == -15.0

    # 3. Stable trend (+2%)
    stable_series = [
        TimeSeriesObservation(period_year=2025, period_month=1, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=2, unit_volume=100, monetary_volume_inr=0.0, enquiry_count=0, order_count=0),
        TimeSeriesObservation(period_year=2025, period_month=3, unit_volume=102, monetary_volume_inr=0.0, enquiry_count=0, order_count=0)
    ]
    t_stable = DemandEngine.calculate_trend(stable_series)
    assert t_stable.status == "STABLE"
    assert t_stable.percentage_change == 2.0


@pytest.mark.asyncio
async def test_demand_trends_api_endpoint(
    client: AsyncClient,
    admin_headers: dict,
    artisan_headers: dict,
    seed_craft: Craft
):
    """Verifies GET /api/v1/demand/trends integration with database observations."""
    now = datetime.now(timezone.utc)

    # Ingest 3 consecutive historical monthly records
    for i, vol in enumerate([100, 110, 130]):
        # e.g., 90 days ago, 60 days ago, 30 days ago
        days_ago = (3 - i) * 30
        p = {
            "craft_id": seed_craft.id,
            "geography_state": "Madhya Pradesh",
            "observation_period_start": (now - timedelta(days=days_ago)).isoformat(),
            "observation_period_end": (now - timedelta(days=days_ago - 28)).isoformat(),
            "unit_volume": vol,
            "is_sample_or_demo": False
        }
        await client.post("/api/v1/demand/observations", json=p, headers=admin_headers)

    res = await client.get(
        f"/api/v1/demand/trends?craft_id={seed_craft.id}&geography_state=Madhya Pradesh",
        headers=artisan_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["craft_id"] == seed_craft.id
    assert data["trend_status"] in {"INCREASING", "STABLE"}
    assert data["observation_periods_count"] >= 3
    assert data["explanation"] != ""
