"""
SIH 26090: Provenance Hash-Chain & Tamper-Evident Ledger Tests
Verifies deterministic canonical JSON serialization, SHA-256 hash chaining,
sequence continuity, and detection of simulated database tampering.
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.auth import User
from backend.app.models.governance import ProvenanceEvent, compute_provenance_event_hash, canonical_json_dumps
from backend.app.services.provenance_service import ProvenanceService, get_genesis_hash


@pytest.mark.asyncio
async def test_deterministic_canonical_json_dumps():
    """Verifies that canonical JSON serialization produces stable, whitespace-free output with sorted keys."""
    d1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
    d2 = {"a": 1, "c": [3, 2, 1], "b": 2}
    assert canonical_json_dumps(d1) == canonical_json_dumps(d2)
    assert " " not in canonical_json_dumps(d1)


@pytest.mark.asyncio
async def test_provenance_event_chaining_and_integrity_verification(
    db_session: AsyncSession,
    artisan_user: User
):
    """
    Tests sequential creation of ProvenanceEvents and verifies the cryptographic chain.
    """
    entity_id = str(uuid.uuid4())
    entity_type = "Product"

    # Event 1: Initial Creation
    ev1 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="title",
        previous_value=None,
        new_value="Original Handloom Stole",
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user,
        change_reason="Initial creation"
    )
    assert ev1.sequence_number == 1
    assert ev1.previous_event_hash == get_genesis_hash(entity_type, entity_id)

    # Event 2: AI Suggestion Confirmed
    ev2 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="storytelling_description",
        previous_value="",
        new_value="Authentic Chanderi silk with hand-woven zari borders.",
        provenance_state="HUMAN_CONFIRMED",
        actor_user=artisan_user,
        change_reason="Confirmed AI Studio suggestion",
        ai_model_version="gemini-2.5-flash",
        human_confirmation_status=True
    )
    assert ev2.sequence_number == 2
    assert ev2.previous_event_hash == ev1.event_hash

    # Event 3: Price Adjustment
    ev3 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="price_inr",
        previous_value="1500.00",
        new_value="1750.00",
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user,
        change_reason="Adjusted for silk yarn cost"
    )
    assert ev3.sequence_number == 3
    assert ev3.previous_event_hash == ev2.event_hash

    # Verify chain validity
    verify_res = await ProvenanceService.verify_provenance_chain(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id
    )
    assert verify_res["is_valid"] is True
    assert verify_res["total_events"] == 3


@pytest.mark.asyncio
async def test_tamper_detection_on_altered_payload(
    db_session: AsyncSession,
    artisan_user: User
):
    """
    Simulates malicious modification of a stored row's new_value_json.
    Verifies that verify_provenance_chain immediately flags the tampering.
    """
    entity_id = str(uuid.uuid4())
    entity_type = "Product"

    ev1 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="price_inr",
        previous_value="1000.00",
        new_value="1200.00",
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user
    )

    ev2 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="stock_quantity",
        previous_value=5,
        new_value=10,
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user
    )

    # Malicious direct modification of Event 1 payload
    ev1.new_value_json = "9999.00"
    await db_session.flush()

    verify_res = await ProvenanceService.verify_provenance_chain(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id
    )
    assert verify_res["is_valid"] is False
    assert verify_res["tampered_event_id"] == ev1.id
    assert "Cryptographic signature mismatch" in verify_res["tamper_reason"]


@pytest.mark.asyncio
async def test_tamper_detection_on_sequence_break(
    db_session: AsyncSession,
    artisan_user: User
):
    """
    Simulates sequence tampering (e.g. deleted or skipped event sequence).
    """
    entity_id = str(uuid.uuid4())
    entity_type = "Product"

    ev1 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="title",
        previous_value=None,
        new_value="Product 1",
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user
    )

    ev2 = await ProvenanceService.record_field_change(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name="title",
        previous_value="Product 1",
        new_value="Product 2",
        provenance_state="ARTISAN_PROVIDED",
        actor_user=artisan_user
    )

    # Break sequence number
    ev2.sequence_number = 5
    await db_session.flush()

    verify_res = await ProvenanceService.verify_provenance_chain(
        db=db_session,
        entity_type=entity_type,
        entity_id=entity_id
    )
    assert verify_res["is_valid"] is False
    assert "Sequence break" in verify_res["tamper_reason"]
