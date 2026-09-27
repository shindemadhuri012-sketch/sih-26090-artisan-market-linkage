"""
SIH 26090: Verification Workflow API Endpoints
Provides KYC/document submission for artisans and audited review workflows for administrators.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.permissions import require_roles
from backend.app.models.auth import User
from backend.app.models.artisan import ArtisanProfile, Verification
from backend.app.models.craft import CraftPassport
from backend.app.schemas.verification import (
    VerificationSubmitRequest,
    VerificationReviewRequest,
    VerificationResponse
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/verifications", tags=["Verifications"])


@router.post("/submit", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_verification_document(
    payload: VerificationSubmitRequest,
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Artisan submits official identification or craft credentials for review."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artisan profile required prior to submitting verification."
        )

    verification = Verification(
        artisan_id=artisan.id,
        document_type=payload.document_type,
        document_url=payload.document_url,
        verification_status="SUBMITTED"
    )
    db.add(verification)
    await db.flush()
    await db.refresh(verification)

    # Move any DRAFT or SUBMITTED passports to UNDER_REVIEW
    await db.execute(
        update(CraftPassport)
        .where(
            CraftPassport.artisan_id == artisan.id,
            CraftPassport.status.in_(["DRAFT", "SUBMITTED"])
        )
        .values(status="UNDER_REVIEW")
    )

    await record_audit_event(
        db=db,
        action="VERIFICATION_SUBMITTED",
        entity_type="Verification",
        entity_id=verification.id,
        actor_user_id=current_user.id,
        payload_after={"document_type": payload.document_type}
    )

    return VerificationResponse(
        id=verification.id,
        artisan_id=verification.artisan_id,
        verifier_user_id=verification.verifier_user_id,
        document_type=verification.document_type,
        document_url=verification.document_url,
        verification_status=verification.verification_status,
        rejection_reason=verification.rejection_reason,
        admin_notes=verification.admin_notes,
        decision_date=verification.decision_date.isoformat() if verification.decision_date else None,
        verified_at=verification.verified_at.isoformat() if verification.verified_at else None,
        created_at=verification.created_at.isoformat() if verification.created_at else ""
    )


@router.get("/my", response_model=List[VerificationResponse])
async def list_my_verifications(
    current_user: User = Depends(require_roles(["artisan"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Lists verification history for the authenticated artisan."""
    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.user_id == current_user.id))
    artisan = art_res.scalar_one_or_none()
    if not artisan:
        return []

    query = select(Verification).where(Verification.artisan_id == artisan.id).order_by(Verification.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return [
        VerificationResponse(
            id=v.id,
            artisan_id=v.artisan_id,
            verifier_user_id=v.verifier_user_id,
            document_type=v.document_type,
            document_url=v.document_url,
            verification_status=v.verification_status,
            rejection_reason=v.rejection_reason,
            admin_notes=v.admin_notes,
            decision_date=v.decision_date.isoformat() if v.decision_date else None,
            verified_at=v.verified_at.isoformat() if v.verified_at else None,
            created_at=v.created_at.isoformat()
        )
        for v in items
    ]


@router.get("/admin/pending", response_model=List[VerificationResponse])
async def list_pending_verifications(
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Administrator view: lists all verification submissions pending review."""
    query = (
        select(Verification)
        .where(Verification.verification_status.in_(["SUBMITTED", "UNDER_REVIEW"]))
        .order_by(Verification.created_at.asc())
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return [
        VerificationResponse(
            id=v.id,
            artisan_id=v.artisan_id,
            verifier_user_id=v.verifier_user_id,
            document_type=v.document_type,
            document_url=v.document_url,
            verification_status=v.verification_status,
            rejection_reason=v.rejection_reason,
            admin_notes=v.admin_notes,
            decision_date=v.decision_date.isoformat() if v.decision_date else None,
            verified_at=v.verified_at.isoformat() if v.verified_at else None,
            created_at=v.created_at.isoformat()
        )
        for v in items
    ]


@router.post("/admin/{verification_id}/review", response_model=VerificationResponse)
async def review_verification_submission(
    verification_id: str,
    payload: VerificationReviewRequest,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Administrator action: APPROVE, REJECT, or REQUEST_CORRECTION for an artisan's credentials.
    Creates an immutable audit event and updates associated profile and passport states.
    """
    query = select(Verification).where(Verification.id == verification_id)
    result = await db.execute(query)
    verif = result.scalar_one_or_none()

    if not verif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification submission not found.")

    now = datetime.now(timezone.utc)
    verif.verifier_user_id = current_user.id
    verif.admin_notes = payload.admin_notes
    verif.decision_date = now

    art_res = await db.execute(select(ArtisanProfile).where(ArtisanProfile.id == verif.artisan_id))
    artisan = art_res.scalar_one_or_none()

    if payload.decision == "APPROVE":
        verif.verification_status = "VERIFIED_APPROVED"
        verif.verified_at = now
        has_auth_reference = bool(getattr(payload, "authoritative_registry_reference", None))
        is_gi_cert = verif.document_type == "GI_AUTHORIZED_USER_CERT"

        if is_gi_cert or has_auth_reference:
            v_level = "GOVERNMENT_VERIFIED_GI" if is_gi_cert else "AUTHORITY_VERIFIED"
        else:
            v_level = "ADMIN_REVIEWED"

        if artisan:
            artisan.verification_status = v_level
            # Update User is_verified flag
            await db.execute(update(User).where(User.id == artisan.user_id).values(is_verified=True))
        # Update associated passports
        await db.execute(
            update(CraftPassport)
            .where(CraftPassport.artisan_id == verif.artisan_id)
            .values(status="VERIFIED", verification_level=v_level)
        )

    elif payload.decision == "REJECT":
        verif.verification_status = "REJECTED"
        verif.rejection_reason = payload.rejection_reason or "Verification criteria not met."
        if artisan:
            artisan.verification_status = "REJECTED"
        # Mark associated passports REJECTED
        await db.execute(
            update(CraftPassport)
            .where(CraftPassport.artisan_id == verif.artisan_id)
            .values(status="REJECTED")
        )

    elif payload.decision == "REQUEST_CORRECTION":
        verif.verification_status = "REQUEST_CORRECTION"
        verif.rejection_reason = payload.rejection_reason

    await record_audit_event(
        db=db,
        action=f"VERIFICATION_DECISION_{payload.decision}",
        entity_type="Verification",
        entity_id=verif.id,
        actor_user_id=current_user.id,
        payload_after={"decision": payload.decision, "notes": payload.admin_notes}
    )

    return VerificationResponse(
        id=verif.id,
        artisan_id=verif.artisan_id,
        verifier_user_id=verif.verifier_user_id,
        document_type=verif.document_type,
        document_url=verif.document_url,
        verification_status=verif.verification_status,
        rejection_reason=verif.rejection_reason,
        admin_notes=verif.admin_notes,
        decision_date=verif.decision_date.isoformat(),
        verified_at=verif.verified_at.isoformat() if verif.verified_at else None,
        created_at=verif.created_at.isoformat()
    )
