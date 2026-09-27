"""
SIH 26090: Fair-Price Intelligence Engine (FAIR_PRICE_ENGINE_V1)
Transparent, deterministic, and evidence-based pricing engine.
Enforces strict Python Decimal arithmetic, strict no-fabrication policy,
minimum sample size thresholds (N >= 3), comparability validation,
and traceable mathematical explanations.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple


ENGINE_VERSION = "FAIR_PRICE_ENGINE_V1"
MIN_OBSERVATION_THRESHOLD = 3
TWO_PLACES = Decimal("0.01")


def quantize_inr(val: Optional[Decimal]) -> Optional[Decimal]:
    """Helper to round Decimal values to 2 decimal places using standard ROUND_HALF_UP."""
    if val is None:
        return None
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class FairPriceEngine:
    """
    Deterministic pricing engine implementing FAIR_PRICE_ENGINE_V1.
    Calculates cost baselines, evaluates market evidence, derives fair price ranges,
    and constructs step-by-step traceable explanations.
    """

    @classmethod
    def calculate_cost_breakdown(
        cls,
        materials: List[Dict[str, Any]],
        labor_calculation_method: str,
        labor_hours: Optional[Decimal],
        hourly_labor_rate: Optional[Decimal],
        total_labor_cost: Optional[Decimal],
        packaging_cost: Decimal,
        transport_cost: Decimal,
        overhead_cost: Decimal,
        overhead_allocation_basis: str,
        other_costs: Decimal,
        batch_quantity: int,
        desired_margin_percentage: Decimal,
    ) -> Dict[str, Any]:
        """
        Calculates itemized and aggregated production costs using pure Decimal arithmetic.
        """
        batch_qty_dec = Decimal(str(max(1, batch_quantity)))

        # 1. Calculate materials total
        processed_materials = []
        total_materials = Decimal("0.00")
        for item in materials:
            name = item.get("material_name", "Unknown Material")
            qty = Decimal(str(item.get("quantity", "1.0")))
            unit = item.get("unit", "units")
            unit_cost = Decimal(str(item.get("unit_cost_inr", "0.00")))
            line_total = (qty * unit_cost).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            total_materials += line_total
            processed_materials.append({
                "material_name": name,
                "quantity": str(qty),
                "unit": unit,
                "unit_cost_inr": str(unit_cost),
                "total_cost_inr": str(line_total),
                "source_type": item.get("source_type", "ARTISAN_ENTERED"),
                "source_reference": item.get("source_reference")
            })

        # 2. Calculate labor
        calc_labor = Decimal("0.00")
        labor_method = labor_calculation_method.strip().upper()
        if labor_method == "HOURLY_RATE":
            if labor_hours is not None and hourly_labor_rate is not None:
                calc_labor = (Decimal(str(labor_hours)) * Decimal(str(hourly_labor_rate))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            elif total_labor_cost is not None:
                calc_labor = Decimal(str(total_labor_cost)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:  # TOTAL_STATED
            if total_labor_cost is not None:
                calc_labor = Decimal(str(total_labor_cost)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            elif labor_hours is not None and hourly_labor_rate is not None:
                calc_labor = (Decimal(str(labor_hours)) * Decimal(str(hourly_labor_rate))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        pkg_cost = Decimal(str(packaging_cost if packaging_cost is not None else "0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        trn_cost = Decimal(str(transport_cost if transport_cost is not None else "0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        ovh_cost = Decimal(str(overhead_cost if overhead_cost is not None else "0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        oth_cost = Decimal(str(other_costs if other_costs is not None else "0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # 3. Direct costs sum for batch
        direct_costs_batch = total_materials + calc_labor + pkg_cost + trn_cost + oth_cost

        # 4. Overhead allocation
        ovh_basis = overhead_allocation_basis.strip().upper()
        if ovh_basis == "PER_PRODUCT":
            # Stated overhead is per single product, so for batch it multiplies by batch_quantity
            total_production_cost = direct_costs_batch + (ovh_cost * batch_qty_dec)
            unit_cost = (total_production_cost / batch_qty_dec).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        elif ovh_basis in ["PER_BATCH", "MONTHLY_ALLOCATION"]:
            # Stated overhead is for the entire batch
            total_production_cost = direct_costs_batch + ovh_cost
            unit_cost = (total_production_cost / batch_qty_dec).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:  # DOCUMENTED_PERCENTAGE
            # Stated overhead is a direct amount
            total_production_cost = direct_costs_batch + ovh_cost
            unit_cost = (total_production_cost / batch_qty_dec).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # 5. Cost-based recommended price with margin
        margin_pct = Decimal(str(desired_margin_percentage if desired_margin_percentage is not None else "25.00"))
        margin_multiplier = Decimal("1.00") + (margin_pct / Decimal("100.00"))
        cost_baseline_price = (unit_cost * margin_multiplier).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        return {
            "processed_materials": processed_materials,
            "total_material_cost": total_materials,
            "labor_calculation_method": labor_method,
            "labor_hours": Decimal(str(labor_hours)) if labor_hours is not None else None,
            "hourly_labor_rate": Decimal(str(hourly_labor_rate)) if hourly_labor_rate is not None else None,
            "total_labor_cost": calc_labor,
            "packaging_cost": pkg_cost,
            "transport_cost": trn_cost,
            "overhead_cost": ovh_cost,
            "overhead_allocation_basis": ovh_basis,
            "other_costs": oth_cost,
            "batch_quantity": int(batch_quantity),
            "desired_margin_percentage": margin_pct,
            "direct_costs_batch": direct_costs_batch,
            "total_production_cost": total_production_cost,
            "cost_baseline_unit_cost": unit_cost,
            "cost_baseline_recommended_price": cost_baseline_price
        }

    @classmethod
    def filter_and_evaluate_market_evidence(
        cls,
        observations: List[Any],
        target_craft_id: str,
        target_materials: List[str]
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        """
        Validates, filters, deduplicates, and evaluates market price observations.
        Enforces product comparability, freshness, currency consistency, and minimum sample thresholds.
        """
        now = datetime.now(timezone.utc)
        valid_observations: List[Dict[str, Any]] = []
        seen_keys = set()

        def get_field(item: Any, field_name: str, default: Any = None) -> Any:
            if isinstance(item, dict):
                return item.get(field_name, default)
            val = getattr(item, field_name, default)
            return default if val is None else val

        for obs in observations:
            craft_id = get_field(obs, "craft_id")
            if str(craft_id) != str(target_craft_id):
                continue

            currency = get_field(obs, "currency", "INR")
            if currency != "INR":
                continue

            price = get_field(obs, "observed_price")
            if price is None:
                continue
            price_dec = Decimal(str(price)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if price_dec <= Decimal("0.00"):
                continue

            obs_date = get_field(obs, "observation_date")
            is_stale = False
            if obs_date:
                if hasattr(obs_date, "tzinfo") and obs_date.tzinfo is None:
                    obs_date = obs_date.replace(tzinfo=timezone.utc)
                age_days = (now - obs_date).days
                if age_days > 730:  # Older than 2 years / 24 months
                    is_stale = True

            source_name = get_field(obs, "source_name", "Unknown Source")
            source_type = get_field(obs, "source_type", "OTHER_DOCUMENTED_SOURCE")
            source_url = get_field(obs, "source_url")
            obs_id = get_field(obs, "id")

            dedup_key = (source_name, str(price_dec), str(obs_date))
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            attrs = get_field(obs, "attributes_json", {})
            comp_tags = get_field(obs, "comparability_tags", [])

            # Check material compatibility if target has materials specified
            is_material_compatible = True
            if target_materials and attrs and "primary_material" in attrs:
                obs_mat = str(attrs["primary_material"]).strip().lower()
                target_mats_lower = [m.lower() for m in target_materials]
                if obs_mat not in target_mats_lower and not any(m in obs_mat for m in target_mats_lower):
                    is_material_compatible = False

            if not is_material_compatible:
                continue

            valid_observations.append({
                "id": str(obs_id) if obs_id else None,
                "product_title": get_field(obs, "product_title"),
                "observed_price": price_dec,
                "currency": currency,
                "source_name": source_name,
                "source_type": source_type,
                "source_url": source_url,
                "observation_date": obs_date.isoformat() if hasattr(obs_date, "isoformat") else str(obs_date),
                "is_stale": is_stale,
                "attributes": attrs,
                "comparability_tags": comp_tags,
                "evidence_quality_status": get_field(obs, "evidence_quality_status", "MEDIUM")
            })

        count = len(valid_observations)

        # Enforce N >= 3 rule
        if count < MIN_OBSERVATION_THRESHOLD:
            evidence_status = "INSUFFICIENT_MARKET_EVIDENCE"
            stats = {
                "status": evidence_status,
                "observation_count": count,
                "required_threshold": MIN_OBSERVATION_THRESHOLD,
                "median_inr": None,
                "min_inr": None,
                "max_inr": None,
                "iqr_low_inr": None,
                "iqr_high_inr": None,
                "quality_rating": "INSUFFICIENT",
                "sources_used": list({obs["source_name"] for obs in valid_observations})
            }
            return valid_observations, evidence_status, stats

        # If count >= 3, compute robust order statistics
        prices = sorted([obs["observed_price"] for obs in valid_observations])
        min_price = prices[0]
        max_price = prices[-1]

        # Calculate median
        if count % 2 == 1:
            median_price = prices[count // 2]
        else:
            mid = count // 2
            median_price = ((prices[mid - 1] + prices[mid]) / Decimal("2")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Calculate 25th percentile (Q1) and 75th percentile (Q3) using nearest rank
        def percentile(p: float) -> Decimal:
            idx = int(round(p * (count - 1)))
            return prices[idx]

        iqr_low = percentile(0.25)
        iqr_high = percentile(0.75)

        # Evaluate quality rating
        official_sources_count = sum(1 for obs in valid_observations if obs["source_type"] in ["GOVERNMENT", "OFFICIAL_REGISTRY", "OFFICIAL_MARKETPLACE"])
        stale_count = sum(1 for obs in valid_observations if obs["is_stale"])

        if count >= 5 and official_sources_count >= 2 and stale_count == 0:
            quality_rating = "HIGH"
        elif count >= 3 and stale_count == 0:
            quality_rating = "MEDIUM"
        else:
            quality_rating = "LOW"

        evidence_status = "SUFFICIENT_MARKET_EVIDENCE"
        stats = {
            "status": evidence_status,
            "observation_count": count,
            "required_threshold": MIN_OBSERVATION_THRESHOLD,
            "median_inr": median_price,
            "min_inr": min_price,
            "max_inr": max_price,
            "iqr_low_inr": iqr_low,
            "iqr_high_inr": iqr_high,
            "quality_rating": quality_rating,
            "sources_used": list({obs["source_name"] for obs in valid_observations})
        }

        return valid_observations, evidence_status, stats

    @classmethod
    def synthesize_fair_price_analysis(
        cls,
        cost_breakdown: Dict[str, Any],
        market_stats: Dict[str, Any],
        valid_observations: List[Dict[str, Any]],
        artisan_current_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes cost structures and market evidence into an explainable fair price analysis.
        Strictly distinguishes between COST_ONLY_BASELINE and FAIR_PRICE_ANALYSIS.
        """
        unit_cost = cost_breakdown["cost_baseline_unit_cost"]
        cost_baseline_price = cost_breakdown["cost_baseline_recommended_price"]
        evidence_status = market_stats["status"]

        if evidence_status == "INSUFFICIENT_MARKET_EVIDENCE":
            # Cost-Only Baseline: Cannot estimate market-based range
            analysis_type = "COST_ONLY_BASELINE"
            floor_price = unit_cost
            recommended_price = cost_baseline_price
            range_min = cost_baseline_price
            range_max = (cost_baseline_price * Decimal("1.15")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            # Evidence-Based Fair Price Analysis (N >= 3 valid comparable observations)
            analysis_type = "FAIR_PRICE_ANALYSIS"
            median_p = market_stats["median_inr"]
            q1_p = market_stats["iqr_low_inr"]
            q3_p = market_stats["iqr_high_inr"]

            # Floor price: Artisan should never price below total unit production cost
            floor_price = max(unit_cost, min(cost_baseline_price, q1_p))
            range_min = max(cost_baseline_price, q1_p)
            range_max = max((cost_baseline_price * Decimal("1.25")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP), q3_p)
            recommended_price = max(cost_baseline_price, median_p)

        # Build ordered, traceable step-by-step explanation
        explanation_steps = cls._build_explanation_steps(
            cost_breakdown=cost_breakdown,
            market_stats=market_stats,
            analysis_type=analysis_type,
            floor_price=floor_price,
            range_min=range_min,
            range_max=range_max,
            recommended_price=recommended_price,
            artisan_current_price=artisan_current_price
        )

        limitations = [
            "Cost baseline is calculated from artisan-provided material, labor, and overhead figures (ARTISAN_PROVIDED).",
            "Statutory minimum wages or formal labor contracts are not verified by this engine.",
            "Market reference observations reflect public, documented retail references and do not guarantee instant buyer demand.",
            "Actual realization price may vary based on buyer order volume, customization complexity, and seasonality."
        ]
        if evidence_status == "INSUFFICIENT_MARKET_EVIDENCE":
            limitations.insert(
                0,
                f"Market evidence is currently insufficient ({market_stats['observation_count']} comparable observations found; minimum {MIN_OBSERVATION_THRESHOLD} required). No market range has been fabricated."
            )

        return {
            "engine_version": ENGINE_VERSION,
            "currency": "INR",
            "analysis_type": analysis_type,
            "evidence_status": evidence_status,
            "floor_price": floor_price,
            "recommended_price": recommended_price,
            "fair_price_min": range_min,
            "fair_price_max": range_max,
            "cost_baseline": {
                "total_material_cost": cost_breakdown["total_material_cost"],
                "total_labor_cost": cost_breakdown["total_labor_cost"],
                "packaging_cost": cost_breakdown["packaging_cost"],
                "transport_cost": cost_breakdown["transport_cost"],
                "overhead_cost": cost_breakdown["overhead_cost"],
                "other_costs": cost_breakdown["other_costs"],
                "batch_quantity": cost_breakdown["batch_quantity"],
                "total_production_cost": cost_breakdown["total_production_cost"],
                "unit_production_cost": unit_cost,
                "desired_margin_percentage": cost_breakdown["desired_margin_percentage"],
                "cost_baseline_price": cost_baseline_price,
                "currency": "INR"
            },
            "market_evidence": market_stats,
            "explanation_steps": explanation_steps,
            "limitations_notes": limitations,
            "provenance_state": "CALCULATED"
        }

    @classmethod
    def _build_explanation_steps(
        cls,
        cost_breakdown: Dict[str, Any],
        market_stats: Dict[str, Any],
        analysis_type: str,
        floor_price: Decimal,
        range_min: Decimal,
        range_max: Decimal,
        recommended_price: Decimal,
        artisan_current_price: Optional[Decimal]
    ) -> List[Dict[str, Any]]:
        """
        Builds structured, transparent explanation steps showing exact mathematical inputs and calculations.
        """
        steps = []

        # Step 1: Input Provenance
        steps.append({
            "step_number": 1,
            "title": "Input Data Sources & Provenance",
            "detail": f"Cost inputs are ARTISAN_PROVIDED. Materials count: {len(cost_breakdown.get('processed_materials', []))}. Labor method: {cost_breakdown['labor_calculation_method']}.",
            "inputs_used": {
                "materials_count": len(cost_breakdown.get("processed_materials", [])),
                "labor_hours": str(cost_breakdown.get("labor_hours")),
                "labor_rate": str(cost_breakdown.get("hourly_labor_rate")),
                "batch_quantity": cost_breakdown["batch_quantity"]
            }
        })

        # Step 2: Cost Build-up Equation
        mat = cost_breakdown["total_material_cost"]
        lab = cost_breakdown["total_labor_cost"]
        pkg = cost_breakdown["packaging_cost"]
        trn = cost_breakdown["transport_cost"]
        ovh = cost_breakdown["overhead_cost"]
        oth = cost_breakdown["other_costs"]
        tot = cost_breakdown["total_production_cost"]
        unit = cost_breakdown["cost_baseline_unit_cost"]
        qty = cost_breakdown["batch_quantity"]

        steps.append({
            "step_number": 2,
            "title": "Production Cost Build-up",
            "detail": f"Direct costs = Materials (₹{mat}) + Labor (₹{lab}) + Packaging (₹{pkg}) + Transport (₹{trn}) + Other (₹{oth}) + Overhead (₹{ovh}) = Total ₹{tot} for {qty} unit(s). Unit cost = ₹{unit}.",
            "mathematical_formula": "Unit Cost = (Materials + Labor + Packaging + Transport + Overhead + Other) / Batch Quantity"
        })

        # Step 3: Margin Addition
        margin = cost_breakdown["desired_margin_percentage"]
        cost_price = cost_breakdown["cost_baseline_recommended_price"]
        steps.append({
            "step_number": 3,
            "title": "Cost-Plus Margin Baseline",
            "detail": f"Applying stated artisan profit margin of {margin}% to unit production cost ₹{unit} yields a Cost-Based Price Baseline of ₹{cost_price}.",
            "mathematical_formula": f"Cost Baseline Price = ₹{unit} × (1 + {margin} / 100) = ₹{cost_price}"
        })

        # Step 4: Market Evidence Analysis
        if market_stats["status"] == "SUFFICIENT_MARKET_EVIDENCE":
            cnt = market_stats["observation_count"]
            med = market_stats["median_inr"]
            q1 = market_stats["iqr_low_inr"]
            q3 = market_stats["iqr_high_inr"]
            sources_str = ", ".join(market_stats["sources_used"])
            steps.append({
                "step_number": 4,
                "title": "Comparable Market Evidence Synthesis",
                "detail": f"Evaluated {cnt} comparable documented market observations from [{sources_str}]. Observed Median is ₹{med} with Interquartile Range (IQR) of ₹{q1} – ₹{q3}.",
                "mathematical_formula": "Median = 50th percentile, IQR = [25th percentile, 75th percentile]"
            })
        else:
            cnt = market_stats["observation_count"]
            steps.append({
                "step_number": 4,
                "title": "Market Evidence Assessment",
                "detail": f"Found {cnt} comparable observations. Minimum requirement is {MIN_OBSERVATION_THRESHOLD} observations. Market evidence is insufficient to calculate a defensible market range without fabricating data.",
                "mathematical_formula": f"Observation count ({cnt}) < Minimum threshold ({MIN_OBSERVATION_THRESHOLD})"
            })

        # Step 5: Fair Price Synthesis
        if analysis_type == "FAIR_PRICE_ANALYSIS":
            steps.append({
                "step_number": 5,
                "title": "Evidence-Based Fair Price Synthesis",
                "detail": f"Recommended Floor Price is ₹{floor_price} (ensuring artisan never sells below unit production cost ₹{unit}). Suggested Fair Retail Range is ₹{range_min} – ₹{range_max}, with a Recommended Fair Retail Price of ₹{recommended_price}.",
                "mathematical_formula": "Floor = max(Unit Cost, min(Cost Baseline, Q1)); Recommended = max(Cost Baseline, Median); Range = [max(Cost Baseline, Q1), max(Cost Baseline × 1.25, Q3)]"
            })
        else:
            steps.append({
                "step_number": 5,
                "title": "Cost-Only Baseline Recommendation",
                "detail": f"Because market evidence is insufficient, pricing is based strictly on production economics. Recommended price floor is ₹{floor_price} (unit cost) and recommended baseline price is ₹{recommended_price} (unit cost + {margin}% margin).",
                "mathematical_formula": "Floor = Unit Cost; Recommended = Cost Baseline Price"
            })

        # Step 6: Comparison with current artisan price (if provided)
        if artisan_current_price is not None:
            curr = Decimal(str(artisan_current_price)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if curr < unit:
                diff = unit - curr
                steps.append({
                    "step_number": 6,
                    "title": "Current Price Risk Warning",
                    "detail": f"WARNING: Your current selling price (₹{curr}) is ₹{diff} below your unit production cost (₹{unit}). You are incurring a loss on each unit produced.",
                    "inputs_used": {"current_price": str(curr), "unit_cost": str(unit)}
                })
            elif curr < recommended_price:
                diff = recommended_price - curr
                steps.append({
                    "step_number": 6,
                    "title": "Value Realization Opportunity",
                    "detail": f"Your current price (₹{curr}) is ₹{diff} below the recommended fair price (₹{recommended_price}). Your work has room for higher value realization.",
                    "inputs_used": {"current_price": str(curr), "recommended_price": str(recommended_price)}
                })
            else:
                steps.append({
                    "step_number": 6,
                    "title": "Current Price Comparison",
                    "detail": f"Your current price (₹{curr}) covers production costs (₹{unit}) and satisfies your desired margin threshold.",
                    "inputs_used": {"current_price": str(curr), "unit_cost": str(unit)}
                })

        return steps
