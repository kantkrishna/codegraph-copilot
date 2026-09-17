# tests/foundation/test_main.py

# This file contains the unit tests for the main FastAPI application skeleton,
# specifically testing health checks and basic routing.

from fastapi.testclient import TestClient

# We will create backend.main in the Green phase
from backend.main import app

client = TestClient(app)


def test_health_endpoint_returns_200_and_payload() -> None:
    """Assert GET /health yields status code 200 and matches {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unhandled_route_returns_404() -> None:
    """Assert GET /invalid-route returns a standard 404 response."""
    response = client.get("/invalid-route")
    assert response.status_code == 404
