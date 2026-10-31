"""
AttendAI — WebSocket Connection & Broadcast Tests
"""

import pytest
from app.core.ws_manager import ConnectionManager
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_connection_manager_basic_lifecycle():
    manager = ConnectionManager()
    session_id = "session_test_100"

    assert session_id not in manager.active_connections

    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []

        async def accept(self):
            pass

        async def send_json(self, data):
            self.sent_messages.append(data)

    mock_ws = MockWebSocket()
    await manager.connect(mock_ws, session_id)
    assert len(manager.active_connections[session_id]) == 1

    # Broadcast message
    count = await manager.broadcast_to_session(session_id, {"type": "test", "data": "hello"})
    assert count == 1
    assert len(mock_ws.sent_messages) == 1
    assert mock_ws.sent_messages[0]["data"] == "hello"

    # Disconnect
    manager.disconnect(mock_ws, session_id)
    assert session_id not in manager.active_connections


def test_websocket_auth_rejects_missing_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/sessions/test_session"):
            pass


def test_websocket_auth_accepts_valid_token(client):
    token = create_access_token(subject="user_123", role="faculty")
    # Connect with valid JWT query token
    with client.websocket_connect(f"/api/v1/ws/sessions/test_session?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["session_id"] == "test_session"
