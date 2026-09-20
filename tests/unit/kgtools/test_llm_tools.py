# tests/unit/kgtools/test_llm_tools.py

# This file tests the orchestration, multi-tool routing, and LLM tool-calling binding logic.

from unittest.mock import MagicMock, patch
from backend.orchestrator import run_chat_cycle, SYSTEM_PROMPT, execute_tool_call
from backend.kgtools.tool_schemas import KG_TOOLS
from backend.kgtools.client import RAGClient

class MockRAGClient(RAGClient):
    def search_documents(self, query: str, top_k: int = 5, filters: dict = None) -> list:
        return []

def test_llm_tool_binding() -> None:
    assert len(KG_TOOLS) == 5
    tool_names = [tool["function"]["name"] for tool in KG_TOOLS]
    assert "hybrid_search" in tool_names

@patch("backend.orchestrator.client.chat.completions.create")
def test_orchestrator_routes_to_rag(mock_create: MagicMock) -> None:
    """Test US-3.2 Scenario 2: Orchestrator safely handles hybrid_search calls."""
    # Correct mock attribute setting
    mock_function = MagicMock()
    mock_function.name = "hybrid_search"
    mock_function.arguments = '{"query": "password hashing"}'
    
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_rag"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function
    
    mock_message = MagicMock(content=None, tool_calls=[mock_tool_call])
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=mock_message)]
    
    mock_final = MagicMock()
    mock_final.choices = [MagicMock(message=MagicMock(content="Hashing uses bcrypt.", tool_calls=None))]
    
    mock_create.side_effect = [mock_response_1, mock_final]
    
    mock_rag = MagicMock()
    mock_rag.search_documents.return_value = [{"snippet": "bcrypt used"}]
    
    final_answer = run_chat_cycle("How does hashing work?", MagicMock(), mock_rag)
    
    assert "bcrypt" in final_answer
    mock_rag.search_documents.assert_called_once_with("password hashing", 5, None)

@patch("backend.orchestrator.client.chat.completions.create")
def test_orchestrator_handles_parallel_calls(mock_create: MagicMock) -> None:
    """Test US-3.2 Scenario 3: Orchestrator executes multiple parallel tool requests."""
    func1 = MagicMock()
    func1.name = "find_entity"
    func1.arguments = '{"name": "App"}'
    call_1 = MagicMock(id="c1", type="function", function=func1)
    
    func2 = MagicMock()
    func2.name = "hybrid_search"
    func2.arguments = '{"query": "App"}'
    call_2 = MagicMock(id="c2", type="function", function=func2)
    
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(content=None, tool_calls=[call_1, call_2]))]
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(content="Done", tool_calls=None))]
    
    mock_create.side_effect = [mock_response_1, mock_response_2]
    
    mock_kg, mock_rag = MagicMock(), MagicMock()
    run_chat_cycle("App", mock_kg, mock_rag)
    
    mock_kg.search_entity.assert_called_once()
    mock_rag.search_documents.assert_called_once()

def test_system_prompt_rules() -> None:
    """Test US-3.3 formatting requirements are enforced in system prompt."""
    assert "### Answer" in SYSTEM_PROMPT
    assert "### Evidence" in SYSTEM_PROMPT
    assert "I could not establish this from the indexed code and documentation." in SYSTEM_PROMPT

