"""
AttendAI — Analytics & CSV Export Unit Tests
"""

import uuid
import pytest
from datetime import datetime, UTC

from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.session import ClassSession, SessionStatus
from app.services.reporting_service import ReportingService


@pytest.mark.asyncio
async def test_reporting_service_summary_and_csv():
    from tests.conftest import AsyncTestingSessionLocal

    async with AsyncTestingSessionLocal() as db:
        service = ReportingService(db)

        # Create session
        session = ClassSession(
            id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            classroom_id=uuid.uuid4(),
            faculty_id=uuid.uuid4(),
            topic="CS-401 Test Session",
            status=SessionStatus.COMPLETED,
            actual_start=datetime.now(UTC),
        )
        db.add(session)
        await db.flush()

        # Add attendance records
        rec1 = AttendanceRecord(
            session_id=session.id,
            student_id=uuid.uuid4(),
            status=AttendanceStatus.PRESENT,
            engagement_score=90.0,
        )
        rec2 = AttendanceRecord(
            session_id=session.id,
            student_id=uuid.uuid4(),
            status=AttendanceStatus.ABSENT,
            engagement_score=0.0,
        )
        db.add_all([rec1, rec2])
        await db.flush()

        # Test JSON summary aggregation
        summary = await service.get_session_summary(session.id)
        assert summary["total_enrolled"] == 2
        assert summary["present_count"] == 1
        assert summary["absent_count"] == 1
        assert summary["attendance_rate_percent"] == 50.0

        # Test CSV export content
        csv_text = await service.generate_attendance_csv(session.id)
        assert "Attendance ID" in csv_text
        assert "Student ID" in csv_text
        assert "present" in csv_text
        assert "absent" in csv_text
