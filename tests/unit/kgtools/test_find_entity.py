# tests/unit/kgtools/test_find_entity.py

# This file contains the unit tests for the find_entity Knowledge Graph tool.

from typing import Dict, Any, Optional
from backend.kgtools.tools import find_entity
from backend.kgtools.client import KGClient, KGTimeoutError


class MockKGClientForFindEntity:
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        if name == "PaymentService":
            return {"id": "ent_123", "type": "Class", "name": "PaymentService"}
        if name == "TimeoutService":
            raise KGTimeoutError("Connection timed out")
        return None

    def fetch_relationships(
        self, entity_id: str, direction: str, relationship_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        return []


def test_find_entity_exact_match() -> None:
    """Test US-2.1 Scenario 1: Entity exists."""
    client: KGClient = MockKGClientForFindEntity()
    result = find_entity("PaymentService", client)

    assert result is not None
    assert result.get("id") == "ent_123"
    assert result.get("type") == "Class"
    assert result.get("name") == "PaymentService"


def test_find_entity_not_found() -> None:
    """Test US-2.1 Scenario 2: Entity does not exist."""
    client: KGClient = MockKGClientForFindEntity()
    result = find_entity("NonExistentService", client)

    assert result.get("status") == "not found"
    assert "not found" in result.get("message", "").lower()


def test_find_entity_backend_timeout() -> None:
    """Test US-2.1 Edge Case: Backend timeout."""
    client: KGClient = MockKGClientForFindEntity()
    result = find_entity("TimeoutService", client)

    assert result.get("status") == "error"
    # Changed "timeout" to "timed out" to match the actual error message
    assert "timed out" in result.get("message", "").lower()
