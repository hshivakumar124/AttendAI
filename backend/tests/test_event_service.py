"""
AttendAI — PresenceEvent Database Persistence Tests
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import PresenceEvent, PresenceEventType
from app.services.event_service import EventService


@pytest.mark.asyncio
async def test_record_and_list_presence_events():
    from tests.conftest import AsyncTestingSessionLocal

    async with AsyncTestingSessionLocal() as db:
        service = EventService(db)
        session_id = uuid.uuid4()
        student_id = uuid.uuid4()

        # Record recognized event
        event1 = await service.record_event(
            event_type="recognized",
            session_id=session_id,
            student_id=student_id,
            tracking_id=1,
            confidence=0.95,
            bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 200},
        )
        assert event1.id is not None
        assert event1.event_type == PresenceEventType.RECOGNIZED
        assert event1.confidence == 0.95

        # Record lost event
        event2 = await service.record_event(
            event_type="lost",
            session_id=session_id,
            student_id=student_id,
            tracking_id=1,
            confidence=0.0,
        )
        assert event2.id is not None

        # Query all session events
        events = await service.list_session_events(session_id=session_id)
        assert len(events) == 2

        # Query filtered by type
        rec_events = await service.list_session_events(
            session_id=session_id, event_type="recognized"
        )
        assert len(rec_events) == 1
        assert rec_events[0].event_type == PresenceEventType.RECOGNIZED
