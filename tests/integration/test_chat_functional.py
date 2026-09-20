# tests/integration/test_chat_functional.py

# This file contains functional/integration tests for the KG tool orchestrator cycle.
# LLM network calls are mocked to ensure deterministic, flake-free CI/CD builds.

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch
from backend.kgtools.client import KGClient, RAGClient
from backend.orchestrator import run_chat_cycle

class FunctionalMockKGClient:
    def __init__(self) -> None:
        self.entities = {
            "PaymentService": {"id": "svc_payment", "type": "Service", "name": "PaymentService"},
            "OrderService": {"id": "svc_order", "type": "Service", "name": "OrderService"},
            "Database": {"id": "infra_db", "type": "Infrastructure", "name": "PostgresDatabase"},
        }
        self.edges = [
            {"source_id": "svc_order", "target_id": "svc_payment", "edge_type": "CALLS"},
            {"source_id": "svc_payment", "target_id": "infra_db", "edge_type": "DEPENDS_ON"},
        ]
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return self.entities.get(name)
    def fetch_relationships(
        self, entity_id: str, direction: str, relationship_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for edge in self.edges:
            if direction in ("outbound", "both") and edge["source_id"] == entity_id:
                results.append(edge)
            elif direction in ("inbound", "both") and edge["target_id"] == entity_id:
                results.append(edge)
        return results

class DummyRAGClient(RAGClient):
    def search_documents(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return []

@patch("backend.orchestrator.client.chat.completions.create")
@pytest.mark.functional
def test_functional_dependency_lookup(mock_create: MagicMock) -> None:
    kg_client: KGClient = FunctionalMockKGClient()
    rag_client: RAGClient = DummyRAGClient()
    
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(
        content=None, tool_calls=[MagicMock(id="call_1", type="function", function=MagicMock(name="find_entity", arguments='{"name": "PaymentService"}'))]
    ))]
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(
        content=None, tool_calls=[MagicMock(id="call_2", type="function", function=MagicMock(name="find_dependencies", arguments='{"entity_id": "svc_payment"}'))]
    ))]
    mock_response_3 = MagicMock()
    mock_response_3.choices = [MagicMock(message=MagicMock(
        content="PaymentService depends on PostgresDatabase (infra_db).", tool_calls=None
    ))]
    mock_create.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    
    response = run_chat_cycle("Find what components PaymentService depends on.", kg_client, rag_client)
    assert any(term in response.lower() for term in ["database", "infra_db", "postgres"])

@patch("backend.orchestrator.client.chat.completions.create")
@pytest.mark.functional
def test_functional_impact_dependents_lookup(mock_create: MagicMock) -> None:
    kg_client: KGClient = FunctionalMockKGClient()
    rag_client: RAGClient = DummyRAGClient()
    
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(
        content=None, tool_calls=[MagicMock(id="call_1", type="function", function=MagicMock(name="find_entity", arguments='{"name": "PaymentService"}'))]
    ))]
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(
        content=None, tool_calls=[MagicMock(id="call_2", type="function", function=MagicMock(name="find_dependents", arguments='{"entity_id": "svc_payment"}'))]
    ))]
    mock_response_3 = MagicMock()
    mock_response_3.choices = [MagicMock(message=MagicMock(
        content="OrderService (svc_order) depends on PaymentService.", tool_calls=None
    ))]
    mock_create.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    
    response = run_chat_cycle("Identify what services or callers depend on PaymentService.", kg_client, rag_client)
    assert any(term in response.lower() for term in ["orderservice", "order", "svc_order"])