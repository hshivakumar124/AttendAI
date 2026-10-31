"""
AttendAI — RBAC Permissions
=============================
Role-based access control via FastAPI dependency injection.
Every protected endpoint declares its required role(s) via `require_roles(...)`.

Usage:
    @router.get("/admin-only")
    async def admin_endpoint(
        current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN))
    ):
        ...
"""

from collections.abc import Callable
from functools import wraps
from uuid import UUID

import structlog
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

logger = structlog.get_logger(__name__)

# HTTP Bearer scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Current User Dependency ──────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT Bearer token,
    then loads and returns the corresponding User from the database.

    Raises:
        UnauthorizedException: if token is missing, invalid, or expired
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("No authentication token provided")

    token = credentials.credentials
    try:
        token_data = decode_access_token(token)
    except JWTError as e:
        raise UnauthorizedException(f"Invalid or expired token: {e}")

    # Load user from DB
    result = await db.execute(
        select(User).where(User.id == UUID(token_data.user_id), User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found or account is inactive")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures the authenticated user account is active."""
    if not current_user.is_active:
        raise UnauthorizedException("Account is deactivated")
    return current_user


# ─── Role-Based Access Dependency Factory ─────────────────────────────────────

def require_roles(*roles: UserRole) -> Callable:
    """
    Returns a FastAPI dependency that requires the current user to have
    one of the specified roles.

    Example:
        Depends(require_roles(UserRole.FACULTY, UserRole.ADMIN))
    """
    async def _check_role(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Role '{current_user.role}' is not authorized for this action. "
                f"Required: {[r.value for r in roles]}"
            )
        return current_user

    return _check_role


# ─── Convenience Dependencies ─────────────────────────────────────────────────

def require_super_admin() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN)


def require_admin_or_above() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)


def require_faculty_or_above() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FACULTY)


def require_any_authenticated() -> Callable:
    """Requires any authenticated user (any role)."""
    return require_roles(*list(UserRole))
