"""
AttendAI — Event Storage & Query Service
==========================================
Persists real-time presence events to PostgreSQL presence_events table and provides filtering.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import PresenceEvent, PresenceEventType

logger = structlog.get_logger(__name__)


class EventService:
    """
    Manages PresenceEvent persistence and querying in PostgreSQL.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(
        self,
        event_type: str,
        session_id: uuid.UUID,
        student_id: Optional[uuid.UUID] = None,
        tracking_id: Optional[int] = None,
        confidence: Optional[float] = None,
        bbox: Optional[Dict] = None,
    ) -> PresenceEvent:
        """
        Record and persist a new presence event to PostgreSQL.
        """
        event = PresenceEvent(
            session_id=session_id,
            student_id=student_id,
            tracking_id=tracking_id,
            event_type=PresenceEventType(event_type),
            confidence=confidence,
            bbox=bbox,
            timestamp=datetime.now(UTC),
        )
        self.db.add(event)
        await self.db.flush()
        logger.info("Presence event stored in DB", event_id=str(event.id), type=event_type, session=str(session_id))
        return event

    async def list_session_events(
        self,
        session_id: uuid.UUID,
        event_type: Optional[str] = None,
        student_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[PresenceEvent]:
        """
        Retrieve presence events for a session with optional filtering.
        """
        query = select(PresenceEvent).where(PresenceEvent.session_id == session_id)

        if event_type:
            query = query.where(PresenceEvent.event_type == PresenceEventType(event_type))
        if student_id:
            query = query.where(PresenceEvent.student_id == student_id)

        query = query.order_by(PresenceEvent.timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
