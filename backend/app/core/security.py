"""
SIH 26090: Security, Cryptography & Token Management
Provides Argon2id password hashing, JWT creation & verification, and secure token generators.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from backend.app.core.config import settings
from backend.app.core.telemetry import logger

# Initialize Argon2id password hasher with recommended RFC 9106 parameters
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16
)

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


def hash_token(token: str) -> str:
    """Generates SHA-256 hash of a refresh token or OTP code for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generates cryptographically strong random URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_numeric_otp(digits: int = 6) -> str:
    """Generates cryptographically random numeric OTP code."""
    lower_bound = 10 ** (digits - 1)
    upper_bound = (10 ** digits) - 1
    return str(secrets.randbelow(upper_bound - lower_bound + 1) + lower_bound)


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates signed, short-lived JWT access token containing subject, role, and jti."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16)
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Access token signature expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid access token: {e}")
        return None
