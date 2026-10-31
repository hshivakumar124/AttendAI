"""
AttendAI — AttendanceEngine Rules Tests
"""

from datetime import datetime, timedelta
from app.models.attendance import AttendanceStatus
from app.services.attendance_engine import AttendanceEngine


def test_attendance_status_present():
    engine = AttendanceEngine(presence_percentage_threshold=75.0, late_threshold_minutes=15.0)
    session_start = datetime(2026, 7, 23, 9, 0, 0)
    session_end = datetime(2026, 7, 23, 10, 0, 0)  # 60 min session

    # Student present for 50 min (83.3%), arrived at 9:05 (5 min delay)
    result = engine.calculate_status(
        session_start=session_start,
        session_end=session_end,
        first_detected_at=session_start + timedelta(minutes=5),
        last_detected_at=session_end,
        total_presence_minutes=50.0,
    )
    assert result["status"] == AttendanceStatus.PRESENT
    assert result["presence_percentage"] == 83.33


def test_attendance_status_late():
    engine = AttendanceEngine(presence_percentage_threshold=75.0, late_threshold_minutes=15.0)
    session_start = datetime(2026, 7, 23, 9, 0, 0)
    session_end = datetime(2026, 7, 23, 10, 0, 0)

    # Student present for 48 min (80%), but arrived at 9:18 (18 min late > 15 min threshold)
    result = engine.calculate_status(
        session_start=session_start,
        session_end=session_end,
        first_detected_at=session_start + timedelta(minutes=18),
        last_detected_at=session_end,
        total_presence_minutes=48.0,
    )
    assert result["status"] == AttendanceStatus.LATE


def test_attendance_status_partial():
    engine = AttendanceEngine(presence_percentage_threshold=75.0)
    session_start = datetime(2026, 7, 23, 9, 0, 0)
    session_end = datetime(2026, 7, 23, 10, 0, 0)

    # Student present for 30 min (50% — between 25% and 75%)
    result = engine.calculate_status(
        session_start=session_start,
        session_end=session_end,
        first_detected_at=session_start,
        last_detected_at=session_start + timedelta(minutes=30),
        total_presence_minutes=30.0,
    )
    assert result["status"] == AttendanceStatus.PARTIAL


def test_attendance_status_absent():
    engine = AttendanceEngine(presence_percentage_threshold=75.0, partial_min_threshold=25.0)
    session_start = datetime(2026, 7, 23, 9, 0, 0)
    session_end = datetime(2026, 7, 23, 10, 0, 0)

    # Student present for only 10 min (16.6% < 25% minimum)
    result = engine.calculate_status(
        session_start=session_start,
        session_end=session_end,
        first_detected_at=session_start,
        last_detected_at=session_start + timedelta(minutes=10),
        total_presence_minutes=10.0,
    )
    assert result["status"] == AttendanceStatus.ABSENT
