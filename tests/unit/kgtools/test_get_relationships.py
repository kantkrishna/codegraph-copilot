# tests/unit/kgtools/test_get_relationships.py

# This file contains the unit tests for the get_relationships Knowledge Graph tool.

import pytest
from typing import Dict, Any, Optional, List
from backend.kgtools.tools import get_relationships
from backend.kgtools.client import KGClient, KGTimeoutError

class MockKGClientForGetRelationships:
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return None

    def fetch_relationships(self, entity_id: str, direction: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if entity_id == "ent_123":
            if direction == "outbound":
                return [{"target_id": "ent_456", "edge_type": "CALLS"}]
            if direction == "inbound":
                return [{"source_id": "ent_789", "edge_type": "DEPENDS_ON"}]
        return []

def test_get_relationships_outbound_success() -> None:
    """Test US-2.2 Scenario 1: Valid retrieval (Outbound)."""
    client: KGClient = MockKGClientForGetRelationships()
    result = get_relationships("ent_123", "outbound", client)
    
    assert len(result) == 1
    assert result[0]["target_id"] == "ent_456"
    assert result[0]["edge_type"] == "CALLS"

def test_get_relationships_inbound_success() -> None:
    """Test US-2.2 Scenario 1: Valid retrieval (Inbound)."""
    client: KGClient = MockKGClientForGetRelationships()
    result = get_relationships("ent_123", "inbound", client)
    
    assert len(result) == 1
    assert result[0]["source_id"] == "ent_789"
    assert result[0]["edge_type"] == "DEPENDS_ON"

def test_get_relationships_empty_result() -> None:
    """Test US-2.2 Scenario 2: No relationships found."""
    client: KGClient = MockKGClientForGetRelationships()
    result = get_relationships("ent_orphan", "both", client)
    
    assert isinstance(result, list)
    assert len(result) == 0

def test_get_relationships_invalid_entity() -> None:
    """Test US-2.2 Edge Case: Null or malformed entity ID returns validation error."""
    client: KGClient = MockKGClientForGetRelationships()
    
    with pytest.raises(ValueError, match="Invalid entity ID"):
        get_relationships("", "outbound", client)
        
    with pytest.raises(ValueError, match="Invalid entity ID"):
        get_relationships(None, "outbound", client) # type: ignore