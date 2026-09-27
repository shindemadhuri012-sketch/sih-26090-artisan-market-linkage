"""
SIH 26090: API Health & Startup Tests
Verifies FastAPI service initialization, router mounting, and diagnostic probes.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns application metadata and environment info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "SIH 26090 Artisan Market Linkage"


def test_health_liveness_endpoint():
    """Verify that liveness probe returns status 'ok' and timestamp."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "timestamp" in data
    assert data["components"]["api"] == "healthy"
