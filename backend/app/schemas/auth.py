"""
AttendAI — Auth Schemas
========================
Pydantic v2 schemas for all authentication request/response payloads.
Passwords are validated for strength. Emails are normalized.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Request Schemas ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(default="student")   # Default role for self-registration

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_self_register = {"student", "faculty"}
        if v not in allowed_self_register:
            raise ValueError(f"Self-registration only allowed for roles: {allowed_self_register}")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ─── Response Schemas ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int           # seconds until access token expiry


class AuthenticatedUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    institution_id: str | None = None
    department_id: str | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: AuthenticatedUserResponse


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
    success: bool = True
