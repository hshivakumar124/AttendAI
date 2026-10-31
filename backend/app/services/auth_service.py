"""
AttendAI — Auth Service
========================
Business logic for authentication: register, login, token refresh, logout.
Separated from the route layer for testability and reuse.
"""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginResponse, AuthenticatedUserResponse, TokenResponse

logger = structlog.get_logger(__name__)


class AuthService:
    """Handles all authentication business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "student",
        institution_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> User:
        """
        Register a new user account.

        Raises:
            ConflictException: if email is already registered
        """
        # Check for existing user
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        if result.scalar_one_or_none():
            raise ConflictException(f"Email '{email}' is already registered")

        user = User(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=full_name.strip(),
            role=UserRole(role),
            institution_id=institution_id,
            department_id=department_id,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # Get generated ID without committing

        logger.info("New user registered", user_id=str(user.id), email=user.email, role=role)
        return user

    async def login(self, email: str, password: str) -> LoginResponse:
        """
        Authenticate a user and issue JWT tokens.

        Raises:
            UnauthorizedException: if credentials are invalid or account inactive
        """
        # Fetch user (always run verify_password even on miss to prevent timing attacks)
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated. Contact your administrator.")

        # Update last login timestamp
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=datetime.now(UTC))
        )

        # Issue tokens
        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id)

        logger.info("User logged in", user_id=str(user.id), role=user.role.value)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            user=AuthenticatedUserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                institution_id=str(user.institution_id) if user.institution_id else None,
                department_id=str(user.department_id) if user.department_id else None,
            ),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new access token using a valid refresh token.

        Raises:
            UnauthorizedException: if refresh token is invalid or user not found
        """
        from jose import JWTError

        try:
            user_id_str = decode_refresh_token(refresh_token)
        except JWTError as e:
            raise UnauthorizedException(f"Invalid or expired refresh token: {e}")

        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id_str), User.is_active == True)  # noqa: E712
        )
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("User not found or account is inactive")

        new_access_token = create_access_token(subject=user.id, role=user.role.value)
        logger.info("Access token refreshed", user_id=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )
