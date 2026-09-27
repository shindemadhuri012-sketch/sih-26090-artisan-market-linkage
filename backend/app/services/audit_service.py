"""
SIH 26090: Security Audit Service
Creates immutable audit trail entries for sensitive operations and state transitions.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.auth import AuditLog
from backend.app.core.telemetry import logger


async def record_audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[str] = None,
    ip_address: str = "127.0.0.1",
    user_agent: Optional[str] = None,
    payload_before: Optional[Dict[str, Any]] = None,
    payload_after: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Appends an immutable record to the audit_logs table."""
    audit_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload_before_json=payload_before,
        payload_after_json=payload_after or {}
    )
    db.add(audit_entry)
    await db.flush()
    logger.info(f"AUDIT: [{action}] on {entity_type}:{entity_id} by user:{actor_user_id}")
    return audit_entry
