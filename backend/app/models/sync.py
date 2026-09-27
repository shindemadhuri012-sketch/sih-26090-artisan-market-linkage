"""
SIH 26090: Sync Operation Model
Tracks offline client mutations, idempotency keys, and replay states.
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now


class SyncOperation(Base):
    """
    Server-side record of an offline mutation processed through the sync engine.
    Guarantees idempotency upon network retry, audits offline operations,
    and caches responses for identical replay attempts.
    """
    __tablename__ = "sync_operations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    entity_type = Column(String(30), nullable=False, index=True, doc="PRODUCT, PRODUCT_MEDIA, RFQ_RESPONSE")
    entity_id = Column(String(36), nullable=False)
    operation_type = Column(String(30), nullable=False, doc="CREATE, UPDATE, DELETE, RESPOND_RFQ")
    
    status = Column(
        String(20),
        nullable=False,
        default="COMMITTED",
        index=True,
        doc="COMMITTED, REJECTED, CONFLICT"
    )
    client_mutation_id = Column(String(36), nullable=True, doc="Client-assigned local UUID")
    response_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User")
