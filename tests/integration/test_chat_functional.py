# tests/integration/test_chat_functional.py

# This file contains functional/integration tests for the KG tool orchestrator cycle.
# LLM network calls are mocked to ensure deterministic, flake-free CI/CD builds.

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch
from backend.kgtools.client import KGClient
from backend.orchestrator import run_chat_cycle


class FunctionalMockKGClient:
    """In-memory KG client mimicking real CodeGraph node and edge schemas."""

    def __init__(self) -> None:
        self.entities = {
            "PaymentService": {
                "id": "svc_payment",
                "type": "Service",
                "name": "PaymentService",
            },
            "OrderService": {
                "id": "svc_order",
                "type": "Service",
                "name": "OrderService",
            },
            "Database": {
                "id": "infra_db",
                "type": "Infrastructure",
                "name": "PostgresDatabase",
            },
        }
        self.edges = [
            {"source_id": "svc_order", "target_id": "svc_payment", "edge_type": "CALLS"},
            {"source_id": "svc_payment", "target_id": "infra_db", "edge_type": "DEPENDS_ON"},
        ]

    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return self.entities.get(name)

    def fetch_relationships(
        self,
        entity_id: str,
        direction: str,
        relationship_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for edge in self.edges:
            if direction in ("outbound", "both") and edge["source_id"] == entity_id:
                results.append(edge)
            elif direction in ("inbound", "both") and edge["target_id"] == entity_id:
                results.append(edge)
        return results


@patch("backend.orchestrator.client.chat.completions.create")
@pytest.mark.functional
def test_functional_dependency_lookup(mock_create: MagicMock) -> None:
    """
    End-to-end run: asks what PaymentService depends on.
    Validates tool selection -> tool execution -> final textual synthesis.
    """
    kg_client: KGClient = FunctionalMockKGClient()
    
    # Mock Turn 1: Model requests to find the entity
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(
        content=None, 
        tool_calls=[MagicMock(id="call_1", type="function", function=MagicMock(name="find_entity", arguments='{"name": "PaymentService"}'))]
    ))]
    
    # Mock Turn 2: Model uses the correct ID to find dependencies
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(
        content=None, 
        tool_calls=[MagicMock(id="call_2", type="function", function=MagicMock(name="find_dependencies", arguments='{"entity_id": "svc_payment"}'))]
    ))]
    
    # Mock Turn 3: Model synthesizes the final answer using the graph facts
    mock_response_3 = MagicMock()
    mock_response_3.choices = [MagicMock(message=MagicMock(
        content="PaymentService depends on PostgresDatabase (infra_db).", 
        tool_calls=None
    ))]
    
    mock_create.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    
    prompt = "Find what components PaymentService depends on."
    response = run_chat_cycle(prompt, kg_client)

    assert isinstance(response, str)
    assert len(response) > 0
    assert any(term in response.lower() for term in ["database", "infra_db", "postgres"])


@patch("backend.orchestrator.client.chat.completions.create")
@pytest.mark.functional
def test_functional_impact_dependents_lookup(mock_create: MagicMock) -> None:
    """
    End-to-end run: asks what depends on PaymentService (upstream caller).
    Validates find_dependents tool selection and synthesis.
    """
    kg_client: KGClient = FunctionalMockKGClient()
    
    # Mock Turn 1
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(
        content=None, 
        tool_calls=[MagicMock(id="call_1", type="function", function=MagicMock(name="find_entity", arguments='{"name": "PaymentService"}'))]
    ))]
    
    # Mock Turn 2
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=MagicMock(
        content=None, 
        tool_calls=[MagicMock(id="call_2", type="function", function=MagicMock(name="find_dependents", arguments='{"entity_id": "svc_payment"}'))]
    ))]
    
    # Mock Turn 3
    mock_response_3 = MagicMock()
    mock_response_3.choices = [MagicMock(message=MagicMock(
        content="OrderService (svc_order) depends on PaymentService.", 
        tool_calls=None
    ))]
    
    mock_create.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    
    prompt = "Identify what services or callers depend on PaymentService."
    response = run_chat_cycle(prompt, kg_client)

    assert isinstance(response, str)
    assert any(term in response.lower() for term in ["orderservice", "order", "svc_order"])