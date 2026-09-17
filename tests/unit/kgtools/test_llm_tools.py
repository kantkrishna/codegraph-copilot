# tests/unit/kgtools/test_llm_tools.py

# This file tests the orchestration and LLM tool-calling binding logic.

from unittest.mock import MagicMock, patch
from backend.orchestrator import run_chat_cycle
from backend.kgtools.tool_schemas import KG_TOOLS

def test_llm_tool_binding() -> None:
    """Test US-2.4 Scenario 1 (Part A): Assert tool schemas are correctly formatted."""
    assert len(KG_TOOLS) == 4
    tool_names = [tool["function"]["name"] for tool in KG_TOOLS]
    assert "find_entity" in tool_names
    assert "get_relationships" in tool_names
    assert "find_dependencies" in tool_names
    assert "find_dependents" in tool_names

@patch("backend.orchestrator.client.chat.completions.create")
def test_llm_invokes_correct_tool(mock_create: MagicMock) -> None:
    """Test US-2.4 Scenario 1 (Part B): LLM outputs structured tool call request."""
    mock_function = MagicMock()
    mock_function.name = "find_entity"
    mock_function.arguments = '{"name": "PaymentService"}'

    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function

    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    
    mock_final_response = MagicMock()
    mock_final_response.choices = [MagicMock(message=MagicMock(content="PaymentService found.", tool_calls=None))]
    
    mock_create.side_effect = [mock_response, mock_final_response]
    
    mock_kg_client = MagicMock()
    mock_kg_client.search_entity.return_value = {"id": "ent_1", "name": "PaymentService"}

    final_answer = run_chat_cycle("Find PaymentService", mock_kg_client)
    
    assert "PaymentService found." in final_answer
    mock_kg_client.search_entity.assert_called_once_with("PaymentService")

@patch("backend.orchestrator.client.chat.completions.create")
def test_orchestrator_returns_tool_data_to_llm(mock_create: MagicMock) -> None:
    """Test US-2.4 Scenario 2: Handling Tool Responses and passing them back."""
    mock_function = MagicMock()
    mock_function.name = "find_dependencies"
    mock_function.arguments = '{"entity_id": "ent_1"}'

    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_99"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function

    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=mock_message)]
    
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(content="It depends on Database.", tool_calls=None))]
    
    mock_create.side_effect = [mock_response_1, mock_response_2]
    
    mock_kg_client = MagicMock()
    mock_kg_client.fetch_relationships.return_value = [{"target_id": "ent_db"}]

    run_chat_cycle("What does it depend on?", mock_kg_client)

    second_call_args = mock_create.call_args_list[1][1]
    messages = second_call_args["messages"]
    
    assert messages[-1]["role"] == "tool"
    assert messages[-1]["tool_call_id"] == "call_99"
    assert "ent_db" in messages[-1]["content"]