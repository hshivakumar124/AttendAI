"""
AttendAI — EventPublisher Tests
"""

import pytest
from ai_service.events.event_publisher import EventPublisher


@pytest.mark.asyncio
async def test_event_publisher_payload_structure():
    publisher = EventPublisher(redis_url="redis://localhost:6379")

    payload = await publisher.publish_event(
        event_type="drowsiness_alert",
        session_id="test_session_123",
        student_id="student_456",
        track_id="track_1",
        severity="critical",
        confidence_score=0.92,
        metadata={"closed_frames": 25},
    )

    assert isinstance(payload, dict)
    assert payload["event_type"] == "drowsiness_alert"
    assert payload["session_id"] == "test_session_123"
    assert payload["student_id"] == "student_456"
    assert payload["severity"] == "critical"
    assert payload["confidence_score"] == 0.92
    assert payload["metadata"]["closed_frames"] == 25
    assert "event_id" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_event_publisher_connect_disconnect():
    publisher = EventPublisher()
    # Connect will gracefully return False if Redis is not running locally (non-fatal)
    res = await publisher.connect()
    assert isinstance(res, bool)
    await publisher.disconnect()
