"""
AttendAI — Class Session Model
================================
A class session is one lecture/lab in a classroom.
The AI pipeline attaches to an active session to stream and analyze video.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Session context
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="RESTRICT"), nullable=False
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    camera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True
    )

    # Timing
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False
    )
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Summary stats (populated at session end)
    total_registered: Mapped[int] = mapped_column(Integer, default=0)
    total_present: Mapped[int] = mapped_column(Integer, default=0)
    total_absent: Mapped[int] = mapped_column(Integer, default=0)
    total_late: Mapped[int] = mapped_column(Integer, default=0)
    avg_engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_device_events: Mapped[int] = mapped_column(Integer, default=0)
    total_drowsiness_events: Mapped[int] = mapped_column(Integer, default=0)

    # Configurable rules for this session (override institution defaults)
    session_config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=lambda: {
        "min_presence_percent": 75,
        "late_grace_minutes": 10,
        "early_departure_minutes": 10,
        "recognition_confidence_threshold": 0.6,
    })

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="sessions")  # noqa: F821
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="sessions")  # noqa: F821
    faculty: Mapped["User"] = relationship("User", foreign_keys=[faculty_id])  # noqa: F821
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(  # noqa: F821
        "AttendanceRecord", back_populates="session", cascade="all, delete-orphan"
    )
    presence_events: Mapped[list["PresenceEvent"]] = relationship(  # noqa: F821
        "PresenceEvent", back_populates="session", cascade="all, delete-orphan"
    )
    engagement_events: Mapped[list["EngagementEvent"]] = relationship(  # noqa: F821
        "EngagementEvent", back_populates="session", cascade="all, delete-orphan"
    )
    device_events: Mapped[list["DeviceEvent"]] = relationship(  # noqa: F821
        "DeviceEvent", back_populates="session", cascade="all, delete-orphan"
    )
    drowsiness_events: Mapped[list["DrowsinessEvent"]] = relationship(  # noqa: F821
        "DrowsinessEvent", back_populates="session", cascade="all, delete-orphan"
    )
    ai_results: Mapped[list["AIAnalysisResult"]] = relationship(  # noqa: F821
        "AIAnalysisResult", back_populates="session", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        "Report", back_populates="session"
    )

    def __repr__(self) -> str:
        return f"<ClassSession {self.id} [{self.status}]>"