@patch("backend.orchestrator.client.chat.completions.create")
def test_response_filters_cot(mock_create: MagicMock) -> None:
    """Test US-3.3 Scenario 3: Chain-of-thought blocks are stripped."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(
        content="<thought>Thinking...</thought>\n### Answer\nYes.", 
        tool_calls=None
    ))]
    mock_create.return_value = mock_response
    
    result = run_chat_cycle("Q?", MagicMock(), MockRAGClient())
    assert "<thought>" not in result
    assert "Thinking..." not in result
    assert "### Answer" in result

@patch("backend.orchestrator.client.chat.completions.create")
def test_orchestrator_handles_invalid_json(mock_create: MagicMock) -> None:
    """Test JSONDecodeError branch when LLM outputs bad JSON arguments."""
    func = MagicMock()
    func.name = "find_entity"
    func.arguments = '{"name": "App", BAD_JSON}'
    call_1 = MagicMock(id="c1", type="function", function=func)
    
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(content=None, tool_calls=[call_1]))]
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(content="Recovered", tool_calls=None))]
    mock_create.side_effect = [mock_response_1, mock_response_2]
    
    mock_kg = MagicMock()
    # It should fallback to args = {} causing find_entity("", kg_client)
    run_chat_cycle("App", mock_kg, MockRAGClient())
    mock_kg.search_entity.assert_called_once_with("")

def test_execute_tool_call_exception() -> None:
    """Test the blanket Exception block in execute_tool_call."""
    mock_kg = MagicMock()
    mock_kg.search_entity.side_effect = Exception("DB Crash")
    
    result = execute_tool_call("find_entity", {"name": "Test"}, mock_kg, MockRAGClient())
    assert "DB Crash" in result
    assert "error" in result

def test_execute_tool_call_all_branches() -> None:
    """Explicitly test all branches of execute_tool_call to maximize coverage."""
    mock_kg, mock_rag = MagicMock(), MagicMock()
    
    # 1. get_relationships
    mock_kg.fetch_relationships.return_value = [{"target_id": "test_rel"}]
    res_rel = execute_tool_call("get_relationships", {"entity_id": "123", "direction": "inbound"}, mock_kg, mock_rag)
    assert "test_rel" in res_rel
    
    # 2. find_dependencies
    mock_kg.fetch_relationships.return_value = [{"target_id": "test_down"}]
    res_dep = execute_tool_call("find_dependencies", {"entity_id": "123"}, mock_kg, mock_rag)
    assert "test_down" in res_dep
    
    # 3. find_dependents
    mock_kg.fetch_relationships.return_value = [{"source_id": "test_up"}]
    res_up = execute_tool_call("find_dependents", {"entity_id": "123"}, mock_kg, mock_rag)
    assert "test_up" in res_up
    
    # 4. hybrid_search
    mock_rag.search_documents.return_value = [{"snippet": "found_doc"}]
    res_rag = execute_tool_call("hybrid_search", {"query": "auth"}, mock_kg, mock_rag)
    assert "found_doc" in res_rag
    
    # 5. Unknown tool
    res_unk = execute_tool_call("made_up_tool", {}, mock_kg, mock_rag)
    assert "Unknown tool" in res_unk

@patch("backend.orchestrator.client.chat.completions.create")
def test_orchestrator_max_turns_reached(mock_create: MagicMock) -> None:
    """Test US-3.2 Edge Case: Loop exhausts max_turns without returning an answer."""
    func = MagicMock()
    func.name = "find_entity"
    func.arguments = '{"name": "Endless"}'
    mock_tool_call = MagicMock(id="c_endless", type="function", function=func)
    
    mock_message = MagicMock(content=None, tool_calls=[mock_tool_call])
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    
    # Constantly return a tool call to force the loop to hit the limit (5 turns)
    mock_create.return_value = mock_response
    
    result = run_chat_cycle("Trigger loop", MagicMock(), MockRAGClient())
    
    assert "Maximum tool iterations reached" in result
    assert mock_create.call_count == 5

def test_execute_tool_call_find_entity_safeguard() -> None:
    """Test that a missing entity triggers the programmatic safeguard instruction."""
    mock_kg = MagicMock()
    mock_kg.search_entity.return_value = None # This forces tools.py to return {"status": "not found"}
    
    res = execute_tool_call("find_entity", {"name": "NonExistent"}, mock_kg, MockRAGClient())
    
    assert "Entity not found" in res
    assert "exactly: 'I could not establish" in res