"""
AttendAI — Backend Health Test
================================
Verifies the FastAPI app can be imported and core configuration loads.
"""

import pytest
from fastapi.testclient import TestClient


def test_app_imports():
    """Verify main app can be imported without errors."""
    from main import app
    assert app is not None


def test_settings_load():
    """Verify settings load from environment."""
    from app.config import settings
    assert settings.app_name == "AttendAI"
    assert settings.app_version is not None


def test_health_endpoint():
    """Verify health check returns 200."""
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "AttendAI"


def test_api_v1_ping():
    """Verify API v1 ping endpoint."""
    from main import app
    client = TestClient(app)
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
