"""
AttendAI — Real-Time Event Publisher
======================================
Publishes structured real-time AI events (presence, drowsiness alerts,
device distractions, engagement updates) to Redis Pub/Sub channels.

Channels:
- attendai:events:session:{session_id} (All session events)
- attendai:events:alerts:{session_id}  (High/Critical severity alerts)
"""

import json
import time
import uuid
from typing import Any, Dict, Optional

import structlog

from ai_service.config.ai_config import ai_settings

logger = structlog.get_logger(__name__)


class EventPublisher:
    """
    Asynchronous Redis Event Publisher.
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or ai_settings.redis_url
        self._redis_client = None

    async def connect(self) -> bool:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self._redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self._redis_client.ping()
            logger.info("Connected to Redis for event publishing", url=self.redis_url)
            return True
        except Exception as e:
            logger.warning("Redis connection failed — event publishing disabled in offline mode", error=str(e))
            self._redis_client = None
            return False

    async def publish_event(
        self,
        event_type: str,
        session_id: str,
        student_id: Optional[str] = None,
        track_id: Optional[str] = None,
        severity: str = "info",  # "info", "warning", "critical"
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Publish a structured event to Redis.

        Returns:
            Dict representing the event payload.
        """
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "session_id": session_id,
            "student_id": student_id,
            "track_id": track_id,
            "severity": severity,
            "confidence_score": round(confidence_score, 4) if confidence_score else None,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        channel_all = f"attendai:events:session:{session_id}"
        channel_alerts = f"attendai:events:alerts:{session_id}"

        if self._redis_client:
            try:
                payload_json = json.dumps(event_payload)
                await self._redis_client.publish(channel_all, payload_json)
                if severity in ("warning", "critical"):
                    await self._redis_client.publish(channel_alerts, payload_json)
                logger.debug("Event published to Redis", event_type=event_type, session_id=session_id)
            except Exception as e:
                logger.warning("Failed to publish event to Redis", error=str(e))

        return event_payload

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
