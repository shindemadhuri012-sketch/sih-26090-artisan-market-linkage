"""
SIH 26090: Fair-Price Intelligence Service
Orchestrates artisan cost structures, authentic market observations,
deterministic FAIR_PRICE_ENGINE_V1 execution, versioned analysis persistence,
and audited artisan price confirmations.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.product import Product, PriceAnalysis, ProductCostBreakdown
from backend.app.models.market import MarketPriceObservation
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.craft import Craft
from backend.app.schemas.pricing import (
    CostBreakdownCreate,
    MarketPriceObservationCreate,
    PriceConfirmationRequest,
    PriceAnalysisResponse
)
from backend.app.services.audit_service import record_audit_event
from ai.pricing.engine import FairPriceEngine, ENGINE_VERSION, quantize_inr


def make_json_serializable(obj: Any) -> Any:
    """Recursively converts Decimal objects to str for SQLAlchemy JSON column storage."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    return obj


async def verify_artisan_product_ownership(
    db: AsyncSession,
    product_id: str,
    user_id: str
) -> Tuple[Product, ArtisanProfile]:
    """
    Verifies that the product exists and is owned by the authenticated artisan.
    Strict server-side IDOR defense.
    """
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == user_id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an active artisan profile."
        )

    prod_res = await db.execute(select(Product).where(Product.id == product_id))
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found."
        )

    if product.artisan_id != artisan.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this product listing."
        )

    return product, artisan


async def save_or_update_cost_breakdown(
    db: AsyncSession,
    product_id: str,
    user_id: str,
    payload: CostBreakdownCreate
) -> ProductCostBreakdown:
    """
    Saves or updates an artisan's structured product cost breakdown.
    Calculates exact baselines using Decimal arithmetic and logs audit trail.
    """
    product, artisan = await verify_artisan_product_ownership(db, product_id, user_id)

    # 1. Execute deterministic cost breakdown calculation
    calc_res = FairPriceEngine.calculate_cost_breakdown(
        materials=[m.model_dump() for m in payload.materials],
        labor_calculation_method=payload.labor_calculation_method,
        labor_hours=payload.labor_hours,
        hourly_labor_rate=payload.hourly_labor_rate,
        total_labor_cost=payload.total_labor_cost,
        packaging_cost=payload.packaging_cost,
        transport_cost=payload.transport_cost,
        overhead_cost=payload.overhead_cost,
        overhead_allocation_basis=payload.overhead_allocation_basis,
        other_costs=payload.other_costs,
        batch_quantity=payload.batch_quantity,
        desired_margin_percentage=payload.desired_margin_percentage
    )

    # 2. Check if a cost breakdown already exists for this product
    cb_res = await db.execute(select(ProductCostBreakdown).where(ProductCostBreakdown.product_id == product.id))
    cost_breakdown = cb_res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not cost_breakdown:
        cost_breakdown = ProductCostBreakdown(
            product_id=product.id,
            artisan_id=artisan.id,
            materials=calc_res["processed_materials"],
            total_material_cost=calc_res["total_material_cost"],
            labor_calculation_method=calc_res["labor_calculation_method"],
            labor_hours=calc_res["labor_hours"],
            hourly_labor_rate=calc_res["hourly_labor_rate"],
            total_labor_cost=calc_res["total_labor_cost"],
            packaging_cost=calc_res["packaging_cost"],
            transport_cost=calc_res["transport_cost"],
            overhead_cost=calc_res["overhead_cost"],
            overhead_allocation_basis=calc_res["overhead_allocation_basis"],
            other_costs=calc_res["other_costs"],
            other_costs_description=payload.other_costs_description,
            batch_quantity=calc_res["batch_quantity"],
            currency=payload.currency,
            current_selling_price=payload.current_selling_price or product.price_inr,
            desired_margin_percentage=calc_res["desired_margin_percentage"],
            total_production_cost=calc_res["total_production_cost"],
            cost_baseline_unit_cost=calc_res["cost_baseline_unit_cost"],
            cost_baseline_recommended_price=calc_res["cost_baseline_recommended_price"],
            provenance_status="ARTISAN_PROVIDED",
            created_at=now,
            updated_at=now
        )
        db.add(cost_breakdown)
    else:
        cost_breakdown.materials = calc_res["processed_materials"]
        cost_breakdown.total_material_cost = calc_res["total_material_cost"]
        cost_breakdown.labor_calculation_method = calc_res["labor_calculation_method"]
        cost_breakdown.labor_hours = calc_res["labor_hours"]
        cost_breakdown.hourly_labor_rate = calc_res["hourly_labor_rate"]
        cost_breakdown.total_labor_cost = calc_res["total_labor_cost"]
        cost_breakdown.packaging_cost = calc_res["packaging_cost"]
        cost_breakdown.transport_cost = calc_res["transport_cost"]
        cost_breakdown.overhead_cost = calc_res["overhead_cost"]
        cost_breakdown.overhead_allocation_basis = calc_res["overhead_allocation_basis"]
        cost_breakdown.other_costs = calc_res["other_costs"]
        cost_breakdown.other_costs_description = payload.other_costs_description
        cost_breakdown.batch_quantity = calc_res["batch_quantity"]
        cost_breakdown.currency = payload.currency
        cost_breakdown.current_selling_price = payload.current_selling_price or product.price_inr
        cost_breakdown.desired_margin_percentage = calc_res["desired_margin_percentage"]
        cost_breakdown.total_production_cost = calc_res["total_production_cost"]
        cost_breakdown.cost_baseline_unit_cost = calc_res["cost_baseline_unit_cost"]
        cost_breakdown.cost_baseline_recommended_price = calc_res["cost_baseline_recommended_price"]
        cost_breakdown.updated_at = now

    await db.commit()
    await db.refresh(cost_breakdown)

    await record_audit_event(
        db=db,
        action="PRICING_COSTS_UPDATED",
        entity_type="ProductCostBreakdown",
        entity_id=cost_breakdown.id,
        actor_user_id=user_id,
        payload_after={
            "product_id": product.id,
            "unit_cost": str(cost_breakdown.cost_baseline_unit_cost),
            "baseline_price": str(cost_breakdown.cost_baseline_recommended_price)
        }
    )

    return cost_breakdown


