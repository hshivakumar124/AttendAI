"""
AttendAI — Attendance Record Model
=====================================
One record per student per session.
Final attendance status is calculated from presence events, not single frames.
Manual override by authorized faculty is supported with full audit trail.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EARLY_DEPARTURE = "early_departure"
    PARTIAL = "partial"          # Was present but didn't meet threshold
    UNCERTAIN = "uncertain"      # Low-confidence recognition
    UNKNOWN = "unknown"          # Not in registered student list


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Attendance outcome
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), default=AttendanceStatus.ABSENT, nullable=False
    )
    # Presence details
    first_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    presence_duration_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    presence_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # AI-estimated engagement
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    head_pose_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    eye_state_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_visibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Recognition quality
    avg_recognition_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_recognition_events: Mapped[int] = mapped_column(Integer, default=0)

    # Manual override support
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    session: Mapped["ClassSession"] = relationship(  # noqa: F821
        "ClassSession", back_populates="attendance_records"
    )
    student: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="attendance_records", foreign_keys=[student_id]
    )

    def __repr__(self) -> str:
        return f"<Attendance session={self.session_id} student={self.student_id} [{self.status}]>"
