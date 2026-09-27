"""
SIH 26090: RBAC & Object-Level Authorization Guards
Provides FastAPI dependencies for user authentication, role-based access control,
and object-level ownership checks (IDOR defenses).
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_async_db
from backend.app.core.security import decode_access_token
from backend.app.models.auth import User

# Optional Bearer token security scheme for OpenAPI documentation
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Extracts and verifies JWT from Bearer Authorization header.
    Returns the authenticated User or raises 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not auth_header or not auth_header.credentials:
        raise credentials_exception

    token = auth_header.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifies that the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled."
        )
    return current_user


def require_roles(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that current user role belongs to the allowed_roles list.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, your role is '{current_user.role}'."
            )
        return current_user

    return role_checker


def check_object_ownership(current_user: User, resource_owner_id: str, resource_name: str = "resource"):
    """
    Object-Level Authorization Guard (Defense against Insecure Direct Object Reference - IDOR).
    Grants access if the current user is an Admin or is the direct owner of the resource.
    """
    if current_user.role == "admin":
        return True

    if str(current_user.id) != str(resource_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You do not own this {resource_name}."
        )
    return True
