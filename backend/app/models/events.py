"""
AttendAI — AI Event Models
============================
PresenceEvent: tracks each detection/absence event for a student in a session.
EngagementEvent: time-windowed engagement signal per student per session.
DeviceEvent: mobile/laptop/tablet detection events.
DrowsinessEvent: possible drowsiness detection events.
AIAnalysisResult: per-frame aggregate AI processing stats.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ─── Presence Events ──────────────────────────────────────────────────────────

class PresenceEventType(str, enum.Enum):
    DETECTED = "detected"
    RECOGNIZED = "recognized"
    LOST = "lost"
    REAPPEARED = "reappeared"
    UNKNOWN = "unknown"
    LOW_CONFIDENCE = "low_confidence"


class PresenceEvent(Base):
    __tablename__ = "presence_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tracking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ByteTrack ID
    event_type: Mapped[PresenceEventType] = mapped_column(Enum(PresenceEventType), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {x,y,w,h}
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="presence_events")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PresenceEvent {self.event_type} student={self.student_id} t={self.timestamp}>"


# ─── Engagement Events ────────────────────────────────────────────────────────

class EngagementEvent(Base):
    __tablename__ = "engagement_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tracking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Engagement sub-scores (each 0.0–1.0)
    head_pose_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    eye_state_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_visibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    looking_away_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Composite score (0.0–100.0)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Window metadata
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="engagement_events")  # noqa: F821

    def __repr__(self) -> str:
        return f"<EngagementEvent student={self.student_id} score={self.composite_score:.1f}>"


# ─── Device Events ────────────────────────────────────────────────────────────

class DeviceType(str, enum.Enum):
    MOBILE_PHONE = "mobile_phone"
    TABLET = "tablet"
    LAPTOP = "laptop"
    OTHER_DEVICE = "other_device"


class DeviceEvent(Base):
    __tablename__ = "device_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tracking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType), nullable=False)
    detection_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="device_events")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DeviceEvent {self.device_type} student={self.student_id} dur={self.duration_seconds}s>"


# ─── Drowsiness Events ────────────────────────────────────────────────────────

class DrowsinessEventType(str, enum.Enum):
    POSSIBLE_DROWSINESS = "possible_drowsiness"
    PROLONGED_EYE_CLOSURE = "prolonged_eye_closure"
    HEAD_DROP = "head_drop"


class DrowsinessEvent(Base):
    __tablename__ = "drowsiness_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tracking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[DrowsinessEventType] = mapped_column(Enum(DrowsinessEventType), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Eye Aspect Ratio values
    ear_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    ear_min: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="drowsiness_events")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DrowsinessEvent {self.event_type} student={self.student_id}>"


# ─── AI Analysis Results (per-frame aggregate) ────────────────────────────────

class AIAnalysisResult(Base):
    """
    Stores lightweight per-frame aggregate stats from the AI pipeline.
    NOT storing raw frame data — only processed aggregate signals.
    """
    __tablename__ = "ai_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    num_faces_detected: Mapped[int] = mapped_column(Integer, default=0)
    num_recognized: Mapped[int] = mapped_column(Integer, default=0)
    num_unknown: Mapped[int] = mapped_column(Integer, default=0)
    avg_engagement: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    possible_drowsiness_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_used: Mapped[bool | None] = mapped_column(nullable=True)

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="ai_results")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AIResult session={self.session_id} faces={self.num_faces_detected} t={self.frame_timestamp}>"
