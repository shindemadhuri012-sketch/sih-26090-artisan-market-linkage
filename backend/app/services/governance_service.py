"""
SIH 26090: Governance Service
Manages neutral administrative review signals, data quality flags,
anomaly detection, and factual governance dashboard metrics.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.governance import GovernanceFlag
from backend.app.models.auth import User
from backend.app.models.product import Product
from backend.app.models.artisan import Verification, ArtisanProfile
from backend.app.models.craft import CraftPassport
from backend.app.models.ai_studio import AIProductSuggestion
from backend.app.services.audit_service import record_audit_event
from backend.app.core.telemetry import logger


class GovernanceService:
    """Service handling governance flags and factual platform metrics."""

    @staticmethod
    async def raise_flag(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        flag_type: str,
        severity: str = "MEDIUM",
        details_json: Optional[Dict[str, Any]] = None,
        flagged_by_user: Optional[User] = None
    ) -> GovernanceFlag:
        """
        Creates or updates a neutral review signal on an entity.
        Prevents duplicate open flags of the same type on the same entity.
        """
        existing_res = await db.execute(
            select(GovernanceFlag)
            .where(
                GovernanceFlag.entity_type == entity_type,
                GovernanceFlag.entity_id == entity_id,
                GovernanceFlag.flag_type == flag_type,
                GovernanceFlag.status.in_(["OPEN", "UNDER_INVESTIGATION"])
            )
        )
        existing_flag = existing_res.scalar_one_or_none()

        if existing_flag:
            # Update details if new details provided
            if details_json:
                existing_flag.details_json = {**existing_flag.details_json, **details_json}
            return existing_flag

        flag = GovernanceFlag(
            entity_type=entity_type,
            entity_id=entity_id,
            flag_type=flag_type,
            severity=severity.upper(),
            status="OPEN",
            details_json=details_json or {},
            flagged_by_user_id=flagged_by_user.id if flagged_by_user else None
        )
        db.add(flag)
        await db.flush()

        logger.info(f"GOVERNANCE_FLAG: Raised {flag_type} ({severity}) on {entity_type}:{entity_id}")
        return flag

    @staticmethod
    async def resolve_flag(
        db: AsyncSession,
        flag_id: str,
        decision: str,
        resolution_notes: str,
        current_user: User
    ) -> GovernanceFlag:
        """
        Resolves an open review signal with an explicit moderator explanation.
        """
        res = await db.execute(select(GovernanceFlag).where(GovernanceFlag.id == flag_id))
        flag = res.scalar_one_or_none()

        if not flag:
            raise ValueError(f"GovernanceFlag with ID '{flag_id}' not found.")

        now = datetime.now(timezone.utc)
        flag.status = decision.upper()
        flag.resolution_notes = resolution_notes
        flag.resolved_by_user_id = current_user.id
        flag.resolved_at = now

        await record_audit_event(
            db=db,
            action="GOVERNANCE_FLAG_RESOLVED",
            entity_type="GovernanceFlag",
            entity_id=flag.id,
            actor_user_id=current_user.id,
            payload_after={"decision": flag.status, "notes": resolution_notes}
        )

        return flag

    @staticmethod
    async def list_flags(
        db: AsyncSession,
        entity_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GovernanceFlag], int]:
        """Returns paginated list of governance flags."""
        query = select(GovernanceFlag)
        conditions = []

        if entity_type:
            conditions.append(GovernanceFlag.entity_type == entity_type)
        if severity:
            conditions.append(GovernanceFlag.severity == severity.upper())
        if status:
            conditions.append(GovernanceFlag.status == status.upper())

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_q = select(func.count()).select_from(query.subquery())
        c_res = await db.execute(count_q)
        total = c_res.scalar() or 0

        # Paginate
        query = query.order_by(GovernanceFlag.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items_res = await db.execute(query)
        items = list(items_res.scalars().all())

        return items, total

    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> Dict[str, Any]:
        """
        Computes factual governance metrics.
        Never outputs synthetic or ungrounded trust scores.
        """
        # 1. Pending product reviews
        p_res = await db.execute(
            select(func.count()).select_from(Product).where(Product.status == "PENDING_REVIEW")
        )
        pending_products = p_res.scalar() or 0

        # 2. Pending verifications
        v_res = await db.execute(
            select(func.count()).select_from(Verification).where(Verification.verification_status.in_(["SUBMITTED", "UNDER_REVIEW"]))
        )
        pending_verifications = v_res.scalar() or 0

        # 3. Pending passports
        cp_res = await db.execute(
            select(func.count()).select_from(CraftPassport).where(CraftPassport.status.in_(["SUBMITTED", "UNDER_REVIEW"]))
        )
        pending_passports = cp_res.scalar() or 0

        # 4. Open flags by severity
        flags_q = await db.execute(
            select(GovernanceFlag.severity, func.count(GovernanceFlag.id))
            .where(GovernanceFlag.status.in_(["OPEN", "UNDER_INVESTIGATION"]))
            .group_by(GovernanceFlag.severity)
        )
        severity_counts = dict(flags_q.all())
        open_flags_total = sum(severity_counts.values())

        # 5. Staged AI suggestions awaiting human confirmation
        ai_res = await db.execute(
            select(func.count()).select_from(AIProductSuggestion).where(AIProductSuggestion.status == "AI_SUGGESTED")
        )
        ai_suggestions_pending = ai_res.scalar() or 0

        # 6. Active demo records
        demo_res = await db.execute(
            select(func.count()).select_from(Product).where(Product.is_sample_or_demo.is_(True))
        )
        demo_records_active = demo_res.scalar() or 0

        return {
            "pending_product_reviews": pending_products,
            "pending_verification_reviews": pending_verifications,
            "pending_passport_reviews": pending_passports,
            "open_flags_total": open_flags_total,
            "open_flags_by_severity": {
                "HIGH": severity_counts.get("HIGH", 0),
                "MEDIUM": severity_counts.get("MEDIUM", 0),
                "LOW": severity_counts.get("LOW", 0)
            },
            "ai_suggestions_awaiting_review": ai_suggestions_pending,
            "active_demo_records_count": demo_records_active
        }
