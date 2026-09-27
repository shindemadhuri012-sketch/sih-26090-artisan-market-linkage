"""
SIH 26090: Authentication API Endpoints
Implements Argon2id authentication, JWT issuance, refresh-token rotation with reuse detection,
passwordless OTP challenges, and audit logging.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_async_db
from backend.app.core.permissions import get_current_active_user
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_secure_token,
    hash_token,
    generate_numeric_otp
)
from backend.app.models.auth import User, RefreshTokenSession, OTPChallenge
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    OTPRequestPayload,
    OTPVerifyPayload,
    UserResponse
)
from backend.app.services.audit_service import record_audit_event
from backend.app.core.telemetry import logger

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Registers a new Artisan or Buyer account with Argon2id password hashing."""
    # Check if phone number is already registered
    existing_phone = await db.execute(select(User).where(User.phone_number == payload.phone_number))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this phone number is already registered."
        )

    # Check if email is already registered (if provided)
    if payload.email:
        existing_email = await db.execute(select(User).where(User.email == payload.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address is already registered."
            )

    new_user = User(
        phone_number=payload.phone_number,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        preferred_language=payload.preferred_language,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    await db.flush()

    await record_audit_event(
        db=db,
        action="USER_REGISTRATION",
        entity_type="User",
        entity_id=new_user.id,
        actor_user_id=new_user.id,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent"),
        payload_after={"phone": payload.phone_number, "role": payload.role}
    )

    return UserResponse(
        id=new_user.id,
        phone_number=new_user.phone_number,
        email=new_user.email,
        role=new_user.role,
        preferred_language=new_user.preferred_language,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        created_at=new_user.created_at.isoformat() if new_user.created_at else datetime.now(timezone.utc).isoformat()
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Authenticates credentials, generates JWT access token, and establishes a revocable refresh token session."""
    ident = payload.login_identifier.strip()
    query = select(User).where((User.phone_number == ident) | (User.email == ident))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        await record_audit_event(
            db=db,
            action="LOGIN_FAILED",
            entity_type="User",
            entity_id=ident,
            ip_address=request.client.host if request.client else "127.0.0.1",
            user_agent=request.headers.get("user-agent"),
            payload_after={"identifier": ident}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your phone/email and password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is disabled. Please contact platform administration."
        )

    # 1. Issue Access Token
    access_token = create_access_token(user_id=user.id, role=user.role)

    # 2. Issue Refresh Token and establish Session
    raw_refresh_token = generate_secure_token(48)
    token_family = generate_secure_token(16)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session_entry = RefreshTokenSession(
        user_id=user.id,
        token_hash=hash_token(raw_refresh_token),
        token_family=token_family,
        is_revoked=False,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    db.add(session_entry)

    await record_audit_event(
        db=db,
        action="LOGIN_SUCCESS",
        entity_type="User",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent"),
        payload_after={"role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        role=user.role
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Rotates refresh token. Detects token reuse: if a previously rotated/revoked token
    is presented, all tokens in the token family are revoked to defend against theft.
    """
    token_hashed = hash_token(payload.refresh_token)
    query = select(RefreshTokenSession).where(RefreshTokenSession.token_hash == token_hashed)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token."
        )

    # TOKEN REUSE DETECTION DEFENSE:
    if session.is_revoked:
        # Invalidate entire token family immediately
        logger.warning(f"SECURITY ALERT: Refresh token reuse detected for family {session.token_family}. Revoking all sessions!")
        await db.execute(
            update(RefreshTokenSession)
            .where(RefreshTokenSession.token_family == session.token_family)
            .values(is_revoked=True)
        )
        await record_audit_event(
            db=db,
            action="TOKEN_REUSE_DETECTED",
            entity_type="RefreshTokenSession",
            entity_id=session.id,
            actor_user_id=session.user_id,
            ip_address=request.client.host if request.client else "127.0.0.1",
            user_agent=request.headers.get("user-agent"),
            payload_after={"token_family": session.token_family}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compromised session detected. Please log in again."
        )

    now = datetime.now(timezone.utc)
    session_expiry = session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else session.expires_at
    if session_expiry < now:
        session.is_revoked = True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again."
        )

    # 1. Fetch user to confirm active status
    user_res = await db.execute(select(User).where(User.id == session.user_id))
    user = user_res.scalar_one_or_none()
    if not user or not user.is_active:
        session.is_revoked = True
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account disabled.")

    # 2. Invalidate current token
    session.is_revoked = True

    # 3. Issue rotated refresh token under the same token family
    new_raw_refresh = generate_secure_token(48)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_session = RefreshTokenSession(
        user_id=user.id,
        token_hash=hash_token(new_raw_refresh),
        token_family=session.token_family,
        is_revoked=False,
        expires_at=new_expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    db.add(new_session)

    # 4. Issue fresh Access Token
    new_access_token = create_access_token(user_id=user.id, role=user.role)

    await record_audit_event(
        db=db,
        action="TOKEN_ROTATION_SUCCESS",
        entity_type="RefreshTokenSession",
        entity_id=new_session.id,
        actor_user_id=user.id,
        ip_address=request.client.host if request.client else "127.0.0.1",
        payload_after={"token_family": session.token_family}
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        role=user.role
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Revokes the active refresh token session."""
    token_hashed = hash_token(payload.refresh_token)
    query = select(RefreshTokenSession).where(RefreshTokenSession.token_hash == token_hashed)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if session:
        session.is_revoked = True
        await record_audit_event(
            db=db,
            action="LOGOUT",
            entity_type="RefreshTokenSession",
            entity_id=session.id,
            actor_user_id=session.user_id,
            ip_address=request.client.host if request.client else "127.0.0.1"
        )

    return {"message": "Successfully logged out and session revoked."}


@router.post("/otp/request")
async def request_otp(
    payload: OTPRequestPayload,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generates a secure numeric OTP challenge for passwordless artisan authentication.
    In development mode, returns dev_otp_code in response to allow automated testing.
    """
    otp_code = generate_numeric_otp(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    challenge = OTPChallenge(
        phone_number=payload.phone_number,
        otp_code_hash=hash_token(otp_code),
        attempts=0,
        max_attempts=3,
        is_consumed=False,
        expires_at=expires_at
    )
    db.add(challenge)
    await db.flush()

    await record_audit_event(
        db=db,
        action="OTP_REQUESTED",
        entity_type="OTPChallenge",
        entity_id=challenge.id,
        ip_address=request.client.host if request.client else "127.0.0.1",
        payload_after={"phone": payload.phone_number}
    )

    response_data = {
        "message": "OTP challenge generated successfully. Code expires in 5 minutes.",
        "phone_number": payload.phone_number
    }

    # Isolated testing facility for development environments:
    if settings.APP_ENV == "development":
        response_data["dev_otp_code"] = otp_code
        response_data["dev_note"] = "Exposed only in development mode for automated testing."

    return response_data


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(
    payload: OTPVerifyPayload,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Verifies an OTP challenge. If valid, retrieves or provisions the user account,
    marks the OTP as consumed, and issues authentication tokens.
    """
    now = datetime.now(timezone.utc)
    query = (
        select(OTPChallenge)
        .where(
            OTPChallenge.phone_number == payload.phone_number,
            OTPChallenge.is_consumed == False
        )
        .order_by(OTPChallenge.created_at.desc())
    )
    result = await db.execute(query)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP challenge found. Please request a new OTP."
        )

    challenge_expiry = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge.expires_at.tzinfo is None else challenge.expires_at
    if challenge_expiry < now:
        challenge.is_consumed = True
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired. Please request a new OTP."
        )

    if challenge.attempts >= challenge.max_attempts:
        challenge.is_consumed = True
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum OTP verification attempts exceeded. Please request a new OTP."
        )

    expected_hash = hash_token(payload.otp_code)
    if challenge.otp_code_hash != expected_hash:
        challenge.attempts += 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check and try again."
        )

    # Mark challenge consumed
    challenge.is_consumed = True

    # Find or provision user
    user_query = select(User).where(User.phone_number == payload.phone_number)
    user_res = await db.execute(user_query)
    user = user_res.scalar_one_or_none()

    if not user:
        # Auto-provision new artisan account on first OTP verification
        user = User(
            phone_number=payload.phone_number,
            password_hash=hash_password(generate_secure_token(24)),
            role="artisan",
            preferred_language="en",
            is_active=True,
            is_verified=False
        )
        db.add(user)
        await db.flush()

    # Issue tokens
    access_token = create_access_token(user_id=user.id, role=user.role)
    raw_refresh = generate_secure_token(48)
    token_family = generate_secure_token(16)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session_entry = RefreshTokenSession(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        token_family=token_family,
        is_revoked=False,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    db.add(session_entry)

    await record_audit_event(
        db=db,
        action="OTP_LOGIN_SUCCESS",
        entity_type="User",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        role=user.role
    )


@router.get("/me", response_model=UserResponse)
async def get_my_user_profile(current_user: User = Depends(get_current_active_user)):
    """Returns authenticated user account identity."""
    return UserResponse(
        id=current_user.id,
        phone_number=current_user.phone_number,
        email=current_user.email,
        role=current_user.role,
        preferred_language=current_user.preferred_language,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat()
    )
