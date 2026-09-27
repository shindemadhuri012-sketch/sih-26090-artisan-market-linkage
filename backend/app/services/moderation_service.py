"""
SIH 26090: Moderation Service
Manages multi-entity moderation workflows (Products, Artisans, Craft Passports),
enforces idempotent review actions, audit logging, and provenance recording.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.governance import ModerationAction
from backend.app.models.auth import User
from backend.app.models.product import Product
from backend.app.models.artisan import ArtisanProfile, Verification
from backend.app.models.craft import CraftPassport
from backend.app.services.audit_service import record_audit_event
from backend.app.services.provenance_service import ProvenanceService
from backend.app.core.telemetry import logger


class ModerationService:
    """Service executing administrative moderation decisions across platform entities."""

    @staticmethod
    async def list_queue(
        db: AsyncSession,
        entity_type: str = "PRODUCT",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves pending moderation submissions with submitter details and submission age.
        """
        entity_type_upper = entity_type.upper()

        if entity_type_upper == "PRODUCT":
            query = (
                select(Product)
                .options(
                    selectinload(Product.craft),
                    selectinload(Product.category),
                    selectinload(Product.artisan)
                )
                .where(Product.status == "PENDING_REVIEW")
                .order_by(Product.updated_at.asc())
            )
            count_q = select(func.count()).select_from(Product).where(Product.status == "PENDING_REVIEW")
            c_res = await db.execute(count_q)
            total = c_res.scalar() or 0

            res = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
            products = res.scalars().all()

            items = [
                {
                    "entity_type": "PRODUCT",
                    "entity_id": p.id,
                    "title": p.title,
                    "artisan_id": p.artisan_id,
                    "artisan_name": p.artisan.full_name if p.artisan else "Registered Artisan",
                    "craft_name": p.craft.name if p.craft else None,
                    "price_inr": str(p.price_inr),
                    "status": p.status,
                    "submitted_at": p.updated_at.isoformat() if p.updated_at else p.created_at.isoformat()
                }
                for p in products
            ]
            return items, total

        elif entity_type_upper == "VERIFICATION":
            query = (
                select(Verification)
                .options(selectinload(Verification.artisan))
                .where(Verification.verification_status.in_(["SUBMITTED", "UNDER_REVIEW"]))
                .order_by(Verification.created_at.asc())
            )
            count_q = select(func.count()).select_from(Verification).where(Verification.verification_status.in_(["SUBMITTED", "UNDER_REVIEW"]))
            c_res = await db.execute(count_q)
            total = c_res.scalar() or 0

            res = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
            verifs = res.scalars().all()

            items = [
                {
                    "entity_type": "VERIFICATION",
                    "entity_id": v.id,
                    "title": f"KYC: {v.document_type}",
                    "artisan_id": v.artisan_id,
                    "artisan_name": v.artisan.full_name if v.artisan else "Artisan",
                    "craft_name": None,
                    "price_inr": None,
                    "status": v.verification_status,
                    "submitted_at": v.created_at.isoformat()
                }
                for v in verifs
            ]
            return items, total

        elif entity_type_upper == "PASSPORT":
            query = (
                select(CraftPassport)
                .options(selectinload(CraftPassport.craft), selectinload(CraftPassport.artisan))
                .where(CraftPassport.status.in_(["SUBMITTED", "UNDER_REVIEW"]))
                .order_by(CraftPassport.issued_at.asc())
            )
            count_q = select(func.count()).select_from(CraftPassport).where(CraftPassport.status.in_(["SUBMITTED", "UNDER_REVIEW"]))
            c_res = await db.execute(count_q)
            total = c_res.scalar() or 0

            res = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
            passports = res.scalars().all()

            items = [
                {
                    "entity_type": "PASSPORT",
                    "entity_id": cp.id,
                    "title": f"Passport: {cp.craft.name if cp.craft else cp.passport_uuid}",
                    "artisan_id": cp.artisan_id,
                    "artisan_name": cp.artisan.full_name if cp.artisan else "Artisan",
                    "craft_name": cp.craft.name if cp.craft else None,
                    "price_inr": None,
                    "status": cp.status,
                    "submitted_at": cp.issued_at.isoformat()
                }
                for cp in passports
            ]
            return items, total

        return [], 0

    @staticmethod
    async def process_decision(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        decision: str,
        reason_category: Optional[str],
        moderator_notes: Optional[str],
        feedback_to_user: Optional[str],
        evidence_reference: Optional[str],
        idempotency_key: Optional[str],
        current_user: User
    ) -> ModerationAction:
        """
        Executes a moderation review decision with strict idempotency and audit trails.
        """
        # 1. Idempotency Check
        if idempotency_key:
            existing_act_res = await db.execute(
                select(ModerationAction).where(ModerationAction.idempotency_key == idempotency_key)
            )
            existing_act = existing_act_res.scalar_one_or_none()
            if existing_act:
                logger.info(f"MODERATION: Returning cached decision for idempotency_key {idempotency_key}")
                return existing_act

        now = datetime.now(timezone.utc)
        entity_type_upper = entity_type.upper()
        decision_upper = decision.upper()

        if entity_type_upper == "PRODUCT":
            p_res = await db.execute(
                select(Product)
                .options(selectinload(Product.craft))
                .where(Product.id == entity_id)
            )
            product = p_res.scalar_one_or_none()
            if not product:
                raise ValueError(f"Product '{entity_id}' not found.")

            prev_status = product.status

            if decision_upper == "APPROVE":
                product.status = "PUBLISHED"
                # MANDATORY CORRECTION: ADMIN_APPROVED != AUTHORITY_VERIFIED
                # Only assign GOVERNMENT_GI_CONFIRMED if explicit authoritative evidence reference is provided!
                if evidence_reference:
                    product.provenance_status = "GOVERNMENT_GI_CONFIRMED"
                else:
                    product.provenance_status = "ADMIN_APPROVED"
            elif decision_upper == "REJECT":
                product.status = "REJECTED"
            elif decision_upper == "REQUEST_CHANGES":
                product.status = "DRAFT"
            else:
                raise ValueError(f"Unsupported decision '{decision}' for Product.")

            new_status = product.status
            product.moderated_by = current_user.id
            product.moderated_at = now
            product.admin_feedback = feedback_to_user or moderator_notes

            # Record ProvenanceEvent for product status change
            await ProvenanceService.record_field_change(
                db=db,
                entity_type="Product",
                entity_id=product.id,
                field_name="status",
                previous_value=prev_status,
                new_value=new_status,
                provenance_state="ADMIN_APPROVED" if decision_upper == "APPROVE" else "ADMIN_REJECTED",
                actor_user=current_user,
                change_reason=f"Moderation decision: {decision_upper}. Reason: {reason_category}",
                evidence_reference=evidence_reference
            )

        elif entity_type_upper == "VERIFICATION":
            v_res = await db.execute(select(Verification).where(Verification.id == entity_id))
            verif = v_res.scalar_one_or_none()
            if not verif:
                raise ValueError(f"Verification '{entity_id}' not found.")

            prev_status = verif.verification_status
            verif.verifier_user_id = current_user.id
            verif.admin_notes = moderator_notes
            verif.decision_date = now

            art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.id == verif.artisan_id))
            artisan = art_res.scalar_one_or_none()

            if decision_upper == "APPROVE":
                # MANDATORY CORRECTION: Check if authoritative evidence is provided!
                if evidence_reference:
                    verif.verification_status = "AUTHORITY_VERIFIED"
                    verif.verified_at = now
                    if artisan:
                        artisan.verification_status = "GOVERNMENT_VERIFIED_GI" if verif.document_type == "GI_AUTHORIZED_USER_CERT" else "AUTHORITY_VERIFIED"
                        artisan.user.is_verified = True if artisan.user else None
                else:
                    verif.verification_status = "ADMIN_REVIEWED"
                    verif.verified_at = now
                    if artisan:
                        artisan.verification_status = "ADMIN_REVIEWED"
            elif decision_upper == "REJECT":
                verif.verification_status = "REJECTED"
                verif.rejection_reason = feedback_to_user or moderator_notes
                if artisan:
                    artisan.verification_status = "REJECTED"
            elif decision_upper == "REQUEST_CHANGES":
                verif.verification_status = "REQUEST_CORRECTION"
                verif.rejection_reason = feedback_to_user

            new_status = verif.verification_status

        else:
            raise ValueError(f"Unsupported entity_type '{entity_type}' for moderation.")

        # Create ModerationAction
        action = ModerationAction(
            entity_type=entity_type_upper,
            entity_id=entity_id,
            previous_status=prev_status,
            new_status=new_status,
            decision=decision_upper,
            moderator_user_id=current_user.id,
            reason_category=reason_category,
            moderator_notes=moderator_notes,
            feedback_to_user=feedback_to_user,
            evidence_reference=evidence_reference,
            idempotency_key=idempotency_key,
            created_at=now
        )
        db.add(action)
        await db.flush()

        # Security AuditLog
        await record_audit_event(
            db=db,
            action=f"MODERATION_ACTION_{decision_upper}",
            entity_type=entity_type_upper,
            entity_id=entity_id,
            actor_user_id=current_user.id,
            payload_after={"decision": decision_upper, "new_status": new_status, "reason": reason_category}
        )

        return action
