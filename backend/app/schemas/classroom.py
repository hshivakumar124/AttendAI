"""
AttendAI — Classroom, Camera, Course & Session Schemas
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Course ───────────────────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    department_id: uuid.UUID
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    credits: int = Field(default=3, ge=1, le=10)
    semester: str | None = None
    academic_year: str | None = None


class CourseResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    code: str
    name: str
    credits: int
    semester: str | None = None
    model_config = {"from_attributes": True}


# ─── Classroom ────────────────────────────────────────────────────────────────
class ClassroomCreate(BaseModel):
    institution_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    code: str | None = None
    building: str | None = None
    floor: str | None = None
    capacity: int = Field(default=60, ge=1)
    description: str | None = None


class ClassroomUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    building: str | None = None
    floor: str | None = None


class ClassroomResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    code: str | None = None
    building: str | None = None
    floor: str | None = None
    capacity: int
    model_config = {"from_attributes": True}


# ─── Camera ───────────────────────────────────────────────────────────────────
class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    camera_type: str = "webcam"
    stream_url: str | None = None
    device_index: int | None = 0
    local_video_path: str | None = None
    is_primary: bool = True
    config: dict | None = None


class CameraResponse(BaseModel):
    id: uuid.UUID
    classroom_id: uuid.UUID
    name: str
    camera_type: str
    stream_url: str | None = None
    device_index: int | None = None
    status: str
    is_primary: bool
    model_config = {"from_attributes": True}


# ─── Session ──────────────────────────────────────────────────────────────────
class SessionCreate(BaseModel):
    course_id: uuid.UUID
    classroom_id: uuid.UUID
    camera_id: uuid.UUID | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    topic: str | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    classroom_id: uuid.UUID
    faculty_id: uuid.UUID
    status: str
    scheduled_start: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    topic: str | None = None
    total_present: int
    total_registered: int
    avg_engagement_score: float | None = None
    model_config = {"from_attributes": True}


class SessionStartResponse(BaseModel):
    session_id: str
    status: str
    actual_start: datetime
    message: str
