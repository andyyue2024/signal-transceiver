"""
Tests for admin UI routes.
"""
from fastapi.testclient import TestClient

from src.main import app


def test_admin_ui_home():
    """Admin UI home returns HTML."""
    client = TestClient(app)
    response = client.get("/admin/ui")
    assert response.status_code == 200
    assert "Signal Transceiver Admin" in response.text


def test_admin_ui_health():
    """Admin UI health endpoint works."""
    client = TestClient(app)
    response = client.get("/admin/ui/health")
    assert response.status_code == 200
    assert "Admin UI" in response.text
