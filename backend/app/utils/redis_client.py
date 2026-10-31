"""
AttendAI — Redis Client
========================
Async Redis client with connection pooling.
Used for: WebSocket pub/sub, event queuing, caching, session store.
"""

from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """
    Returns a shared Redis client instance.
    Creates the connection on first call.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close the Redis connection pool on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
