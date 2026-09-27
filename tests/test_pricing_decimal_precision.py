"""
SIH 26090: Decimal Precision & Monetary Integrity Tests
Verifies that all monetary arithmetic avoids floating-point errors,
uses exact Python Decimal objects, and applies ROUND_HALF_UP quantization.
"""

from decimal import Decimal
import pytest
from ai.pricing.engine import FairPriceEngine, quantize_inr


def test_no_floating_point_imprecision():
    """
    Verifies that classic IEEE 754 floating point imprecision (0.1 + 0.2 != 0.3)
    does not occur in the pricing engine.
    """
    materials = [
        {"material_name": "Item A", "quantity": "1.0", "unit": "pc", "unit_cost_inr": "0.10"},
        {"material_name": "Item B", "quantity": "1.0", "unit": "pc", "unit_cost_inr": "0.20"}
    ]

    calc = FairPriceEngine.calculate_cost_breakdown(
        materials=materials,
        labor_calculation_method="HOURLY_RATE",
        labor_hours=None,
        hourly_labor_rate=None,
        total_labor_cost=None,
        packaging_cost=Decimal("0.00"),
        transport_cost=Decimal("0.00"),
        overhead_cost=Decimal("0.00"),
        overhead_allocation_basis="PER_PRODUCT",
        other_costs=Decimal("0.00"),
        batch_quantity=1,
        desired_margin_percentage=Decimal("0.00")
    )

    # In binary float, 0.1 + 0.2 == 0.30000000000000004
    # In Decimal, it must be EXACTLY Decimal('0.30')
    assert calc["total_material_cost"] == Decimal("0.30")
    assert calc["total_production_cost"] == Decimal("0.30")
    assert calc["cost_baseline_unit_cost"] == Decimal("0.30")
    assert calc["cost_baseline_recommended_price"] == Decimal("0.30")


def test_division_and_quantization_precision():
    """
    Verifies that batch division (e.g. 1000 / 3) produces clean 2-decimal rounded results
    using ROUND_HALF_UP without infinite expansion or float approximations.
    """
    calc = FairPriceEngine.calculate_cost_breakdown(
        materials=[],
        labor_calculation_method="TOTAL_STATED",
        labor_hours=None,
        hourly_labor_rate=None,
        total_labor_cost=Decimal("1000.00"),
        packaging_cost=Decimal("0.00"),
        transport_cost=Decimal("0.00"),
        overhead_cost=Decimal("0.00"),
        overhead_allocation_basis="PER_BATCH",
        other_costs=Decimal("0.00"),
        batch_quantity=3,
        desired_margin_percentage=Decimal("25.00")
    )

    # 1000 / 3 = 333.333333... quantized to 2 decimal places is 333.33
    assert calc["cost_baseline_unit_cost"] == Decimal("333.33")

    # 333.33 * 1.25 = 416.6625 quantized with ROUND_HALF_UP is 416.66
    assert calc["cost_baseline_recommended_price"] == Decimal("416.66")


def test_fractional_quantity_precision():
    """
    Verifies fractional quantities like 0.375 meters of silk at 1250.80 INR/meter.
    0.375 * 1250.80 = 469.05 exact.
    """
    materials = [
        {"material_name": "Brocade Silk", "quantity": "0.375", "unit": "meters", "unit_cost_inr": "1250.80"}
    ]

    calc = FairPriceEngine.calculate_cost_breakdown(
        materials=materials,
        labor_calculation_method="TOTAL_STATED",
        labor_hours=None,
        hourly_labor_rate=None,
        total_labor_cost=Decimal("0.00"),
        packaging_cost=Decimal("0.00"),
        transport_cost=Decimal("0.00"),
        overhead_cost=Decimal("0.00"),
        overhead_allocation_basis="PER_PRODUCT",
        other_costs=Decimal("0.00"),
        batch_quantity=1,
        desired_margin_percentage=Decimal("15.00")
    )

    assert calc["total_material_cost"] == Decimal("469.05")
    # 469.05 * 1.15 = 539.4075 -> 539.41
    assert calc["cost_baseline_recommended_price"] == Decimal("539.41")
