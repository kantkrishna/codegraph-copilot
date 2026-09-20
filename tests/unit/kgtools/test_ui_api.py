# tests/unit/kgtools/test_ui_api.py

# This file contains the unit tests for the UI and Chat REST API endpoints,
# following strict TDD to validate the HTTP orchestration layer.

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure frontend directory and dummy index exist to prevent test fixture failures
# before the frontend/index.html is created in the Green phase.
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend")
os.makedirs(frontend_dir, exist_ok=True)
dummy_index = os.path.join(frontend_dir, "index.html")
if not os.path.exists(dummy_index):
    with open(dummy_index, "w") as f:
        f.write("<html>Test Dummy</html>")

from backend.main import app

client = TestClient(app)

def test_api_chat_endpoint_empty() -> None:
    """US-4.1 AC2: Empty prompt returns 400 Bad Request."""
    response = client.post("/api/v1/chat", json={"prompt": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

@patch("backend.main.run_chat_cycle")
def test_api_chat_endpoint_success(mock_run: MagicMock) -> None:
    """US-4.1 AC1: Valid prompt invokes run_chat_cycle and returns 200."""
    mock_run.return_value = "### Answer\nThe frontend calls checkoutservice."
    
    response = client.post("/api/v1/chat", json={"prompt": "What calls checkout?"})
    
    assert response.status_code == 200
    assert response.json() == {"response": "### Answer\nThe frontend calls checkoutservice."}
    mock_run.assert_called_once()
    assert mock_run.call_args[0][0] == "What calls checkout?"

@patch("backend.main.run_chat_cycle")
def test_api_chat_endpoint_exception(mock_run: MagicMock) -> None:
    """Test US-4.1 Edge Case: Graph or orchestration failures yield a 500."""
    mock_run.side_effect = ValueError("Database connection lost")
    
    response = client.post("/api/v1/chat", json={"prompt": "Hello"})
    
    assert response.status_code == 500
    assert "Database connection lost" in response.json()["detail"]

def test_static_index_served() -> None:
    """US-4.2 AC1: GET / serves index.html successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()