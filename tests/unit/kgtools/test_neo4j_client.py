# tests/unit/kgtools/test_neo4j_client.py

# This file contains the unit tests for the Neo4jKGClient, mocking the neo4j driver
# to achieve maximum test coverage without requiring a live database connection.

from unittest.mock import MagicMock, patch
from typing import Any
import pytest

from backend.kgtools.neo4j_client import Neo4jKGClient


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_neo4j_client_init_and_close(mock_driver_cls: MagicMock) -> None:
    """Test that the driver is initialized correctly and closed properly."""
    mock_driver_instance = MagicMock()
    mock_driver_cls.return_value = mock_driver_instance
    
    client = Neo4jKGClient()
    mock_driver_cls.assert_called_once()
    
    client.close()
    mock_driver_instance.close.assert_called_once()


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_search_entity_found(mock_driver_cls: MagicMock) -> None:
    """Test search_entity successfully parses an exact match and handles name cleanup."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    # Mock the Neo4j node object and record dictionary
    mock_node = MagicMock()
    mock_node.element_id = "node_123"
    mock_node.get.return_value = "PaymentService"
    
    mock_record = MagicMock()
    
    def record_getitem(key: str) -> Any:
        if key == "entity":
            return mock_node
        if key == "labels":
            return ["Service"]
        return None
        
    mock_record.__getitem__.side_effect = record_getitem
    
    mock_result = MagicMock()
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result
    
    # Passing "Payment Service" tests the clean_name replace logic inside search_entity
    result = client.search_entity("Payment Service")
    
    assert result is not None
    assert result["id"] == "node_123"
    assert result["type"] == "Service"
    assert result["name"] == "PaymentService"
    mock_session.run.assert_called_once()


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_search_entity_empty_labels_fallback(mock_driver_cls: MagicMock) -> None:
    """Test search_entity falls back to 'Entity' type when node has no labels."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    mock_node = MagicMock()
    mock_node.element_id = "node_456"
    mock_node.get.return_value = "UnknownComponent"
    
    mock_record = MagicMock()
    
    def record_getitem(key: str) -> Any:
        if key == "entity":
            return mock_node
        if key == "labels":
            return []  # Empty labels array tests the fallback branch
        return None
        
    mock_record.__getitem__.side_effect = record_getitem
    mock_session.run.return_value.single.return_value = mock_record
    
    result = client.search_entity("UnknownComponent")
    
    assert result is not None
    assert result["type"] == "Entity"


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_search_entity_not_found(mock_driver_cls: MagicMock) -> None:
    """Test search_entity handles empty database results gracefully."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    mock_result = MagicMock()
    mock_result.single.return_value = None
    mock_session.run.return_value = mock_result
    
    result = client.search_entity("NonExistent")
    
    assert result is None


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_fetch_relationships_outbound(mock_driver_cls: MagicMock) -> None:
    """Test fetch_relationships correctly formats outbound edge queries."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    mock_node = MagicMock()
    mock_node.element_id = "target_999"
    mock_node.get.return_value = "PostgresDatabase"
    
    mock_record = {"target": mock_node, "edge_type": "DEPENDS_ON"}
    mock_session.run.return_value = [mock_record]
    
    results = client.fetch_relationships("node_123", "outbound")
    
    assert len(results) == 1
    assert results[0]["target_id"] == "target_999"
    assert results[0]["target_name"] == "PostgresDatabase"
    assert results[0]["edge_type"] == "DEPENDS_ON"
    mock_session.run.assert_called_once()


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_fetch_relationships_inbound(mock_driver_cls: MagicMock) -> None:
    """Test fetch_relationships correctly formats inbound edge queries."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    mock_node = MagicMock()
    mock_node.element_id = "source_777"
    mock_node.get.return_value = "OrderService"
    
    mock_record = {"source": mock_node, "edge_type": "CALLS"}
    mock_session.run.return_value = [mock_record]
    
    results = client.fetch_relationships("node_123", "inbound")
    
    assert len(results) == 1
    assert results[0]["source_id"] == "source_777"
    assert results[0]["source_name"] == "OrderService"
    assert results[0]["edge_type"] == "CALLS"
    mock_session.run.assert_called_once()


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_fetch_relationships_both(mock_driver_cls: MagicMock) -> None:
    """Test fetch_relationships executes and merges both inbound and outbound queries."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    # Setup Outbound Mock Response
    mock_target = MagicMock()
    mock_target.element_id = "t_1"
    mock_target.get.return_value = "DownstreamComponent"
    out_record = {"target": mock_target, "edge_type": "CALLS"}
    
    # Setup Inbound Mock Response
    mock_source = MagicMock()
    mock_source.element_id = "s_1"
    mock_source.get.return_value = "UpstreamComponent"
    in_record = {"source": mock_source, "edge_type": "DEPENDS_ON"}
    
    # Return out_record on first run() call, and in_record on second run() call
    mock_session.run.side_effect = [[out_record], [in_record]]
    
    results = client.fetch_relationships("node_123", "both")
    
    assert len(results) == 2
    assert results[0]["target_id"] == "t_1"
    assert results[1]["source_id"] == "s_1"
    assert mock_session.run.call_count == 2


@patch("backend.kgtools.neo4j_client.GraphDatabase.driver")
def test_search_documents_success(mock_driver_cls: MagicMock) -> None:
    """Test that search_documents correctly formats and executes a RAG cypher query."""
    client = Neo4jKGClient()
    mock_session = MagicMock()
    client.driver.session.return_value.__enter__.return_value = mock_session
    
    # Mock Neo4j Record structure matching the 'node_data' return schema
    mock_record = {
        "title": "AuthController",
        "node_data": {
            "content": "Handles JWT authentication.",
            "name": "AuthController",
            "content_embedding": [0.1, 0.2, 0.3], # Should be filtered out
            "complex_object": {"ignore": "me"} # Should be filtered out (not str/int/float)
        },
        "filepath": "backend/auth.py"
    }
    mock_session.run.return_value = [mock_record]
    
    # We pass a full sentence to verify the stop-word removal logic works
    results = client.search_documents("explain the authentication flow", top_k=3)
    
    assert len(results) == 1
    assert results[0]["title"] == "AuthController"
    assert results[0]["filepath"] == "backend/auth.py"
    
    # Verify the snippet builder correctly extracted string properties and dropped embeddings
    assert "Handles JWT authentication." in results[0]["snippet"]
    assert "AuthController" in results[0]["snippet"]
    assert "content_embedding" not in results[0]["snippet"]
    
    # Verify the driver was called exactly once with the tokenized keywords
    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args[1]
    assert "authentication" in call_args["keywords"]
    assert "explain" not in call_args["keywords"] # Proves stop-words are stripped
    assert call_args["top_k"] == 3