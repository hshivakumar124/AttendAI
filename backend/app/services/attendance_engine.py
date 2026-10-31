"""
AttendAI — Physical Attendance Aggregation Engine
===================================================
Evaluates student presence events collected over a session duration.
Calculates final physical attendance status based on observable presence signals.

Rules:
- PRESENT: Presence % >= threshold (default 75%) AND arrived within late_threshold (default 15 min).
- LATE: Presence % >= threshold BUT arrived after late_threshold.
- PARTIAL: 25% <= Presence % < threshold.
- ABSENT: Presence % < 25% or not detected.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import structlog

try:
    from app.models.attendance import AttendanceStatus
except ImportError:
    from backend.app.models.attendance import AttendanceStatus

logger = structlog.get_logger(__name__)


class AttendanceEngine:
    """
    Physical Attendance Rule Evaluator.

    Takes raw presence duration & timestamps and calculates official attendance status.
    Reconciles registered course roster vs detected students to classify Present and Absent students.
    """

    def __init__(
        self,
        presence_percentage_threshold: float = 75.0,
        late_threshold_minutes: float = 15.0,
        partial_min_threshold: float = 25.0,
    ):
        self.presence_threshold = presence_percentage_threshold
        self.late_threshold = late_threshold_minutes
        self.partial_min_threshold = partial_min_threshold

    def calculate_status(
        self,
        session_start: datetime,
        session_end: datetime,
        first_detected_at: Optional[datetime],
        last_detected_at: Optional[datetime],
        total_presence_minutes: float,
    ) -> Dict[str, any]:
        """
        Calculate physical attendance status and percentage metrics.

        Returns:
            Dict with status, presence_percentage, presence_duration_minutes
        """
        session_duration = (session_end - session_start).total_seconds() / 60.0
        if session_duration <= 0:
            session_duration = 60.0  # Fallback 1 hour default if timestamps invalid

        # Cap presence duration at session_duration
        presence_duration = min(total_presence_minutes, session_duration)
        presence_percentage = round((presence_duration / session_duration) * 100.0, 2)

        if not first_detected_at or presence_percentage < self.partial_min_threshold:
            return {
                "status": AttendanceStatus.ABSENT,
                "presence_percentage": presence_percentage,
                "presence_duration_minutes": round(presence_duration, 2),
            }

        # Check arrival delay
        arrival_delay_minutes = (first_detected_at - session_start).total_seconds() / 60.0

        if presence_percentage >= self.presence_threshold:
            if arrival_delay_minutes > self.late_threshold:
                final_status = AttendanceStatus.LATE
            else:
                final_status = AttendanceStatus.PRESENT
        else:
            final_status = AttendanceStatus.PARTIAL

        return {
            "status": final_status,
            "presence_percentage": presence_percentage,
            "presence_duration_minutes": round(presence_duration, 2),
            "arrival_delay_minutes": round(max(0.0, arrival_delay_minutes), 2),
        }

    def reconcile_session_roster(
        self,
        registered_students: List[Dict[str, str]],
        detected_student_ids: Dict[str, Dict[str, any]],
    ) -> Dict[str, any]:
        """
        Reconciles registered course roster vs detected presence during a session.
        Determines who is PRESENT, LATE, or ABSENT.

        Args:
            registered_students: List of dicts [{"student_id": "...", "name": "...", "roll_no": "..."}]
            detected_student_ids: Dict mapping student_id -> presence stats dict

        Returns:
            Full reconciled class attendance breakdown including absent students list.
        """
        roster_results = []
        present_count = 0
        absent_count = 0
        late_count = 0

        for s in registered_students:
            sid = s["student_id"]
            name = s.get("name", "Student")
            roll_no = s.get("roll_no", sid)

            if sid in detected_student_ids:
                d_info = detected_student_ids[sid]
                status = d_info.get("status", AttendanceStatus.PRESENT)
                presence_pct = d_info.get("presence_percentage", 95.0)
                engagement = d_info.get("engagement_score", 85.0)
                device_mins = d_info.get("device_minutes", 0.0)
                drowsy_mins = d_info.get("drowsy_minutes", 0.0)

                if status == AttendanceStatus.LATE:
                    late_count += 1
                present_count += 1

                roster_results.append({
                    "student_id": sid,
                    "name": name,
                    "roll_no": roll_no,
                    "status": "PRESENT" if status != AttendanceStatus.LATE else "LATE",
                    "presence_percentage": presence_pct,
                    "engagement_score": engagement,
                    "device_minutes": device_mins,
                    "drowsy_minutes": drowsy_mins,
                })
            else:
                absent_count += 1
                roster_results.append({
                    "student_id": sid,
                    "name": name,
                    "roll_no": roll_no,
                    "status": "ABSENT",
                    "presence_percentage": 0.0,
                    "engagement_score": 0.0,
                    "device_minutes": 0.0,
                    "drowsy_minutes": 0.0,
                })

        total_registered = len(registered_students)
        avg_engagement = (
            round(sum(r["engagement_score"] for r in roster_results if r["status"] != "ABSENT") / max(1, present_count), 2)
            if present_count > 0
            else 0.0
        )

        return {
            "registered_count": total_registered,
            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "average_engagement": avg_engagement,
            "roster": roster_results,
        }
