"""
SIH 26090: Provenance & Data Lineage Tests
Verifies that models enforce provenance tracking and demo/sample data segregation.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base
from backend.app.models.craft import Craft, CraftCategory
from backend.app.models.product import Product


def test_default_sample_flag_is_false():
    """Verify that by default, entities are not tagged as demo/sample in schema and on persist."""
    # 1. Column default check
    assert Craft.is_sample_or_demo.default.arg is False

    # 2. Database session persistence check
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        cat = CraftCategory(name="Textiles")
        session.add(cat)
        session.flush()

        craft = Craft(
            category_id=cat.id,
            name="Paithani Silk",
            origin_state="Maharashtra",
            origin_district="Chhatrapati Sambhajinagar",
            cultural_heritage_description="Traditional gold zari border handloom silk saree."
        )
        session.add(craft)
        session.flush()

        assert craft.is_sample_or_demo is False
        assert craft.data_provenance_level == "VERIFIED_EXTERNAL_SOURCE"
    finally:
        session.close()


def test_demo_record_explicit_tagging():
    """Verify that development/demo fixtures can be explicitly tagged."""
    demo_product = Product(
        title="[DEMO] Test Saree Sample",
        storytelling_description="Sample demonstration piece for UI testing.",
        price_inr=1500.0,
        is_sample_or_demo=True,
        data_provenance_level="DEMO_SAMPLE",
        provenance_metadata={"fixture_id": "FX-001", "created_by": "developer_test"}
    )
    assert demo_product.is_sample_or_demo is True
    assert demo_product.data_provenance_level == "DEMO_SAMPLE"
    assert demo_product.provenance_metadata["fixture_id"] == "FX-001"
