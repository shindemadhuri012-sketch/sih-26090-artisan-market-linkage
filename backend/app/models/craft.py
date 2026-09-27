"""
SIH 26090: Craft, Category & Craft Passport Models
Defines CraftCategory, Craft (grounded in official GI & ODOP records), and digital CraftPassport entities.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin, generate_uuid, utc_now


class CraftCategory(Base, TimestampMixin):
    """High-level craft classification (e.g., Handloom Textiles, Metalware, Pottery)."""
    __tablename__ = "craft_categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)

    # Relationships
    parent = relationship("CraftCategory", remote_side=[id], back_populates="subcategories")
    subcategories = relationship("CraftCategory", back_populates="parent", cascade="all")
    crafts = relationship("Craft", back_populates="category", cascade="all, delete-orphan")


class Craft(Base, TimestampMixin, ProvenanceMixin):
    """Official master directory of Indian crafts mapped to GI Registry and ODOP records."""
    __tablename__ = "crafts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(String(36), ForeignKey("craft_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    normalized_name = Column(String(150), nullable=True, index=True)
    gi_tag_number = Column(String(50), unique=True, nullable=True, index=True)
    has_gi_tag = Column(Boolean, nullable=False, default=False, index=True)
    origin_state = Column(String(100), nullable=False, index=True)
    origin_district = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    cultural_heritage_description = Column(Text, nullable=False)
    traditional_technique = Column(Text, nullable=True)
    traditional_raw_materials = Column(JSON, default=list, nullable=False)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    category = relationship("CraftCategory", back_populates="crafts")
    data_source = relationship("DataSource", back_populates="crafts")
    products = relationship("Product", back_populates="craft")
    craft_passports = relationship("CraftPassport", back_populates="craft")
    artisans = relationship("ArtisanProfile", back_populates="primary_craft")
    artisan_associations = relationship("ArtisanCraft", back_populates="craft", cascade="all, delete-orphan")
    demand_observations = relationship("DemandObservation", back_populates="craft")
    price_observations = relationship("MarketPriceObservation", back_populates="craft", cascade="all, delete-orphan")


class CraftPassport(Base, ProvenanceMixin):
    """Tamper-evident digital provenance passport documenting an artisan's verified craft certification."""
    __tablename__ = "craft_passports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="RESTRICT"), nullable=False, index=True)
    passport_uuid = Column(String(64), unique=True, nullable=False, index=True)
    qr_code_url = Column(Text, nullable=False)
    authorized_user_gi_certificate = Column(Text, nullable=True)
    verification_level = Column(
        String(30),
        nullable=False,
        default="SELF_DECLARED",
        doc="SELF_DECLARED, COOPERATIVE_VERIFIED, GOVERNMENT_VERIFIED_GI"
    )
    status = Column(
        String(30),
        nullable=False,
        default="DRAFT",
        index=True,
        doc="DRAFT, SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED, EXPIRED"
    )
    issued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    provenance_hash = Column(String(64), nullable=False)

    # Relationships
    artisan = relationship("ArtisanProfile", back_populates="craft_passports")
    craft = relationship("Craft", back_populates="craft_passports")
