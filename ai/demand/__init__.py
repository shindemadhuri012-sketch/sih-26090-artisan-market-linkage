"""
SIH 26090: AI Demand Intelligence Module
Exports classical forecasting engine, time-series data structures, and honest evaluation results.
"""

from ai.demand.engine import (
    DemandEngine,
    DEMAND_ENGINE_V1,
    TimeSeriesObservation,
    EligibilityResult,
    TrendResult,
    ForecastRunResult,
    ForecastPointOutput
)

__all__ = [
    "DemandEngine",
    "DEMAND_ENGINE_V1",
    "TimeSeriesObservation",
    "EligibilityResult",
    "TrendResult",
    "ForecastRunResult",
    "ForecastPointOutput"
]
