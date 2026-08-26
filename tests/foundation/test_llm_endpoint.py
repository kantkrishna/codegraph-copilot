# tests/foundation/test_llm_endpoint.py

# This file contains the unit tests for the basic LLM test endpoint,
# validating success paths, empty prompts, and upstream API errors.

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import httpx
import openai
import pytest

from backend.main import app

client = TestClient(app)

# Helper to generate a mock httpx.Response for openai errors
def _mock_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return httpx.Response(status_code=status_code, request=request)

def test_llm_test_endpoint_empty_prompt() -> None:
    """Assert POSTing an empty prompt returns a 400 Bad Request."""
    response = client.post("/api/v1/chat/test", json={"prompt": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

# FIXED: Patching backend.main.call_llm instead of backend.llm.call_llm
@patch("backend.main.call_llm")
def test_llm_test_endpoint_success(mock_call_llm: MagicMock) -> None:
    """Assert the endpoint returns 200 and matches the mocked string on success."""
    mock_call_llm.return_value = "Mocked LLM response."
    response = client.post("/api/v1/chat/test", json={"prompt": "Hello"})
    
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked LLM response."}
    mock_call_llm.assert_called_once_with("Hello")

# FIXED: Patching backend.main.call_llm
@patch("backend.main.call_llm")
def test_llm_test_endpoint_auth_failure(mock_call_llm: MagicMock) -> None:
    """Assert auth exceptions yield a 502 with a clean error message."""
    mock_call_llm.side_effect = openai.AuthenticationError(
        message="Invalid API Key", 
        response=_mock_response(401), 
        body=None
    )
    response = client.post("/api/v1/chat/test", json={"prompt": "Hello"})
    
    assert response.status_code == 502
    assert "upstream authentication failure" in response.json()["detail"].lower()

# FIXED: Patching backend.main.call_llm
@patch("backend.main.call_llm")
def test_llm_test_endpoint_timeout(mock_call_llm: MagicMock) -> None:
    """Assert timeout exceptions yield a 504 Gateway Timeout."""
    mock_call_llm.side_effect = openai.APITimeoutError(request=_mock_response(408).request) # type: ignore
    response = client.post("/api/v1/chat/test", json={"prompt": "Hello"})
    
    assert response.status_code == 504
    assert "timeout" in response.json()["detail"].lower()