"""
SIH 26090: Provenance Service
Provides cryptographic SHA-256 hash-chaining, field-level change history,
tamper detection, and chronological provenance reconstruction.
"""

import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.governance import ProvenanceEvent, compute_provenance_event_hash
from backend.app.models.auth import User
from backend.app.core.telemetry import logger


def get_genesis_hash(entity_type: str, entity_id: str) -> str:
    """Computes deterministic genesis hash for the root of an entity's provenance chain."""
    seed = f"SIH26090_GENESIS_ROOT_{entity_type}_{entity_id}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


class ProvenanceService:
    """Service orchestrating tamper-evident field-level provenance ledgers."""

    @staticmethod
    async def record_field_change(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        field_name: str,
        previous_value: Any,
        new_value: Any,
        provenance_state: str,
        actor_user: Optional[User] = None,
        change_reason: Optional[str] = None,
        source_id: Optional[str] = None,
        source_url: Optional[str] = None,
        evidence_reference: Optional[str] = None,
        ai_model_version: Optional[str] = None,
        prompt_version: Optional[str] = None,
        human_confirmation_status: bool = False
    ) -> ProvenanceEvent:
        """
        Appends an immutable ProvenanceEvent to the entity's hash-chained ledger.
        """
        # Fetch the latest event for this entity to chain the hash
        latest_res = await db.execute(
            select(ProvenanceEvent)
            .where(
                ProvenanceEvent.entity_type == entity_type,
                ProvenanceEvent.entity_id == entity_id
            )
            .order_by(ProvenanceEvent.sequence_number.desc())
            .limit(1)
        )
        latest_event = latest_res.scalar_one_or_none()

        if latest_event:
            sequence_number = latest_event.sequence_number + 1
            previous_event_hash = latest_event.event_hash
        else:
            sequence_number = 1
            previous_event_hash = get_genesis_hash(entity_type, entity_id)

        now = datetime.now(timezone.utc)
        import uuid
        event_id = str(uuid.uuid4())
        actor_id = actor_user.id if actor_user else None
        actor_role = actor_user.role if actor_user else "system"

        event_hash = compute_provenance_event_hash(
            event_id=event_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            previous_value_json=previous_value,
            new_value_json=new_value,
            provenance_state=provenance_state,
            actor_user_id=actor_id,
            actor_role=actor_role,
            source_id=source_id,
            created_at=now,
            sequence_number=sequence_number,
            previous_event_hash=previous_event_hash
        )

        event = ProvenanceEvent(
            id=event_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            previous_value_json=previous_value,
            new_value_json=new_value,
            provenance_state=provenance_state,
            actor_user_id=actor_id,
            actor_role=actor_role,
            change_reason=change_reason,
            source_id=source_id,
            source_url=source_url,
            evidence_reference=evidence_reference,
            ai_model_version=ai_model_version,
            prompt_version=prompt_version,
            human_confirmation_status=human_confirmation_status,
            event_hash=event_hash,
            previous_event_hash=previous_event_hash,
            sequence_number=sequence_number,
            created_at=now
        )
        db.add(event)
        await db.flush()
        logger.info(f"PROVENANCE: Recorded event #{sequence_number} on {entity_type}:{entity_id}:{field_name} state={provenance_state}")
        return event

    @staticmethod
    async def verify_provenance_chain(
        db: AsyncSession,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Verifies the cryptographic hash-chain integrity for an entity.
        Detects:
        - modified field values or payloads
        - altered previous hashes
        - out-of-order or deleted sequences
        - altered actors or timestamps
        """
        events_res = await db.execute(
            select(ProvenanceEvent)
            .where(
                ProvenanceEvent.entity_type == entity_type,
                ProvenanceEvent.entity_id == entity_id
            )
            .order_by(ProvenanceEvent.sequence_number.asc())
        )
        events = events_res.scalars().all()

        if not events:
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "is_valid": True,
                "total_events": 0,
                "message": "No provenance events recorded for this entity."
            }

        expected_prev_hash = get_genesis_hash(entity_type, entity_id)

        for i, ev in enumerate(events):
            expected_seq = i + 1
            if ev.sequence_number != expected_seq:
                return {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "is_valid": False,
                    "total_events": len(events),
                    "tampered_event_id": ev.id,
                    "tamper_reason": f"Sequence break: Expected #{expected_seq}, found #{ev.sequence_number}."
                }

            if ev.previous_event_hash != expected_prev_hash:
                return {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "is_valid": False,
                    "total_events": len(events),
                    "tampered_event_id": ev.id,
                    "tamper_reason": f"Broken hash chain at sequence #{ev.sequence_number}: previous_event_hash does not match expected predecessor hash."
                }

            # Recompute event hash with stored values
            recomputed_hash = compute_provenance_event_hash(
                event_id=ev.id,
                entity_type=ev.entity_type,
                entity_id=ev.entity_id,
                field_name=ev.field_name,
                previous_value_json=ev.previous_value_json,
                new_value_json=ev.new_value_json,
                provenance_state=ev.provenance_state,
                actor_user_id=ev.actor_user_id,
                actor_role=ev.actor_role,
                source_id=ev.source_id,
                created_at=ev.created_at,
                sequence_number=ev.sequence_number,
                previous_event_hash=ev.previous_event_hash
            )

            if ev.event_hash != recomputed_hash:
                return {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "is_valid": False,
                    "total_events": len(events),
                    "tampered_event_id": ev.id,
                    "tamper_reason": f"Cryptographic signature mismatch at sequence #{ev.sequence_number}: Record payload was altered after creation."
                }

            expected_prev_hash = ev.event_hash

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "is_valid": True,
            "total_events": len(events),
            "latest_sequence": len(events),
            "message": f"Cryptographic provenance chain verified successfully across {len(events)} events."
        }

    @staticmethod
    async def get_entity_timeline(
        db: AsyncSession,
        entity_type: str,
        entity_id: str
    ) -> List[ProvenanceEvent]:
        """Returns chronological list of provenance events for an entity."""
        res = await db.execute(
            select(ProvenanceEvent)
            .where(
                ProvenanceEvent.entity_type == entity_type,
                ProvenanceEvent.entity_id == entity_id
            )
            .order_by(ProvenanceEvent.sequence_number.asc())
        )
        return list(res.scalars().all())
