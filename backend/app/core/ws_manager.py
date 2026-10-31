"""
AttendAI — WebSocket Connection Manager
=========================================
Tracks and manages live WebSocket connections for real-time classroom feeds.
Provides pub/sub fan-out broadcasting to all connected faculty and admin UI clients.
"""

from typing import Dict, List
import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by session_id.
    """

    def __init__(self):
        # Maps session_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept a WebSocket connection and register it to a session group."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info("WebSocket client connected", session_id=session_id, total_clients=len(self.active_connections[session_id]))

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove a disconnected WebSocket from the session group."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info("WebSocket client disconnected", session_id=session_id)

    async def broadcast_to_session(self, session_id: str, message: dict) -> int:
        """
        Broadcast a JSON message dictionary to all active WebSocket clients in a session group.

        Returns:
            Number of clients successfully notified.
        """
        if session_id not in self.active_connections:
            return 0

        dead_sockets = []
        sent_count = 0

        for socket in self.active_connections[session_id]:
            try:
                await socket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send to WebSocket, marking for removal", error=str(e))
                dead_sockets.append(socket)

        for dead in dead_sockets:
            self.disconnect(dead, session_id)

        return sent_count


# Global singleton connection manager
ws_manager = ConnectionManager()
