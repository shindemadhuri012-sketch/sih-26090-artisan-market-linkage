"""
SIH 26090: Demand Intelligence Service
Orchestrates observation ingestion, deterministic aggregation rollups,
empirical trend calculation, and run-point forecast persistence.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.market import DemandObservation, DemandForecast
from backend.app.models.forecast import DemandForecastRun, DemandForecastPoint
from backend.app.models.craft import Craft, CraftCategory
from backend.app.schemas.demand import (
    DemandObservationCreate,
    DemandSummaryResponse,
    DemandTrendResponse,
    DemandForecastResponse,
    ForecastPointResponse
)
from backend.app.services.audit_service import record_audit_event
from ai.demand.engine import DemandEngine, TimeSeriesObservation, DEMAND_ENGINE_V1


class DemandService:
    """Business logic and database persistence for Demand Intelligence."""

    @staticmethod
    async def create_observation(
        db: AsyncSession,
        payload: DemandObservationCreate,
        actor_id: str
    ) -> DemandObservation:
        """Records a new verified demand observation."""
        obs = DemandObservation(
            craft_id=payload.craft_id,
            craft_category_id=payload.craft_category_id,
            geography_state=payload.geography_state.strip(),
            observation_period_start=payload.observation_period_start,
            observation_period_end=payload.observation_period_end,
            total_enquiries=payload.total_enquiries,
            fulfilled_orders=payload.fulfilled_orders,
            unit_volume=payload.unit_volume,
            monetary_volume_inr=payload.monetary_volume_inr,
            average_realized_price=payload.average_realized_price,
            seasonal_festival_tag=payload.seasonal_festival_tag,
            signal_tier=payload.signal_tier,
            observation_type=payload.observation_type,
            data_quality_status=payload.data_quality_status,
            data_source_id=payload.data_source_id,
            ingestion_batch_id=payload.ingestion_batch_id,
            is_sample_or_demo=payload.is_sample_or_demo,
            data_provenance_level="VERIFIED_EXTERNAL_SOURCE" if not payload.is_sample_or_demo else "SAMPLE_RECORD"
        )
        db.add(obs)
        await db.flush()

        await record_audit_event(
            db=db,
            actor_user_id=actor_id,
            action="DEMAND_OBSERVATION_RECORDED",
            entity_type="DemandObservation",
            entity_id=obs.id,
            payload_after={
                "craft_id": obs.craft_id,
                "state": obs.geography_state,
                "unit_volume": obs.unit_volume,
                "signal_tier": obs.signal_tier
            }
        )
        return obs

    @staticmethod
    async def get_demand_summary(
        db: AsyncSession,
        craft_id: Optional[str] = None,
        category_id: Optional[str] = None,
        state: Optional[str] = None
    ) -> DemandSummaryResponse:
        """Calculates deterministic aggregated demand summary across real observations."""
        query = select(DemandObservation).where(DemandObservation.is_sample_or_demo == False)

        craft_name = None
        if craft_id:
            query = query.where(DemandObservation.craft_id == craft_id)
            c_res = await db.execute(select(Craft).where(Craft.id == craft_id))
            craft = c_res.scalar_one_or_none()
            if craft:
                craft_name = craft.name
        if category_id:
            query = query.where(DemandObservation.craft_category_id == category_id)
        if state:
            query = query.where(DemandObservation.geography_state.ilike(state.strip()))

        res = await db.execute(query)
        observations = res.scalars().all()

        if not observations:
            return DemandSummaryResponse(
                craft_id=craft_id,
                craft_category_id=category_id,
                craft_name=craft_name,
                geography_state=state,
                total_observations=0,
                total_unit_volume=0,
                total_monetary_volume_inr=Decimal("0.00"),
                total_enquiries=0,
                total_fulfilled_orders=0,
                period_start=None,
                period_end=None,
                data_sufficiency_state="NO_OBSERVATIONS"
            )

        total_units = sum(o.unit_volume for o in observations)
        total_money = sum(o.monetary_volume_inr or Decimal("0.00") for o in observations)
        total_enq = sum(o.total_enquiries for o in observations)
        total_ord = sum(o.fulfilled_orders for o in observations)

        min_date = min(o.observation_period_start for o in observations)
        max_date = max(o.observation_period_end for o in observations)

        sufficiency = "COMPLETE" if len(observations) >= 12 else ("PARTIAL_HISTORY" if len(observations) >= 3 else "INSUFFICIENT_DATA")

        return DemandSummaryResponse(
            craft_id=craft_id,
            craft_category_id=category_id,
            craft_name=craft_name,
            geography_state=state,
            total_observations=len(observations),
            total_unit_volume=total_units,
            total_monetary_volume_inr=Decimal(str(total_money)),
            total_enquiries=total_enq,
            total_fulfilled_orders=total_ord,
            period_start=min_date.isoformat(),
            period_end=max_date.isoformat(),
            data_sufficiency_state=sufficiency
        )

    @staticmethod
    async def get_demand_trends(
        db: AsyncSession,
        craft_id: Optional[str] = None,
        state: Optional[str] = None
    ) -> DemandTrendResponse:
        """Evaluates empirical directional trend across monthly observation buckets."""
        series = await db_helper_get_time_series(db, craft_id=craft_id, state=state)
        trend = DemandEngine.calculate_trend(series)

        craft_name = None
        if craft_id:
            c_res = await db.execute(select(Craft).where(Craft.id == craft_id))
            craft = c_res.scalar_one_or_none()
            if craft:
                craft_name = craft.name

        return DemandTrendResponse(
            craft_id=craft_id,
            craft_name=craft_name,
            geography_state=state,
            trend_status=trend.status,
            current_period_volume=trend.current_period_volume,
            previous_period_volume=trend.previous_period_volume,
            absolute_change=trend.absolute_change,
            percentage_change=trend.percentage_change,
            rolling_average_3m=trend.rolling_average_3m,
            explanation=trend.explanation,
            observation_periods_count=trend.observation_periods_count
        )

    @classmethod
    async def get_or_run_forecast(
        cls,
        db: AsyncSession,
        craft_id: Optional[str] = None,
        state: Optional[str] = None,
        force_recompute: bool = False
    ) -> DemandForecastResponse:
        """
        Retrieves existing forecast or executes classical time-series forecast run
        with strict multi-gate eligibility and honest limitation state.
        """
        craft_name = None
        if craft_id:
            c_res = await db.execute(select(Craft).where(Craft.id == craft_id))
            craft = c_res.scalar_one_or_none()
            if craft:
                craft_name = craft.name

        # Check latest completed run if not force_recompute
        if not force_recompute and craft_id:
            latest_run_query = (
                select(DemandForecastRun)
                .options(selectinload(DemandForecastRun.points))
                .where(DemandForecastRun.craft_id == craft_id)
                .order_by(DemandForecastRun.created_at.desc())
            )
            run_res = await db.execute(latest_run_query)
            existing_run = run_res.scalars().first()
            if existing_run:
                return DemandForecastResponse(
                    run_id=existing_run.id,
                    craft_id=existing_run.craft_id,
                    craft_name=craft_name,
                    geography_state=existing_run.geography_state,
                    status=existing_run.status,
                    model_name=existing_run.model_name,
                    model_version=existing_run.model_version,
                    training_start_date=existing_run.training_start_date.isoformat(),
                    training_end_date=existing_run.training_end_date.isoformat(),
                    observation_count=existing_run.observation_count,
                    validation_mape=existing_run.validation_mape,
                    validation_rmse=existing_run.validation_rmse,
                    points=[
                        ForecastPointResponse(
                            forecast_month=p.forecast_period_month,
                            forecast_year=p.forecast_period_year,
                            projected_demand_index=p.projected_demand_index,
                            projected_unit_volume=p.projected_unit_volume,
                            uncertainty_lower=p.uncertainty_lower,
                            uncertainty_upper=p.uncertainty_upper,
                            data_sufficiency_status=p.data_sufficiency_status,
                            explanation_note=p.explanation_note
                        )
                        for p in existing_run.points
                    ],
                    limitations_notes=existing_run.limitations_notes or ""
                )

        # Run fresh forecast
        series = await db_helper_get_time_series(db, craft_id=craft_id, state=state)
        result = DemandEngine.generate_forecast(series, horizon=3, craft_name=craft_name)

        # Persist run and points
        run = DemandForecastRun(
            craft_id=craft_id,
            geography_state=state,
            model_name=result.model_name,
            model_version=result.model_version,
            training_start_date=result.training_start_date,
            training_end_date=result.training_end_date,
            validation_start_date=result.validation_start_date,
            validation_end_date=result.validation_end_date,
            test_start_date=result.test_start_date,
            test_end_date=result.test_end_date,
            observation_count=result.observation_count,
            validation_mape=result.validation_mape,
            validation_rmse=result.validation_rmse,
            status=result.status,
            limitations_notes=result.limitations_notes,
            parameters_json=result.parameters
        )
        db.add(run)
        await db.flush()

        for pt in result.points:
            point_entity = DemandForecastPoint(
                run_id=run.id,
                forecast_period_month=pt.forecast_month,
                forecast_period_year=pt.forecast_year,
                projected_demand_index=pt.projected_demand_index,
                projected_unit_volume=pt.projected_unit_volume,
                uncertainty_lower=pt.uncertainty_lower,
                uncertainty_upper=pt.uncertainty_upper,
                data_sufficiency_status=pt.data_sufficiency_status,
                explanation_note=pt.explanation
            )
            db.add(point_entity)

        await db.flush()

        return DemandForecastResponse(
            run_id=run.id,
            craft_id=craft_id,
            craft_name=craft_name,
            geography_state=state,
            status=result.status,
            model_name=result.model_name,
            model_version=result.model_version,
            training_start_date=result.training_start_date.isoformat(),
            training_end_date=result.training_end_date.isoformat(),
            observation_count=result.observation_count,
            validation_mape=result.validation_mape,
            validation_rmse=result.validation_rmse,
            points=[
                ForecastPointResponse(
                    forecast_month=p.forecast_month,
                    forecast_year=p.forecast_year,
                    projected_demand_index=p.projected_demand_index,
                    projected_unit_volume=p.projected_unit_volume,
                    uncertainty_lower=p.uncertainty_lower,
                    uncertainty_upper=p.uncertainty_upper,
                    data_sufficiency_status=p.data_sufficiency_status,
                    explanation_note=p.explanation
                )
                for p in result.points
            ],
            limitations_notes=result.limitations_notes
        )


async def db_helper_get_time_series(
    db: AsyncSession,
    craft_id: Optional[str] = None,
    state: Optional[str] = None
) -> List[TimeSeriesObservation]:
    """Helper aggregating observations into monthly time-series buckets."""
    query = select(DemandObservation).where(DemandObservation.is_sample_or_demo == False)
    if craft_id:
        query = query.where(DemandObservation.craft_id == craft_id)
    if state:
        query = query.where(DemandObservation.geography_state.ilike(state.strip()))

    query = query.order_by(DemandObservation.observation_period_start.asc())
    res = await db.execute(query)
    observations = res.scalars().all()

    if not observations:
        return []

    # Bucket by (year, month)
    buckets: Dict[Tuple[int, int], Dict[str, Any]] = {}
    now = datetime.now(timezone.utc)

    for o in observations:
        dt = o.observation_period_start
        key = (dt.year, dt.month)
        if key not in buckets:
            buckets[key] = {
                "unit_volume": 0,
                "monetary_volume": 0.0,
                "enquiries": 0,
                "orders": 0,
                "count": 0,
                "is_partial": (dt.year == now.year and dt.month == now.month)
            }
        buckets[key]["unit_volume"] += o.unit_volume
        buckets[key]["monetary_volume"] += float(o.monetary_volume_inr or 0.0)
        buckets[key]["enquiries"] += o.total_enquiries
        buckets[key]["orders"] += o.fulfilled_orders
        buckets[key]["count"] += 1

    series: List[TimeSeriesObservation] = []
    for (year, month), val in sorted(buckets.items()):
        series.append(
            TimeSeriesObservation(
                period_year=year,
                period_month=month,
                unit_volume=val["unit_volume"],
                monetary_volume_inr=val["monetary_volume"],
                enquiry_count=val["enquiries"],
                order_count=val["orders"],
                is_partial_period=val["is_partial"],
                observation_count=val["count"]
            )
        )
    return series
