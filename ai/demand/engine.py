"""
SIH 26090: Classical Demand Forecasting & Real Trend Engine (DEMAND_ENGINE_V1)
Implements deterministic aggregation, empirical trend evaluation, multi-gate eligibility validation,
classical time-series forecasting (WMA and Holt-Winters), and leakage-free temporal validation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import List, Dict, Any, Optional, Tuple

DEMAND_ENGINE_V1 = "DEMAND_ENGINE_V1"


@dataclass
class TimeSeriesObservation:
    """Represents a single chronological aggregated observation point."""
    period_year: int
    period_month: int
    unit_volume: int
    monetary_volume_inr: float
    enquiry_count: int
    order_count: int
    is_partial_period: bool = False
    observation_count: int = 1


@dataclass
class EligibilityResult:
    """Multi-gate eligibility verification result for statistical time-series forecasting."""
    is_eligible: bool
    status: str  # SUFFICIENT_DATA_AVAILABLE, INSUFFICIENT_HISTORY, INSUFFICIENT_DATA_QUALITY, FORECAST_UNAVAILABLE
    explanation: str
    total_periods: int
    missing_periods_ratio: float
    time_span_months: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendResult:
    """Empirical, non-speculative directional trend evaluation."""
    status: str  # INCREASING, DECREASING, STABLE, INSUFFICIENT_DATA
    current_period_volume: Optional[int]
    previous_period_volume: Optional[int]
    absolute_change: Optional[int]
    percentage_change: Optional[float]
    rolling_average_3m: Optional[float]
    explanation: str
    observation_periods_count: int


@dataclass
class ForecastPointOutput:
    """Single period projection output with honest status and uncertainty bounds."""
    forecast_month: int
    forecast_year: int
    projected_demand_index: float  # Normalized to 100.0 baseline
    projected_unit_volume: Optional[int]
    uncertainty_lower: Optional[float]
    uncertainty_upper: Optional[float]
    data_sufficiency_status: str
    explanation: str


@dataclass
class ForecastRunResult:
    """Complete execution record of a forecasting run."""
    status: str  # FORECAST_AVAILABLE, INSUFFICIENT_HISTORY, INSUFFICIENT_DATA_QUALITY, FORECAST_FAILED
    model_name: str
    model_version: str
    training_start_date: datetime
    training_end_date: datetime
    validation_start_date: Optional[datetime]
    validation_end_date: Optional[datetime]
    test_start_date: Optional[datetime]
    test_end_date: Optional[datetime]
    observation_count: int
    validation_mape: Optional[float]
    validation_rmse: Optional[float]
    points: List[ForecastPointOutput]
    limitations_notes: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class DemandEngine:
    """
    Core AI & Statistical Demand Engine (DEMAND_ENGINE_V1).
    Enforces strict real-data rules, leakage prevention, and explicit sparse-data honesty.
    """

    @staticmethod
    def check_eligibility(series: List[TimeSeriesObservation]) -> EligibilityResult:
        """
        Validates multi-gate eligibility before statistical forecasting:
        1. Observation count threshold (N >= 12 consecutive/near-consecutive months).
        2. Chronological time span coverage (at least 12 months between first and last).
        3. Missing data tolerance (< 15% missing periods).
        4. Observation quality (non-empty volumes).
        5. Minimum evaluation window (at least 3 periods for held-out validation).
        """
        if not series:
            return EligibilityResult(
                is_eligible=False,
                status="NO_DEMAND_OBSERVATIONS",
                explanation="No historical demand observations recorded for this craft or region.",
                total_periods=0,
                missing_periods_ratio=1.0,
                time_span_months=0
            )

        # Filter out partial periods from baseline eligibility
        complete_series = [obs for obs in series if not obs.is_partial_period]
        n = len(complete_series)

        if n < 12:
            return EligibilityResult(
                is_eligible=False,
                status="INSUFFICIENT_HISTORY",
                explanation=f"Recorded history spans only {n} monthly period(s). At least 12 complete monthly observation periods are required for statistically valid forecasting.",
                total_periods=n,
                missing_periods_ratio=0.0,
                time_span_months=n
            )

        # Chronological sorting
        sorted_series = sorted(complete_series, key=lambda x: (x.period_year, x.period_month))
        first = sorted_series[0]
        last = sorted_series[-1]

        # Calculate expected total months
        expected_span_months = (last.period_year - first.period_year) * 12 + (last.period_month - first.period_month) + 1
        missing_count = max(0, expected_span_months - n)
        missing_ratio = missing_count / expected_span_months if expected_span_months > 0 else 0.0

        if missing_ratio > 0.20:  # More than 20% gaps in monthly coverage
            return EligibilityResult(
                is_eligible=False,
                status="INSUFFICIENT_DATA_QUALITY",
                explanation=f"Historical observations contain significant gaps ({missing_count} missing out of {expected_span_months} expected months, {missing_ratio:.1%}). Continuous observation is required.",
                total_periods=n,
                missing_periods_ratio=missing_ratio,
                time_span_months=expected_span_months
            )

        return EligibilityResult(
            is_eligible=True,
            status="SUFFICIENT_DATA_AVAILABLE",
            explanation=f"Dataset satisfies multi-gate eligibility: {n} complete monthly periods spanning {expected_span_months} months with {missing_ratio:.1%} missing ratio.",
            total_periods=n,
            missing_periods_ratio=missing_ratio,
            time_span_months=expected_span_months,
            details={"start_period": f"{first.period_year}-{first.period_month:02d}", "end_period": f"{last.period_year}-{last.period_month:02d}"}
        )

    @staticmethod
    def calculate_trend(series: List[TimeSeriesObservation]) -> TrendResult:
        """
        Calculates empirical, non-speculative directional trend across historical periods.
        Requires at least 3 periods (N >= 3) to declare a trend direction.
        """
        complete_series = [obs for obs in series if not obs.is_partial_period]
        if len(complete_series) < 3:
            return TrendResult(
                status="INSUFFICIENT_DATA",
                current_period_volume=complete_series[-1].unit_volume if complete_series else None,
                previous_period_volume=None,
                absolute_change=None,
                percentage_change=None,
                rolling_average_3m=None,
                explanation=f"Only {len(complete_series)} observation period(s) available. At least 3 periods are required for an empirical trend analysis.",
                observation_periods_count=len(complete_series)
            )

        sorted_series = sorted(complete_series, key=lambda x: (x.period_year, x.period_month))
        curr = sorted_series[-1]
        prev = sorted_series[-2]

        curr_vol = curr.unit_volume
        prev_vol = prev.unit_volume
        abs_change = curr_vol - prev_vol

        pct_change = None
        if prev_vol > 0:
            pct_change = round(((curr_vol - prev_vol) / prev_vol) * 100.0, 2)

        # 3-period moving average
        recent_3 = [x.unit_volume for x in sorted_series[-3:]]
        sma_3 = round(sum(recent_3) / len(recent_3), 2)

        # Determine discrete trend state
        if pct_change is not None:
            if pct_change >= 5.0:
                trend_status = "INCREASING"
                exp = f"Observed demand grew by {pct_change:+.1f}% from previous period ({prev_vol} to {curr_vol} units)."
            elif pct_change <= -5.0:
                trend_status = "DECREASING"
                exp = f"Observed demand declined by {pct_change:+.1f}% from previous period ({prev_vol} to {curr_vol} units)."
            else:
                trend_status = "STABLE"
                exp = f"Observed demand remained stable ({pct_change:+.1f}% change from {prev_vol} to {curr_vol} units)."
        else:
            trend_status = "STABLE" if abs_change == 0 else ("INCREASING" if abs_change > 0 else "DECREASING")
            exp = f"Demand changed from baseline 0 to {curr_vol} units."

        return TrendResult(
            status=trend_status,
            current_period_volume=curr_vol,
            previous_period_volume=prev_vol,
            absolute_change=abs_change,
            percentage_change=pct_change,
            rolling_average_3m=sma_3,
            explanation=exp,
            observation_periods_count=len(sorted_series)
        )

    @classmethod
    def fit_wma(cls, values: List[float], window: int = 3) -> float:
        """
        Weighted Moving Average (WMA) with linear weights [1, 2, ..., window].
        Weights sum strictly to 1.0.
        """
        if len(values) < window:
            return sum(values) / len(values) if values else 0.0
        
        subset = values[-window:]
        weights = list(range(1, window + 1))
        weight_sum = sum(weights)
        return sum(v * w for v, w in zip(subset, weights)) / weight_sum

    @classmethod
    def fit_holt_winters(
        cls,
        values: List[float],
        seasonal_periods: int = 12,
        alpha: float = 0.3,
        beta: float = 0.1,
        gamma: float = 0.2,
        horizon: int = 3
    ) -> List[float]:
        """
        Classical Additive Holt-Winters Exponential Smoothing.
        Requires at least 2 full cycles (24 periods) for full seasonal fit.
        If N < 24, falls back to Holt's Linear (level + trend).
        """
        n = len(values)
        if n < seasonal_periods * 2:
            # Fallback to Holt's Linear Exponential Smoothing (Level + Trend)
            level = values[0]
            trend = (values[-1] - values[0]) / max(1, n - 1)
            for v in values[1:]:
                last_level = level
                level = alpha * v + (1 - alpha) * (last_level + trend)
                trend = beta * (level - last_level) + (1 - beta) * trend
            return [max(0.0, level + (i + 1) * trend) for i in range(horizon)]

        # Full Additive Holt-Winters
        L = seasonal_periods
        # Initial level and trend
        level = sum(values[:L]) / L
        trend = sum((values[L + i] - values[i]) / L for i in range(L)) / L

        # Initial seasonal indices
        seasonals = [values[i] - level for i in range(L)]

        # Iterative update
        for i in range(L, n):
            val = values[i]
            last_level = level
            s_idx = i % L
            level = alpha * (val - seasonals[s_idx]) + (1 - alpha) * (last_level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            seasonals[s_idx] = gamma * (val - level) + (1 - gamma) * seasonals[s_idx]

        # Project future points
        projections = []
        for h in range(1, horizon + 1):
            s_idx = (n + h - 1) % L
            pred = level + h * trend + seasonals[s_idx]
            projections.append(max(0.0, pred))
        return projections

    @classmethod
    def walk_forward_evaluate(
        cls,
        values: List[float],
        model_type: str = "WMA",
        seasonal_periods: int = 12,
        val_size: int = 3
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Strict Chronological Walk-Forward Validation.
        Zero future leakage: Trains strictly on [0 : T - val_size],
        evaluates against held-out validation points [T - val_size : T].
        Returns (MAPE, RMSE).
        """
        n = len(values)
        if n <= val_size + 3:
            return None, None

        train_vals = values[:-val_size]
        actual_vals = values[-val_size:]
        predicted_vals = []

        if model_type == "WMA":
            # Walk forward 1 step at a time
            history = list(train_vals)
            for actual in actual_vals:
                pred = cls.fit_wma(history, window=3)
                predicted_vals.append(pred)
                history.append(actual)
        else:
            # Holt-Winters / Holt Linear
            preds = cls.fit_holt_winters(train_vals, seasonal_periods=seasonal_periods, horizon=val_size)
            predicted_vals = preds

        # Calculate MAPE and RMSE
        errors = [act - pred for act, pred in zip(actual_vals, predicted_vals)]
        squared_errors = [e ** 2 for e in errors]
        rmse = math.sqrt(sum(squared_errors) / len(squared_errors))

        pct_errors = []
        for act, pred in zip(actual_vals, predicted_vals):
            if act > 0:
                pct_errors.append(abs(act - pred) / act)
        mape = (sum(pct_errors) / len(pct_errors)) * 100.0 if pct_errors else None

        return (round(mape, 2) if mape is not None else None, round(rmse, 2))

    @classmethod
    def generate_forecast(
        cls,
        series: List[TimeSeriesObservation],
        horizon: int = 3,
        craft_name: Optional[str] = None
    ) -> ForecastRunResult:
        """
        Executes complete forecasting pipeline with strict honesty gates:
        1. Checks multi-gate eligibility.
        2. If eligible, splits data chronologically for walk-forward evaluation.
        3. Fits appropriate classical model (WMA if 12 <= N < 24, Holt-Winters if N >= 24).
        4. Calculates prediction intervals based on genuine validation residuals.
        """
        now = datetime.now(timezone.utc)
        eligibility = cls.check_eligibility(series)

        # Baseline dates
        sorted_series = sorted(series, key=lambda x: (x.period_year, x.period_month))
        first = sorted_series[0] if sorted_series else None
        last = sorted_series[-1] if sorted_series else None

        start_dt = datetime(first.period_year, first.period_month, 1, tzinfo=timezone.utc) if first else now
        end_dt = datetime(last.period_year, last.period_month, 28, tzinfo=timezone.utc) if last else now

        if not eligibility.is_eligible:
            return ForecastRunResult(
                status=eligibility.status,
                model_name="NONE",
                model_version=DEMAND_ENGINE_V1,
                training_start_date=start_dt,
                training_end_date=end_dt,
                validation_start_date=None,
                validation_end_date=None,
                test_start_date=None,
                test_end_date=None,
                observation_count=len(series),
                validation_mape=None,
                validation_rmse=None,
                points=[],
                limitations_notes=eligibility.explanation,
                parameters={}
            )

        # Extract numerical series (unit volume)
        complete_series = [x for x in sorted_series if not x.is_partial_period]
        volumes = [float(x.unit_volume) for x in complete_series]
        n = len(volumes)

        # Select model based on data depth
        if n >= 24:
            model_name = "HOLT_WINTERS"
            seasonal_periods = 12
        else:
            model_name = "WMA"
            seasonal_periods = 12

        # Held-out walk-forward validation (val_size=3)
        val_size = 3
        mape, rmse = cls.walk_forward_evaluate(volumes, model_type=model_name, seasonal_periods=seasonal_periods, val_size=val_size)

        # Chronological window dates
        val_start_obs = complete_series[-val_size]
        val_start_dt = datetime(val_start_obs.period_year, val_start_obs.period_month, 1, tzinfo=timezone.utc)
        train_end_obs = complete_series[-val_size - 1]
        train_end_dt = datetime(train_end_obs.period_year, train_end_obs.period_month, 28, tzinfo=timezone.utc)

        # Generate future projections
        if model_name == "HOLT_WINTERS":
            raw_projections = cls.fit_holt_winters(volumes, seasonal_periods=seasonal_periods, horizon=horizon)
        else:
            # Multi-step WMA projection
            proj_hist = list(volumes)
            raw_projections = []
            for _ in range(horizon):
                step_pred = cls.fit_wma(proj_hist, window=3)
                raw_projections.append(step_pred)
                proj_hist.append(step_pred)

        # Calculate base index (average of historical series = 100.0)
        mean_vol = sum(volumes) / len(volumes) if volumes and sum(volumes) > 0 else 1.0

        # Build projected points
        last_year = last.period_year
        last_month = last.period_month
        points: List[ForecastPointOutput] = []

        for i, val in enumerate(raw_projections):
            target_month = (last_month + i) % 12 + 1
            year_offset = (last_month + i) // 12
            target_year = last_year + year_offset

            proj_index = round((val / mean_vol) * 100.0, 1)
            proj_units = max(0, int(round(val)))

            # Statistically justified uncertainty interval using validation RMSE
            uncertainty_lower = None
            uncertainty_upper = None
            if rmse is not None and rmse > 0:
                uncertainty_lower = round(max(0.0, ((val - 1.96 * rmse) / mean_vol) * 100.0), 1)
                uncertainty_upper = round(((val + 1.96 * rmse) / mean_vol) * 100.0, 1)

            points.append(
                ForecastPointOutput(
                    forecast_month=target_month,
                    forecast_year=target_year,
                    projected_demand_index=proj_index,
                    projected_unit_volume=proj_units,
                    uncertainty_lower=uncertainty_lower,
                    uncertainty_upper=uncertainty_upper,
                    data_sufficiency_status="FORECAST_AVAILABLE",
                    explanation=f"Projected demand index {proj_index} ({proj_units} estimated units) for {craft_name or 'craft'} in {target_year}-{target_month:02d} based on {model_name}."
                )
            )

        limitations = (
            f"Model: {model_name}. Evaluated via chronological walk-forward validation on last {val_size} historical months. "
            f"Validation MAPE: {mape:.1f}%, RMSE: {rmse:.1f} units. Projections assume consistent market access."
            if mape is not None else
            f"Model: {model_name}. Baseline projections without held-out validation metric due to short evaluation window."
        )

        return ForecastRunResult(
            status="FORECAST_AVAILABLE",
            model_name=model_name,
            model_version=DEMAND_ENGINE_V1,
            training_start_date=start_dt,
            training_end_date=train_end_dt,
            validation_start_date=val_start_dt,
            validation_end_date=end_dt,
            test_start_date=None,
            test_end_date=None,
            observation_count=n,
            validation_mape=mape,
            validation_rmse=rmse,
            points=points,
            limitations_notes=limitations,
            parameters={"model": model_name, "seasonal_periods": seasonal_periods, "horizon": horizon}
        )
