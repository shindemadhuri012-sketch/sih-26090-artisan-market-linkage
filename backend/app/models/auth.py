"""
SIH 26090: Authentication, Authorization & Audit Models
Defines User, Role, AuditLog, and Notification entities.
"""

from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid, utc_now


class Role(Base):
    """Granular system roles and permission sets."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions_json = Column(JSON, default=list, nullable=False)


class User(Base, TimestampMixin):
    """Central user identity for Artisans, Buyers, Verifiers, and Admins."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="artisan", index=True)
    preferred_language = Column(String(10), nullable=False, default="en")
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Relationships
    artisan_profile = relationship("ArtisanProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
    refresh_sessions = relationship("RefreshTokenSession", back_populates="user", cascade="all, delete-orphan")


class RefreshTokenSession(Base):
    """
    Secure refresh token sessions with SHA-256 hashed storage,
    token family tracking for reuse detection, and revocation support.
    """
    __tablename__ = "refresh_token_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    token_family = Column(String(36), nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationship
    user = relationship("User", back_populates="refresh_sessions")


class OTPChallenge(Base):
    """
    Secure passwordless OTP challenges with SHA-256 code hashing,
    attempt rate-limiting, and consumption state tracking.
    """
    __tablename__ = "otp_challenges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone_number = Column(String(15), nullable=False, index=True)
    otp_code_hash = Column(String(64), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    is_consumed = Column(Boolean, nullable=False, default=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    """Immutable security audit trail recording all critical state mutations."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    payload_before_json = Column(JSON, nullable=True)
    payload_after_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    actor = relationship("User", back_populates="audit_logs")


class Notification(Base):
    """User notifications across in-app, SMS, and messaging channels."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    channel = Column(String(20), nullable=False, default="IN_APP")
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="notifications")
