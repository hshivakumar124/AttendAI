"""
AttendAI — WebSocket Gateway Router
====================================
Real-time WebSocket endpoint for classroom session live feeds.

Endpoint: /ws/sessions/{session_id}?token={jwt_access_token}
Authenticates token, subscribes to Redis Pub/Sub, and streams events to client.
"""

import asyncio
import json
import uuid

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.config import settings
from app.core.security import decode_access_token
from app.core.ws_manager import ws_manager
from app.utils.redis_client import get_redis_client

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.websocket("/sessions/{session_id}")
async def websocket_session_feed(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None),
):
    """
    Real-time WebSocket feed for a classroom session.
    Requires a valid JWT access token passed via query parameter `?token=...`.
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        # Validate JWT token
        token_data = decode_access_token(token)
    except JWTError as e:
        logger.warning("WebSocket authentication failed", error=str(e))
        await websocket.close(code=4008, reason="Invalid or expired token")
        return

    # Accept & register connection
    await ws_manager.connect(websocket, session_id)

    # Subscribe to Redis Pub/Sub channel for this session
    channel_name = f"attendai:events:session:{session_id}"
    redis_client = None
    pubsub = None

    try:
        redis_client = await get_redis_client()
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_name)

        # Welcome message
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "user_id": token_data.user_id,
            "message": "Connected to AttendAI Real-Time Event Stream 🚀",
        })

        async def listen_redis():
            """Listen to Redis channel and forward to WebSocket."""
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception:
                            pass
                    await websocket.send_json(data)

        async def listen_client():
            """Listen to incoming client messages (e.g. ping/pong)."""
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        # Run listener tasks concurrently until disconnect
        await asyncio.gather(
            listen_redis(),
            listen_client(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally", session_id=session_id)
    except Exception as e:
        logger.warning("WebSocket error encountered", error=str(e))
    finally:
        ws_manager.disconnect(websocket, session_id)
        if pubsub:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
            except Exception:
                pass
