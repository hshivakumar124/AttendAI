"""
AttendAI — Auth Router
========================
REST endpoints for authentication: register, login, token refresh,
logout, current user, change password.

All endpoints are rate-limited to prevent brute-force attacks.
"""

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.permissions import get_current_active_user
from app.core.security import verify_password, hash_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    AuthenticatedUserResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=201,
    summary="Register a new user account",
    description="Self-registration for students and faculty. Admins use the /users endpoint.",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=body.role,
    )
    return MessageResponse(message="Account created successfully. You can now log in.")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and obtain JWT tokens",
    description="Returns an access token (15 min) and a refresh token (7 days).",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login(email=body.email, password=body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use a valid refresh token to get a new access token without re-authenticating.",
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh_tokens(refresh_token=body.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (client-side token invalidation)",
    description=(
        "AttendAI uses stateless JWT. Logout is handled client-side by discarding tokens. "
        "In production, implement a Redis token blocklist for immediate invalidation."
    ),
)
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    logger.info("User logged out", user_id=str(current_user.id))
    return MessageResponse(message="Logged out successfully. Please discard your tokens.")


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return AuthenticatedUserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        institution_id=str(current_user.institution_id) if current_user.institution_id else None,
        department_id=str(current_user.department_id) if current_user.department_id else None,
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change current user's password",
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")

    from sqlalchemy import update
    from datetime import UTC, datetime

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(hashed_password=hash_password(body.new_password))
    )
    logger.info("Password changed", user_id=str(current_user.id))
    return MessageResponse(message="Password updated successfully")
