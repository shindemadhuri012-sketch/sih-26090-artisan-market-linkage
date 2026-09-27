"""
SIH 26090: Artisan Profile & Verification Models
Defines ArtisanProfile and Verification entities with Pehchan ID tracking and KYC workflows.
"""

from sqlalchemy import Column, String, Integer, Text, Float, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, ProvenanceMixin, generate_uuid, utc_now


class ArtisanProfile(Base, TimestampMixin, ProvenanceMixin):
    """Artisan identity, location, production capacity, and cooperative membership."""
    __tablename__ = "artisan_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    cooperative_name = Column(String(200), nullable=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), nullable=False)
    address_line = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    primary_craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="RESTRICT"), nullable=False, index=True)
    years_of_experience = Column(Integer, nullable=False, default=1)
    monthly_production_capacity = Column(Integer, nullable=False, default=10)
    pehchan_id = Column(String(50), unique=True, nullable=True, index=True, doc="Ministry of Textiles Artisan Pehchan Card Number")
    verification_status = Column(String(30), nullable=False, default="PENDING", index=True)

    # Relationships
    user = relationship("User", back_populates="artisan_profile")
    primary_craft = relationship("Craft", back_populates="artisans")
    craft_associations = relationship("ArtisanCraft", back_populates="artisan", cascade="all, delete-orphan")
    craft_passports = relationship("CraftPassport", back_populates="artisan", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="artisan", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="artisan", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="artisan")
    enquiries = relationship("Enquiry", back_populates="artisan")


class ArtisanCraft(Base, TimestampMixin):
    """
    Many-to-many relationship linking an artisan to multiple crafts practiced,
    tracking specific skill levels, experience, technique, and evidence.
    """
    __tablename__ = "artisan_crafts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    craft_id = Column(String(36), ForeignKey("crafts.id", ondelete="RESTRICT"), nullable=False, index=True)
    skill_level = Column(
        String(50),
        nullable=False,
        default="SKILLED",
        doc="MASTER_CRAFTSMAN, SKILLED, APPRENTICE"
    )
    years_of_experience = Column(Integer, nullable=False, default=1)
    is_primary = Column(Boolean, nullable=False, default=False)
    technique = Column(String(150), nullable=True)
    evidence_url = Column(Text, nullable=True)
    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE, VERIFIED, INACTIVE"
    )

    __table_args__ = (
        UniqueConstraint("artisan_id", "craft_id", name="uq_artisan_craft"),
    )

    # Relationships
    artisan = relationship("ArtisanProfile", back_populates="craft_associations")
    craft = relationship("Craft", back_populates="artisan_associations")


class Verification(Base):
    """Artisan KYC identity validation, Pehchan check, and GI Authorized User verification records."""
    __tablename__ = "verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    artisan_id = Column(String(36), ForeignKey("artisan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    verifier_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_type = Column(
        String(50),
        nullable=False,
        doc="PEHCHAN_CARD, AADHAAR, GI_AUTHORIZED_USER_CERT, COOPERATIVE_MEMBERSHIP"
    )
    document_url = Column(Text, nullable=False)
    verification_status = Column(String(30), nullable=False, default="SUBMITTED", index=True)
    rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    decision_date = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    artisan = relationship("ArtisanProfile", back_populates="verifications")
