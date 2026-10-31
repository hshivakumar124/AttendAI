"""
AttendAI — Attendance & Biometric Enrollment Schemas
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class FaceEnrollmentRequest(BaseModel):
    user_id: uuid.UUID | None = None  # Admin can enroll on behalf of student
    image_base64: str | None = None   # Base64 encoded JPEG/PNG image


class FaceEnrollmentResponse(BaseModel):
    embedding_id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    message: str


class AttendanceMarkRequest(BaseModel):
    session_id: uuid.UUID
    student_id: uuid.UUID
    status: str = Field(default="present")
    confidence: float | None = None
    remarks: str | None = None


class AttendanceRecordResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    status: str
    marked_at: datetime
    confidence_score: float | None = None
    verification_type: str
    model_config = {"from_attributes": True}
