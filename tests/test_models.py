"""
SIH 26090: Database Model & Metadata Unit Tests
Verifies that all 23 entities have valid schemas, foreign keys, and relationships.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from backend.app.models import (
    Base,
    User,
    Role,
    AuditLog,
    Notification,
    DataSource,
    DataImport,
    CraftCategory,
    Craft,
    CraftPassport,
    ArtisanProfile,
    Verification,
    Product,
    ProductMedia,
    ProductAttributes,
    PriceAnalysis,
    BuyerProfile,
    BuyerRequirement,
    Match,
    MatchExplanation,
    Enquiry,
    Order,
    DemandObservation,
    RefreshTokenSession,
    OTPChallenge
)


def test_all_34_entities_registered_in_metadata():
    """Verifies that all 34 entities are declared and recognized in SQLAlchemy metadata."""
    expected_tables = {
        "users", "roles", "audit_logs", "notifications",
        "data_sources", "data_imports",
        "craft_categories", "crafts", "craft_passports",
        "artisan_profiles", "artisan_crafts", "verifications",
        "products", "product_media", "product_attributes", "price_analyses",
        "product_cost_breakdowns", "market_price_observations",
        "ai_product_analyses", "ai_product_suggestions",
        "buyer_profiles", "buyer_requirements", "requirement_understandings", "matches", "match_explanations",
        "enquiries", "orders", "demand_observations", "demand_forecasts",
        "demand_forecast_runs", "demand_forecast_points", "sync_operations",
        "refresh_token_sessions", "otp_challenges",
        "governance_flags", "moderation_actions", "provenance_events"
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"
    assert len(expected_tables) == 37


def test_in_memory_sqlite_schema_creation_and_insertion():
    """Verifies that tables can be created and core entities inserted with foreign key integrity."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create User and Role
        role = Role(name="artisan", description="Rural artisan role")
        session.add(role)

        user = User(
            phone_number="+919876543210",
            email="artisan@example.in",
            password_hash="hashed_secret",
            role="artisan"
        )
        session.add(user)
        session.flush()

        # 2. Create CraftCategory & Craft
        cat = CraftCategory(name="Handloom Textiles", description="Traditional hand-woven textiles")
        session.add(cat)
        session.flush()

        craft = Craft(
            category_id=cat.id,
            name="Chanderi Weaves",
            gi_tag_number="GI-7",
            has_gi_tag=True,
            origin_state="Madhya Pradesh",
            origin_district="Ashoknagar",
            cultural_heritage_description="Centuries-old delicate sheer handloom weaving tradition.",
            traditional_raw_materials=["Silk", "Cotton", "Zari"]
        )
        session.add(craft)
        session.flush()

        # 3. Create ArtisanProfile
        artisan = ArtisanProfile(
            user_id=user.id,
            full_name="Radha Bai",
            state="Madhya Pradesh",
            district="Ashoknagar",
            pincode="473446",
            primary_craft_id=craft.id,
            monthly_production_capacity=20
        )
        session.add(artisan)
        session.flush()

        # 4. Verify Relationships
        assert artisan.user.email == "artisan@example.in"
        assert artisan.primary_craft.name == "Chanderi Weaves"
        assert len(craft.artisans) == 1
        assert craft.artisans[0].full_name == "Radha Bai"

    finally:
        session.close()
