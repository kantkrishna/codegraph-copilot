# tests/unit/kgtools/test_dependencies.py

# This file contains the unit tests for the find_dependencies and find_dependents KG tools.

from typing import Dict, Any, List, Optional
from backend.kgtools.tools import find_dependencies, find_dependents
from backend.kgtools.client import KGClient


class MockKGClientForDependencies:
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return None

    def fetch_relationships(
        self, entity_id: str, direction: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if entity_id == "ent_123":
            if direction == "outbound":
                return [{"target_id": "ent_downstream", "edge_type": "CALLS"}]
            if direction == "inbound":
                return [{"source_id": "ent_upstream", "edge_type": "DEPENDS_ON"}]
        return []


def test_find_dependencies_returns_list() -> None:
    """Test US-2.3 Scenario 1: Find Dependencies (Downstream)."""
    client: KGClient = MockKGClientForDependencies()
    result = find_dependencies("ent_123", client)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["target_id"] == "ent_downstream"


def test_find_dependents_returns_list() -> None:
    """Test US-2.3 Scenario 2: Find Dependents (Upstream / Impact)."""
    client: KGClient = MockKGClientForDependencies()
    result = find_dependents("ent_123", client)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["source_id"] == "ent_upstream"


def test_find_dependencies_none_exist() -> None:
    """Test US-2.3 Edge Case: None exist returns empty list."""
    client: KGClient = MockKGClientForDependencies()
    result = find_dependencies("ent_isolated", client)

    assert isinstance(result, list)
    assert len(result) == 0
