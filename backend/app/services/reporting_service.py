"""
AttendAI — Reporting & Analytics Service
=========================================
Generates CSV and JSON attendance & engagement analytics reports for class sessions.
"""

import csv
import io
import uuid
from typing import Any, Dict

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.events import PresenceEvent
from app.models.session import ClassSession

logger = structlog.get_logger(__name__)


class ReportingService:
    """
    Service for session analytics aggregation and CSV report generation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_summary(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """
        Aggregate session-level attendance & engagement analytics summary.
        """
        session = await self.db.get(ClassSession, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Fetch attendance records
        query = select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)
        res = await self.db.execute(query)
        records = res.scalars().all()

        total_students = len(records)
        present_count = sum(1 for r in records if r.status and r.status.value in ("present", "late"))
        absent_count = sum(1 for r in records if r.status and r.status.value == "absent")
        late_count = sum(1 for r in records if r.status and r.status.value == "late")

        attendance_rate = (present_count / total_students * 100.0) if total_students > 0 else 0.0

        # Average engagement score calculation
        eng_scores = [r.engagement_score for r in records if r.engagement_score is not None]
        avg_engagement = (sum(eng_scores) / len(eng_scores)) if eng_scores else 85.0

        return {
            "session_id": str(session_id),
            "session_topic": session.topic or "Untitled Session",
            "session_status": session.status.value if session.status else "completed",
            "total_enrolled": total_students,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "attendance_rate_percent": round(attendance_rate, 2),
            "avg_engagement_score": round(avg_engagement, 2),
            "start_time": session.actual_start.isoformat() if session.actual_start else None,
            "end_time": session.actual_end.isoformat() if session.actual_end else None,
        }

    async def generate_attendance_csv(self, session_id: uuid.UUID) -> str:
        """
        Generate CSV content string containing student attendance & engagement details.
        """
        query = select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)
        res = await self.db.execute(query)
        records = res.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header Row
        writer.writerow([
            "Attendance ID",
            "Student ID",
            "Status",
            "First Detected Time",
            "Presence Duration Minutes",
            "Visual Engagement Score",
            "Manual Override",
        ])

        for r in records:
            writer.writerow([
                str(r.id),
                str(r.student_id) if r.student_id else "Unassigned",
                r.status.value if r.status else "ABSENT",
                r.first_detected_at.isoformat() if r.first_detected_at else "N/A",
                r.presence_duration_minutes or 0.0,
                f"{r.engagement_score:.1f}%" if r.engagement_score else "N/A",
                "Yes" if r.is_manual_override else "No",
            ])

        return output.getvalue()
