"""
SIH 26090: Base Model & Entity Mixins
Provides standard primary keys, timestamps, audit fields, and provenance headers across all models.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.types import JSON
from backend.app.core.database import Base


def generate_uuid() -> str:
    """Generates standard UUIDv4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Mixin adding timezone-aware creation and update timestamps."""
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )


class ProvenanceMixin:
    """
    Mixin tracking data source provenance, external identifiers, and demo/sample segregation.
    Ensures zero-fabrication and clear auditability for every imported record.
    """
    is_sample_or_demo = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Explicit flag marking demo/sample records to prevent confusion with verified real data."
    )
    data_provenance_level = Column(
        String(50),
        default="VERIFIED_EXTERNAL_SOURCE",
        nullable=False,
        doc="Provenance tier: OFFICIAL_GOVERNMENT_REGISTRY, VERIFIED_EXTERNAL_SOURCE, USER_DECLARED, DEMO_SAMPLE"
    )
    provenance_metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        doc="Extensible dictionary storing source URL, original source ID, license, retrieval timestamp."
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("is_sample_or_demo", False)
        kwargs.setdefault("data_provenance_level", "VERIFIED_EXTERNAL_SOURCE")
        super().__init__(*args, **kwargs)
