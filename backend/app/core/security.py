"""
AttendAI — Security Core
==========================
JWT token creation, validation, and password hashing.
Access tokens: 15 min. Refresh tokens: 7 days (stored in httpOnly cookie).
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ─── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token Creation ───────────────────────────────────────────────────────

def create_access_token(
    subject: str | UUID,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID as string)
        role: UserRole string (e.g., "faculty", "student")
        extra_claims: Optional additional JWT claims

    Returns:
        Encoded JWT string
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str | UUID) -> str:
    """
    Create a long-lived JWT refresh token.
    Only contains subject — no role or sensitive info.
    """
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ─── JWT Token Validation ─────────────────────────────────────────────────────

class TokenData:
    """Decoded and validated JWT token payload."""

    def __init__(self, user_id: str, role: str, token_type: str):
        self.user_id = user_id
        self.role = role
        self.token_type = token_type


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT access token.

    Raises:
        JWTError: if token is invalid, expired, or wrong type
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

    if payload.get("type") != "access":
        raise JWTError("Invalid token type — expected access token")

    user_id: str | None = payload.get("sub")
    role: str | None = payload.get("role")

    if not user_id or not role:
        raise JWTError("Token missing required claims")

    return TokenData(user_id=user_id, role=role, token_type="access")


def decode_refresh_token(token: str) -> str:
    """
    Decode and validate a JWT refresh token.

    Returns:
        user_id (str)

    Raises:
        JWTError: if token is invalid, expired, or wrong type
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type — expected refresh token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise JWTError("Refresh token missing subject")

    return user_id
