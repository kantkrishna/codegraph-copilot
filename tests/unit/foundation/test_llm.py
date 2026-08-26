# tests/unit/foundation/test_llm.py

# This file contains the unit tests for the LLM client wrapper.

import pytest
from unittest.mock import MagicMock, patch
from backend.llm import call_llm

@patch("backend.llm.client.chat.completions.create")
def test_call_llm_success(mock_create) -> None:
    """Test that call_llm successfully parses a valid LLM response."""
    # Arrange: Mock the deeply nested OpenAI response object
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Mocked LLM response"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    mock_create.return_value = mock_response

    # Act
    result = call_llm("Explain the architecture.")

    # Assert
    assert result == "Mocked LLM response"
    mock_create.assert_called_once()


@patch("backend.llm.client.chat.completions.create")
def test_call_llm_empty_response(mock_create) -> None:
    """Test that call_llm handles an empty/None response gracefully."""
    # Arrange: Mock a response where content is None
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = None
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    mock_create.return_value = mock_response

    # Act
    result = call_llm("Say nothing.")

    # Assert
    assert result == ""
    mock_create.assert_called_once()