async def get_cost_breakdown(
    db: AsyncSession,
    product_id: str,
    user_id: str
) -> Optional[ProductCostBreakdown]:
    """Retrieves current cost breakdown for an artisan's product."""
    product, _ = await verify_artisan_product_ownership(db, product_id, user_id)
    cb_res = await db.execute(select(ProductCostBreakdown).where(ProductCostBreakdown.product_id == product.id))
    return cb_res.scalar_one_or_none()


async def run_price_analysis(
    db: AsyncSession,
    product_id: str,
    user_id: str,
    custom_cost_input: Optional[CostBreakdownCreate] = None
) -> PriceAnalysis:
    """
    Executes FAIR_PRICE_ENGINE_V1 for the given product.
    Fetches costs, evaluates comparable market observations, derives fair price range,
    persists a versioned PriceAnalysis record, and audits the execution.
    """
    product, artisan = await verify_artisan_product_ownership(db, product_id, user_id)

    # 1. Resolve cost structure
    if custom_cost_input:
        cost_breakdown = await save_or_update_cost_breakdown(db, product_id, user_id, custom_cost_input)
    else:
        cb_res = await db.execute(select(ProductCostBreakdown).where(ProductCostBreakdown.product_id == product.id))
        cost_breakdown = cb_res.scalar_one_or_none()

    if not cost_breakdown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot analyze pricing: No cost breakdown found. Please save production costs first."
        )

    # Convert cost breakdown model to dict for engine
    cost_dict = {
        "processed_materials": cost_breakdown.materials,
        "total_material_cost": cost_breakdown.total_material_cost,
        "labor_calculation_method": cost_breakdown.labor_calculation_method,
        "labor_hours": cost_breakdown.labor_hours,
        "hourly_labor_rate": cost_breakdown.hourly_labor_rate,
        "total_labor_cost": cost_breakdown.total_labor_cost,
        "packaging_cost": cost_breakdown.packaging_cost,
        "transport_cost": cost_breakdown.transport_cost,
        "overhead_cost": cost_breakdown.overhead_cost,
        "overhead_allocation_basis": cost_breakdown.overhead_allocation_basis,
        "other_costs": cost_breakdown.other_costs,
        "batch_quantity": cost_breakdown.batch_quantity,
        "desired_margin_percentage": cost_breakdown.desired_margin_percentage,
        "total_production_cost": cost_breakdown.total_production_cost,
        "cost_baseline_unit_cost": cost_breakdown.cost_baseline_unit_cost,
        "cost_baseline_recommended_price": cost_breakdown.cost_baseline_recommended_price
    }

    # 2. Fetch comparable market observations from DB matching craft_id
    obs_res = await db.execute(
        select(MarketPriceObservation)
        .where(
            and_(
                MarketPriceObservation.craft_id == product.craft_id,
                MarketPriceObservation.currency == "INR"
            )
        )
    )
    raw_observations = obs_res.scalars().all()

    # 3. Filter and evaluate market evidence
    target_materials = [m.get("material_name", "") for m in cost_breakdown.materials] if cost_breakdown.materials else []
    if not target_materials and product.materials:
        target_materials = product.materials if isinstance(product.materials, list) else []

    valid_obs, evidence_status, market_stats = FairPriceEngine.filter_and_evaluate_market_evidence(
        observations=raw_observations,
        target_craft_id=product.craft_id,
        target_materials=target_materials
    )

    # 4. Synthesize fair price analysis
    analysis_dict = FairPriceEngine.synthesize_fair_price_analysis(
        cost_breakdown=cost_dict,
        market_stats=market_stats,
        valid_observations=valid_obs,
        artisan_current_price=cost_breakdown.current_selling_price or product.price_inr
    )

    # 5. Persist versioned PriceAnalysis (append-only for historical auditing)
    now = datetime.now(timezone.utc)
    new_analysis = PriceAnalysis(
        product_id=product.id,
        artisan_id=artisan.id,
        cost_breakdown_id=cost_breakdown.id,
        engine_version=ENGINE_VERSION,
        currency="INR",
        raw_material_cost=cost_breakdown.total_material_cost,
        labor_hours=cost_breakdown.labor_hours or Decimal("0.00"),
        skill_level_hourly_rate=cost_breakdown.hourly_labor_rate or Decimal("0.00"),
        consumables_overhead_cost=cost_breakdown.overhead_cost,
        packaging_logistics_cost=cost_breakdown.packaging_cost + cost_breakdown.transport_cost,
        calculated_total_cost=cost_breakdown.total_production_cost,
        fair_margin_percentage=cost_breakdown.desired_margin_percentage,
        recommended_floor_price=analysis_dict["floor_price"],
        recommended_fair_retail_price=analysis_dict["recommended_price"],
        fair_price_min=analysis_dict["fair_price_min"],
        fair_price_max=analysis_dict["fair_price_max"],
        fair_price_recommended=analysis_dict["recommended_price"],
        evidence_status=evidence_status,
        market_sample_size=market_stats["observation_count"],
        market_median_price=market_stats.get("median_inr"),
        market_min_price=market_stats.get("min_inr"),
        market_max_price=market_stats.get("max_inr"),
        market_iqr_low=market_stats.get("iqr_low_inr"),
        market_iqr_high=market_stats.get("iqr_high_inr"),
        market_benchmark_reference=f"Found {market_stats['observation_count']} comparable observations",
        confidence_indicator=market_stats.get("quality_rating", "USER_SELF_REPORTED"),
        input_snapshot_json=make_json_serializable(cost_dict),
        comparable_observations_json=make_json_serializable(valid_obs),
        explanation_steps=make_json_serializable(analysis_dict["explanation_steps"]),
        limitations_notes=analysis_dict["limitations_notes"],
        provenance_state="CALCULATED",
        is_confirmed_by_artisan=False,
        created_at=now,
        updated_at=now
    )

    db.add(new_analysis)
    await db.commit()
    await db.refresh(new_analysis)

    await record_audit_event(
        db=db,
        action="PRICING_ANALYSIS_GENERATED",
        entity_type="PriceAnalysis",
        entity_id=new_analysis.id,
        actor_user_id=user_id,
        payload_after={
            "product_id": product.id,
            "engine_version": ENGINE_VERSION,
            "evidence_status": evidence_status,
            "recommended_price": str(new_analysis.recommended_fair_retail_price)
        }
    )

    return new_analysis


