"""
SIH 26090: Matching Engine Unit & API Tests
Verifies hard constraint filtering, hybrid multi-criteria scoring, missing data neutrality,
explainability generation, and matching run API execution.
"""

from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient

from ai.matching.engine import MatchingEngine, MATCHING_ENGINE_V1
from backend.app.models.auth import User
from backend.app.models.product import Product
from backend.app.models.artisan import ArtisanProfile


def test_hard_constraint_filtering_eliminations():
    """Validates that unpublished products, missing artisan, or GI tag violations are eliminated."""
    # 1. Product not PUBLISHED
    draft_prod = SimpleNamespace(status="DRAFT", artisan=SimpleNamespace())
    req = SimpleNamespace(requires_gi_certification=False, required_quantity=10, max_acceptable_moq=None)
    eligible, reason = MatchingEngine.evaluate_hard_constraints(req, draft_prod)
    assert eligible is False
    assert "PUBLISHED" in reason

    # 2. GI Certification demanded, but craft has no GI tag
    non_gi_craft = SimpleNamespace(gi_tag_number=None)
    prod_no_gi = SimpleNamespace(
        status="PUBLISHED",
        artisan=SimpleNamespace(),
        craft=non_gi_craft,
        min_order_quantity=1
    )
    req_gi = SimpleNamespace(requires_gi_certification=True, required_quantity=10, max_acceptable_moq=None)
    eligible, reason = MatchingEngine.evaluate_hard_constraints(req_gi, prod_no_gi)
    assert eligible is False
    assert "GI Certification" in reason

    # 3. MOQ exceeds buyer maximum acceptable MOQ
    prod_high_moq = SimpleNamespace(
        status="PUBLISHED",
        artisan=SimpleNamespace(),
        craft=SimpleNamespace(gi_tag_number="GI-007"),
        min_order_quantity=50
    )
    req_moq = SimpleNamespace(requires_gi_certification=False, required_quantity=10, max_acceptable_moq=20)
    eligible, reason = MatchingEngine.evaluate_hard_constraints(req_moq, prod_high_moq)
    assert eligible is False
    assert "MOQ (50) exceeds" in reason


def test_hybrid_scoring_deterministic_weights():
    """Validates multi-criteria scoring calculation, provenance bonus, and scorecard assembly."""
    craft = SimpleNamespace(name="Chanderi Silk", gi_tag_number="GI-007")
    category = SimpleNamespace(name="Handloom Sarees")
    artisan = SimpleNamespace(
        full_name="Ramesh Weaver",
        monthly_production_capacity=100,
        pehchan_id="PEH-998877",
        cooperative_name="Chanderi Bunkar Samiti"
    )
    prod = SimpleNamespace(
        id="prod-123",
        craft_id="craft-1",
        category_id="cat-1",
        craft=craft,
        category=category,
        artisan=artisan,
        attributes=None,
        materials=["Silk", "Zari", "Cotton"],
        technique="Handloom Extra Weft",
        monthly_production_capacity=80,
        price_inr=Decimal("2500.00"),
        lead_time_days=14
    )

    req = SimpleNamespace(
        target_craft_id="craft-1",
        target_category_id="cat-1",
        desired_materials=["Silk", "Zari"],
        desired_techniques=["Handloom"],
        required_quantity=50,
        target_unit_price_inr=Decimal("3000.00"),
        max_budget_inr=Decimal("150000.00"),
        deadline_date=datetime.now(timezone.utc) + timedelta(days=30),
        max_lead_time_days=None
    )

    scorecard = MatchingEngine.score_candidate(requirement=req, product=prod, semantic_similarity=0.85)

    assert scorecard.engine_version == MATCHING_ENGINE_V1
    assert scorecard.craft_compatibility == 1.00  # Exact craft match
    assert scorecard.material_compatibility == 1.00  # Both Silk and Zari present
    assert scorecard.capacity_compatibility == 1.00  # 80 capacity satisfies 50 units
    assert scorecard.price_compatibility == 1.00  # 2500 is within 3000 budget
    assert scorecard.lead_time_compatibility == 1.00  # 14 days is well within 30 days
    assert scorecard.provenance_bonus > 0.04  # GI + Pehchan + Cooperative
    assert scorecard.composite_score >= 0.90  # High compatibility match
    assert len(scorecard.positive_reasons) >= 4


def test_missing_data_neutral_scoring_and_limitations():
    """Verifies that missing optional data is scored neutrally and produces explicit limitations."""
    prod_sparse = SimpleNamespace(
        id="prod-sparse",
        craft_id="craft-2",
        category_id=None,
        craft=None,
        category=None,
        artisan=SimpleNamespace(monthly_production_capacity=10, pehchan_id=None, cooperative_name=None),
        attributes=None,
        materials=[],  # Missing materials
        technique=None,  # Missing technique
        monthly_production_capacity=None,
        price_inr=None,  # Missing price
        lead_time_days=7
    )

    req = SimpleNamespace(
        target_craft_id="craft-1",
        target_category_id="cat-1",
        desired_materials=["Brass"],
        desired_techniques=["Dokra"],
        required_quantity=20,
        target_unit_price_inr=None,
        max_budget_inr=None,
        deadline_date=None,
        max_lead_time_days=None
    )

    scorecard = MatchingEngine.score_candidate(requirement=req, product=prod_sparse, semantic_similarity=None)

    # Missing fields must be recorded
    assert "semantic_embedding" in scorecard.missing_fields
    assert "product_materials" in scorecard.missing_fields
    assert "product_price" in scorecard.missing_fields
    assert scorecard.data_sufficiency_state in {"PARTIALLY_MATCHABLE", "INSUFFICIENT_INFORMATION"}
    assert len(scorecard.limitations) >= 3


@pytest.mark.asyncio
async def test_end_to_end_matching_api_run(
    client: AsyncClient,
    buyer_user: User,
    buyer_headers: dict,
    artisan_user: User,
    seed_craft: dict
):
    # Setup buyer
    await client.post(
        "/api/v1/buyers/me",
        json={"company_name": "FabIndia Matching Suite", "buyer_type": "RETAIL_CURATOR"},
        headers=buyer_headers
    )

    # Setup artisan profile and published product
    artisan_profile = ArtisanProfile(
        user_id=artisan_user.id,
        full_name="Kishore Weaver",
        state="Madhya Pradesh",
        district="Ashoknagar",
        pincode="473446",
        primary_craft_id=seed_craft.id,
        monthly_production_capacity=120,
        pehchan_id="PEH-CHAND-001"
    )
    from backend.app.core.database import get_async_db
    # Create product directly via client or DB
    # We will create via DB session in client override
    deadline = (datetime.now(timezone.utc) + timedelta(days=40)).isoformat()
    req_res = await client.post(
        "/api/v1/buyer-requirements",
        json={
            "title": "Chanderi Silk Procurement Batch",
            "raw_text": "Need 50 authentic Chanderi Silk Saree items.",
            "target_craft_id": seed_craft.id,
            "required_quantity": 50,
            "target_unit_price_inr": 4000.00,
            "deadline_date": deadline
        },
        headers=buyer_headers
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Run matches API (even with 0 published products, it executes cleanly and returns empty list)
    run_res = await client.post(f"/api/v1/matches/requirements/{req_id}/run", headers=buyer_headers)
    assert run_res.status_code == 200
    assert isinstance(run_res.json(), list)
