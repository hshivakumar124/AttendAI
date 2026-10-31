"""
AttendAI — User Schemas
========================
Pydantic schemas for user management endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Admin-created user (can set any role)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: str
    institution_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    consent_biometric: bool
    institution_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    created_at: datetime
    last_login: datetime | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
