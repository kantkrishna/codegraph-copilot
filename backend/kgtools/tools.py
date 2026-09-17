# backend/kgtools/tools.py

# This file implements the deterministic Knowledge Graph tools for LLM consumption.

from typing import Dict, Any, List, Optional
from backend.kgtools.client import KGClient, KGTimeoutError


def find_entity(name: str, client: KGClient) -> Dict[str, Any]:
    """
    Search for a specific entity by name in the Knowledge Graph.

    Args:
        name: The exact name of the entity (e.g., 'PaymentService').
        client: The injected Knowledge Graph client.

    Returns:
        A dictionary containing the entity details (id, type, name),
        or a graceful error/not-found dictionary if the entity cannot be retrieved.
    """
    try:
        entity: Optional[Dict[str, Any]] = client.search_entity(name)
        if not entity:
            return {
                "status": "not found",
                "message": f"Entity '{name}' not found in the Knowledge Graph.",
            }
        return entity
    except KGTimeoutError:
        return {
            "status": "error",
            "message": "Knowledge Graph query timed out. Please try again.",
        }


def get_relationships(
    entity_id: str,
    direction: str,
    client: KGClient,
    relationship_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the surrounding relationships for a verified entity.

    Args:
        entity_id: The unique identifier of the entity.
        direction: The direction of the relationship ('inbound', 'outbound', or 'both').
        client: The injected Knowledge Graph client.
        relationship_type: Optional filter for specific relationship types (e.g., 'CALLS').

    Returns:
        A list of connected nodes and their edge types. Returns an empty list if none exist.

    Raises:
        ValueError: If the entity_id or direction is invalid.
    """
    if not entity_id or not isinstance(entity_id, str):
        raise ValueError("Invalid entity ID provided.")

    valid_directions: List[str] = ["inbound", "outbound", "both"]
    if direction not in valid_directions:
        raise ValueError(f"Direction must be one of {valid_directions}.")

    return client.fetch_relationships(entity_id, direction, relationship_type)


def find_dependencies(entity_id: str, client: KGClient) -> List[Dict[str, Any]]:
    """
    Find components that the given entity relies upon (downstream).

    Args:
        entity_id: The unique identifier of the entity.
        client: The injected Knowledge Graph client.

    Returns:
        A list of downstream components.
    """
    return get_relationships(entity_id, "outbound", client)


def find_dependents(entity_id: str, client: KGClient) -> List[Dict[str, Any]]:
    """
    Find components that rely on the given entity (upstream / impact).

    Args:
        entity_id: The unique identifier of the entity.
        client: The injected Knowledge Graph client.

    Returns:
        A list of upstream components impacted by this entity.
    """
    return get_relationships(entity_id, "inbound", client)
