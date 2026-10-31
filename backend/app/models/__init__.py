"""
AttendAI — Models Package
==========================
Import all models here so Alembic can discover them for migrations.
"""

from app.models.user import User, UserRole
from app.models.institution import Institution, Department
from app.models.course import Course
from app.models.classroom import Classroom, Camera, CameraType, CameraStatus
from app.models.session import ClassSession, SessionStatus
from app.models.face_embedding import FaceEmbedding
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.events import (
    PresenceEvent, PresenceEventType,
    EngagementEvent,
    DeviceEvent, DeviceType,
    DrowsinessEvent, DrowsinessEventType,
    AIAnalysisResult,
)
from app.models.reporting import Report, ReportType, Notification, NotificationType, AuditLog

__all__ = [
    "User", "UserRole",
    "Institution", "Department",
    "Course",
    "Classroom", "Camera", "CameraType", "CameraStatus",
    "ClassSession", "SessionStatus",
    "FaceEmbedding",
    "AttendanceRecord", "AttendanceStatus",
    "PresenceEvent", "PresenceEventType",
    "EngagementEvent",
    "DeviceEvent", "DeviceType",
    "DrowsinessEvent", "DrowsinessEventType",
    "AIAnalysisResult",
    "Report", "ReportType",
    "Notification", "NotificationType",
    "AuditLog",
]
