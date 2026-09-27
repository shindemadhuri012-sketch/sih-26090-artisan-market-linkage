"""
SIH 26090: Governance, Moderation & Provenance Database Models
Defines GovernanceFlag, ModerationAction, and ProvenanceEvent entities
for tamper-evident auditability, neutral review signaling, and audited state transitions.
"""

import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid, utc_now


def canonical_json_dumps(obj: Any) -> str:
    """
    Deterministic canonical JSON serializer:
    - stable key ordering (sort_keys=True)
    - strict separators without whitespace (',', ':')
    - explicit UTF-8 encoding
    - normalized ISO-8601 UTC datetimes
    """
    def _default(val: Any) -> Any:
        if isinstance(val, datetime):
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            return val.astimezone(timezone.utc).isoformat()
        return str(val)

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_default, ensure_ascii=True)


def compute_provenance_event_hash(
    event_id: str,
    entity_type: str,
    entity_id: str,
    field_name: str,
    previous_value_json: Any,
    new_value_json: Any,
    provenance_state: str,
    actor_user_id: Optional[str],
    actor_role: str,
    source_id: Optional[str],
    created_at: datetime,
    sequence_number: int,
    previous_event_hash: str
) -> str:
    """
    Computes a deterministic SHA-256 hash over the canonical payload of a ProvenanceEvent.
    Guarantees tamper-evident auditability across historical state transitions.
    """
    payload_dict = {
        "event_id": event_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field_name": field_name,
        "previous_value": previous_value_json,
        "new_value": new_value_json,
        "provenance_state": provenance_state,
        "actor_user_id": actor_user_id or "NONE",
        "actor_role": actor_role,
        "source_id": source_id or "NONE",
        "created_at": created_at.astimezone(timezone.utc).isoformat() if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc).isoformat(),
        "sequence_number": sequence_number,
        "previous_event_hash": previous_event_hash
    }
    canonical_repr = canonical_json_dumps(payload_dict)
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


class GovernanceFlag(Base, TimestampMixin):
    """
    Neutral administrative review signal identifying data quality issues,
    missing provenance, or policy anomalies.
    """
    __tablename__ = "governance_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True, doc="Product, ArtisanProfile, CraftPassport, MarketPriceObservation")
    entity_id = Column(String(36), nullable=False, index=True)
    flag_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="MISSING_PROVENANCE, PRICE_ANOMALY_REVIEW, UNSUPPORTED_CLAIM, EXPIRED_EVIDENCE, DUPLICATE_SOURCE, STALE_MARKET_DATA, SAMPLE_EXPOSURE"
    )
    severity = Column(String(20), nullable=False, default="MEDIUM", index=True, doc="LOW, MEDIUM, HIGH")
    status = Column(
        String(30),
        nullable=False,
        default="OPEN",
        index=True,
        doc="OPEN, UNDER_INVESTIGATION, RESOLVED_VALIDATED, RESOLVED_CORRECTED, RESOLVED_ACTIONED, DISMISSED"
    )
    details_json = Column(JSON, default=dict, nullable=False)
    flagged_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Compound index for fast queries by entity
    __table_args__ = (
        Index("idx_gov_flags_entity_status", "entity_type", "entity_id", "status"),
        Index("idx_gov_flags_severity_status", "severity", "status"),
    )

    # Relationships
    flagged_by = relationship("User", foreign_keys=[flagged_by_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])


class ModerationAction(Base):
    """
    Formal record of an administrative or moderator decision on a platform resource.
    Documents review rationale, state transitions, internal notes, and user-facing feedback.
    """
    __tablename__ = "moderation_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True, doc="Product, ArtisanProfile, CraftPassport, Verification, ProductMedia")
    entity_id = Column(String(36), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    decision = Column(String(50), nullable=False, index=True, doc="APPROVE, REJECT, REQUEST_CHANGES, SUSPEND, RESTORE")
    moderator_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason_category = Column(
        String(100),
        nullable=True,
        doc="QUALITY_DEFICIENCY, AUTHENTICITY_VERIFIED, INCORRECT_ATTRIBUTES, POLICY_VIOLATION, OTHER"
    )
    moderator_notes = Column(Text, nullable=True, doc="Internal moderator notes (never exposed publicly)")
    feedback_to_user = Column(Text, nullable=True, doc="Constructive feedback delivered to the resource owner")
    evidence_reference = Column(Text, nullable=True, doc="Authoritative reference or document inspected")
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("idx_mod_actions_entity_created", "entity_type", "entity_id", "created_at"),
    )

    # Relationships
    moderator = relationship("User", foreign_keys=[moderator_user_id])


class ProvenanceEvent(Base):
    """
    Append-only, tamper-evident historical ledger tracking field-level provenance changes.
    Employs SHA-256 cryptographic hash-chaining across sequential revisions.
    """
    __tablename__ = "provenance_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True, doc="Product, ArtisanProfile, CraftPassport, Craft, Verification")
    entity_id = Column(String(36), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    previous_value_json = Column(JSON, nullable=True)
    new_value_json = Column(JSON, nullable=False)
    provenance_state = Column(
        String(50),
        nullable=False,
        index=True,
        doc="ARTISAN_PROVIDED, SOURCE_BACKED, AI_SUGGESTED, CALCULATED, HUMAN_CONFIRMED, ADMIN_APPROVED, ADMIN_REJECTED, FLAGGED, SUPERSEDED, AUTHORITY_VERIFIED"
    )
    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_role = Column(String(30), nullable=False, default="artisan")
    change_reason = Column(Text, nullable=True)
    source_id = Column(String(100), nullable=True)
    source_url = Column(Text, nullable=True)
    evidence_reference = Column(Text, nullable=True)
    ai_model_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    human_confirmation_status = Column(Boolean, nullable=False, default=False)
    event_hash = Column(String(64), nullable=False, index=True)
    previous_event_hash = Column(String(64), nullable=False)
    sequence_number = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("idx_prov_events_entity_field", "entity_type", "entity_id", "field_name"),
        Index("idx_prov_events_entity_seq", "entity_type", "entity_id", "sequence_number"),
    )

    # Relationships
    actor = relationship("User", foreign_keys=[actor_user_id])
