"""
SIH 26090: RFQ & Enquiry Service
Manages commercial negotiation lifecycle, counter-offers, party-to-transaction security,
and server-side state transitions.
"""

from datetime import datetime, timezone
import secrets
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.market import Enquiry
from backend.app.models.buyer import BuyerRequirement, Match, BuyerProfile
from backend.app.models.product import Product
from backend.app.models.artisan import ArtisanProfile
from backend.app.schemas.matching import (
    RFQCreateRequest,
    RFQResponseRequest,
    RFQBuyerDecisionRequest
)
from backend.app.services.audit_service import record_audit_event


class RFQService:
    """Service layer managing RFQ negotiation state machine."""

    @staticmethod
    def generate_rfq_reference() -> str:
        """Generates human-readable unique reference: RFQ-{HEX8}."""
        token = secrets.token_hex(4).upper()
        return f"RFQ-{token}"

    @staticmethod
    async def create_rfq(
        db: AsyncSession,
        buyer_id: str,
        payload: RFQCreateRequest
    ) -> Enquiry:
        """Creates and dispatches an RFQ to an artisan."""
        rfq_ref = RFQService.generate_rfq_reference()

        enquiry = Enquiry(
            rfq_reference_number=rfq_ref,
            buyer_id=buyer_id,
            artisan_id=payload.artisan_id,
            requirement_id=payload.requirement_id,
            product_id=payload.product_id,
            match_id=payload.match_id,
            message=payload.message,
            proposed_quantity=payload.proposed_quantity,
            proposed_unit_price=payload.proposed_unit_price,
            currency="INR",
            status="SENT",
            created_at=datetime.now(timezone.utc)
        )
        db.add(enquiry)

        # Update Match status if linked
        if payload.match_id:
            m_res = await db.execute(select(Match).where(Match.id == payload.match_id))
            match_rec = m_res.scalar_one_or_none()
            if match_rec:
                match_rec.status = "ENQUIRED"

        await db.flush()
        await db.refresh(enquiry)

        await record_audit_event(
            db=db,
            action="RFQ_DISPATCHED",
            entity_type="Enquiry",
            entity_id=enquiry.id,
            actor_user_id=buyer_id,
            payload_after={
                "rfq_ref": rfq_ref,
                "artisan_id": payload.artisan_id,
                "quantity": payload.proposed_quantity,
                "unit_price": str(payload.proposed_unit_price)
            }
        )

        return enquiry

    @staticmethod
    async def mark_rfq_viewed(
        db: AsyncSession,
        enquiry: Enquiry,
        artisan_id: str
    ) -> Enquiry:
        """Transitions RFQ from SENT to VIEWED when opened by the recipient artisan."""
        if enquiry.artisan_id != artisan_id:
            return enquiry

        if enquiry.status == "SENT":
            enquiry.status = "VIEWED"
            enquiry.viewed_at = datetime.now(timezone.utc)
            await db.flush()

        return enquiry

    @staticmethod
    async def artisan_respond(
        db: AsyncSession,
        enquiry: Enquiry,
        artisan_id: str,
        payload: RFQResponseRequest
    ) -> Enquiry:
        """Processes artisan response to RFQ (Accept, Decline, or Counter-Offer)."""
        action = payload.action.upper()
        now = datetime.now(timezone.utc)

        if action == "ACCEPT":
            enquiry.status = "ACCEPTED"
            enquiry.responded_at = now
            if payload.artisan_response_message:
                enquiry.artisan_response_message = payload.artisan_response_message
        elif action == "DECLINE":
            enquiry.status = "DECLINED"
            enquiry.responded_at = now
            enquiry.decline_reason = payload.decline_reason or "Artisan declined terms"
            if payload.artisan_response_message:
                enquiry.artisan_response_message = payload.artisan_response_message
        elif action == "COUNTER_OFFER":
            enquiry.status = "NEGOTIATION"
            enquiry.responded_at = now
            enquiry.counter_unit_price = payload.counter_unit_price
            enquiry.counter_lead_time_days = payload.counter_lead_time_days
            enquiry.artisan_response_message = payload.artisan_response_message or "Artisan submitted counter-offer"

        await db.flush()

        await record_audit_event(
            db=db,
            action=f"RFQ_{action}",
            entity_type="Enquiry",
            entity_id=enquiry.id,
            actor_user_id=artisan_id,
            payload_after={"status": enquiry.status, "action": action}
        )

        return enquiry

    @staticmethod
    async def buyer_decision(
        db: AsyncSession,
        enquiry: Enquiry,
        buyer_id: str,
        payload: RFQBuyerDecisionRequest
    ) -> Enquiry:
        """Processes buyer decision on an artisan counter-offer."""
        action = payload.action.upper()

        if enquiry.status != "NEGOTIATION":
            raise ValueError(f"Cannot accept or decline counter-offer when status is '{enquiry.status}'.")

        if action == "ACCEPT":
            enquiry.status = "ACCEPTED"
            # Adopt counter-price as agreed unit price
            if enquiry.counter_unit_price:
                enquiry.proposed_unit_price = enquiry.counter_unit_price
        elif action == "DECLINE":
            enquiry.status = "DECLINED"

        await db.flush()

        await record_audit_event(
            db=db,
            action=f"RFQ_BUYER_{action}",
            entity_type="Enquiry",
            entity_id=enquiry.id,
            actor_user_id=buyer_id,
            payload_after={"status": enquiry.status, "action": action}
        )

        return enquiry