async def get_latest_price_analysis(
    db: AsyncSession,
    product_id: str,
    user_id: str
) -> Optional[PriceAnalysis]:
    """Retrieves the latest PriceAnalysis for a product."""
    product, _ = await verify_artisan_product_ownership(db, product_id, user_id)
    stmt = (
        select(PriceAnalysis)
        .where(PriceAnalysis.product_id == product.id)
        .order_by(desc(PriceAnalysis.created_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def get_price_analysis_history(
    db: AsyncSession,
    product_id: str,
    user_id: str
) -> List[PriceAnalysis]:
    """Retrieves historical PriceAnalysis records for an artisan's product."""
    product, _ = await verify_artisan_product_ownership(db, product_id, user_id)
    stmt = (
        select(PriceAnalysis)
        .where(PriceAnalysis.product_id == product.id)
        .order_by(desc(PriceAnalysis.created_at))
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def confirm_price_analysis(
    db: AsyncSession,
    analysis_id: str,
    user_id: str,
    payload: PriceConfirmationRequest
) -> PriceAnalysis:
    """
    Artisan explicitly reviews and confirms a price analysis.
    Optionally applies the confirmed price to product.price_inr.
    Audits the confirmation event.
    """
    res = await db.execute(select(PriceAnalysis).where(PriceAnalysis.id == analysis_id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PriceAnalysis with ID '{analysis_id}' was not found."
        )

    product, _ = await verify_artisan_product_ownership(db, analysis.product_id, user_id)

    analysis.is_confirmed_by_artisan = True
    analysis.confirmed_price_inr = payload.confirmed_price_inr
    analysis.artisan_notes = payload.artisan_notes
    analysis.provenance_state = "HUMAN_CONFIRMED"
    analysis.updated_at = datetime.now(timezone.utc)

    if payload.apply_to_product:
        product.price_inr = payload.confirmed_price_inr

    await db.commit()
    await db.refresh(analysis)

    await record_audit_event(
        db=db,
        action="PRICING_ANALYSIS_CONFIRMED",
        entity_type="PriceAnalysis",
        entity_id=analysis.id,
        actor_user_id=user_id,
        payload_after={
            "product_id": product.id,
            "confirmed_price": str(payload.confirmed_price_inr),
            "applied_to_product": payload.apply_to_product
        }
    )

    return analysis


async def ingest_market_price_observation(
    db: AsyncSession,
    payload: MarketPriceObservationCreate,
    is_sample: bool = False
) -> MarketPriceObservation:
    """
    Ingests an authentic, source-backed market price observation.
    Preserves complete provenance, observation timestamp, and source metadata.
    """
    craft_res = await db.execute(select(Craft).where(Craft.id == payload.craft_id))
    if not craft_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specified craft_id '{payload.craft_id}' does not exist in master catalogue."
        )

    obs = MarketPriceObservation(
        craft_id=payload.craft_id,
        craft_category_id=payload.craft_category_id,
        product_title=payload.product_title,
        observed_price=payload.observed_price,
        currency=payload.currency,
        source_name=payload.source_name,
        source_url=payload.source_url,
        source_type=payload.source_type,
        geography_state=payload.geography_state,
        region=payload.region,
        observation_date=payload.observation_date,
        original_source_id=payload.original_source_id,
        license_or_usage_info=payload.license_or_usage_info,
        attributes_json=payload.attributes_json,
        comparability_tags=payload.comparability_tags,
        evidence_quality_status=payload.evidence_quality_status,
        verification_status=payload.verification_status,
        data_source_id=payload.data_source_id,
        data_provenance_level="SOURCE_BACKED",
        is_sample_or_demo=is_sample or payload.is_sample_or_demo,
        ingestion_batch_id=payload.ingestion_batch_id,
        created_at=datetime.now(timezone.utc)
    )

    db.add(obs)
    await db.commit()
    await db.refresh(obs)
    return obs


async def list_market_price_observations(
    db: AsyncSession,
    craft_id: Optional[str] = None,
    state: Optional[str] = None,
    quality: Optional[str] = None,
    limit: int = 50
) -> List[MarketPriceObservation]:
    """Lists market price observations with optional filtering."""
    query = select(MarketPriceObservation)
    filters = []
    if craft_id:
        filters.append(MarketPriceObservation.craft_id == craft_id)
    if state:
        filters.append(MarketPriceObservation.geography_state == state)
    if quality:
        filters.append(MarketPriceObservation.evidence_quality_status == quality)

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(desc(MarketPriceObservation.observation_date)).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


def format_analysis_response(analysis: PriceAnalysis) -> PriceAnalysisResponse:
    """Helper to convert a PriceAnalysis ORM model into PriceAnalysisResponse."""
    return PriceAnalysisResponse(
        id=analysis.id,
        product_id=analysis.product_id,
        artisan_id=analysis.artisan_id,
        cost_breakdown_id=analysis.cost_breakdown_id,
        engine_version=analysis.engine_version,
        currency=analysis.currency,
        evidence_status=analysis.evidence_status,
        cost_baseline={
            "total_material_cost": analysis.raw_material_cost,
            "total_labor_cost": quantize_inr(analysis.labor_hours * analysis.skill_level_hourly_rate) if analysis.labor_hours and analysis.skill_level_hourly_rate else Decimal("0.00"),
            "packaging_logistics_cost": analysis.packaging_logistics_cost,
            "overhead_cost": analysis.consumables_overhead_cost,
            "total_production_cost": analysis.calculated_total_cost,
            "unit_production_cost": analysis.recommended_floor_price,
            "desired_margin_percentage": analysis.fair_margin_percentage,
            "cost_baseline_price": analysis.recommended_fair_retail_price,
            "currency": analysis.currency
        },
        market_evidence={
            "status": analysis.evidence_status,
            "observation_count": analysis.market_sample_size,
            "median_inr": analysis.market_median_price,
            "min_inr": analysis.market_min_price,
            "max_inr": analysis.market_max_price,
            "iqr_low_inr": analysis.market_iqr_low,
            "iqr_high_inr": analysis.market_iqr_high,
            "quality_rating": analysis.confidence_indicator,
            "benchmark_reference": analysis.market_benchmark_reference
        },
        fair_price_analysis={
            "status": analysis.evidence_status,
            "floor_price": analysis.recommended_floor_price,
            "recommended_price": analysis.fair_price_recommended or analysis.recommended_fair_retail_price,
            "price_range_min": analysis.fair_price_min,
            "price_range_max": analysis.fair_price_max
        },
        explanation_steps=analysis.explanation_steps if isinstance(analysis.explanation_steps, list) else [],
        limitations_notes=analysis.limitations_notes if isinstance(analysis.limitations_notes, list) else [],
        provenance_state=analysis.provenance_state,
        is_confirmed_by_artisan=analysis.is_confirmed_by_artisan,
        confirmed_price_inr=analysis.confirmed_price_inr,
        artisan_notes=analysis.artisan_notes,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at
    )
