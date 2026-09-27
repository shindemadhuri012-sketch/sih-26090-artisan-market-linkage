"""
SIH 26090: Data Source & Provenance Management Models
Defines DataSource and DataImport entities to ensure complete lineage for all external datasets.
"""

from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid, utc_now


class DataSource(Base, TimestampMixin):
    """Authoritative external public registries and government data providers."""
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_identifier = Column(String(100), unique=True, nullable=False, index=True)
    source_name = Column(String(200), nullable=False)
    custodian_organization = Column(String(200), nullable=False)
    official_url = Column(Text, nullable=False)
    license_type = Column(String(100), nullable=False)
    is_active_feed = Column(Boolean, nullable=False, default=True)

    # Relationships
    data_imports = relationship("DataImport", back_populates="data_source", cascade="all, delete-orphan")
    crafts = relationship("Craft", back_populates="data_source")


class DataImport(Base):
    """Cryptographic audit record for every external data ingestion batch."""
    __tablename__ = "data_imports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    import_version = Column(String(50), nullable=False)
    records_extracted = Column(Integer, nullable=False)
    records_ingested = Column(Integer, nullable=False)
    records_failed = Column(Integer, nullable=False, default=0)
    checksum_hash = Column(String(64), nullable=False)
    report_json = Column(JSON, default=dict, nullable=False)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    data_source = relationship("DataSource", back_populates="data_imports")
