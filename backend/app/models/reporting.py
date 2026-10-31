"""
AttendAI — Report, Notification & Audit Log Models
=====================================================
Report: AI-generated end-of-class report stored as JSON + optional file.
Notification: In-app notifications for users.
AuditLog: Immutable log of all security-sensitive actions.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ─── Report ───────────────────────────────────────────────────────────────────

class ReportType(str, enum.Enum):
    SESSION_SUMMARY = "session_summary"
    ATTENDANCE = "attendance"
    ENGAGEMENT = "engagement"
    FULL_CLASS = "full_class"
    STUDENT_PERSONAL = "student_personal"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)       # Full report data
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # PDF/Excel path
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="reports")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Report {self.report_type} session={self.session_id}>"


# ─── Notification ─────────────────────────────────────────────────────────────

class NotificationType(str, enum.Enum):
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    ATTENDANCE_MARKED = "attendance_marked"
    DROWSINESS_ALERT = "drowsiness_alert"
    DEVICE_ALERT = "device_alert"
    REPORT_READY = "report_ready"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="SET NULL"), nullable=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Notification [{self.notification_type}] user={self.user_id} read={self.is_read}>"


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable audit trail of all security-sensitive actions.
    Records are NEVER updated or deleted.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)   # IPv6 max
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user={self.user_id} at {self.timestamp}>"
