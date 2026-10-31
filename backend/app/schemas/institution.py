"""
AttendAI — Institution & Department Schemas
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    address: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None


class InstitutionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None


class InstitutionResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    head_faculty_id: uuid.UUID | None = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
