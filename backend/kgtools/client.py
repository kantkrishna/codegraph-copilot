# backend/kgtools/client.py

# This file defines the Knowledge Graph and RAG Client interfaces and common exceptions.

from typing import Dict, Any, List, Optional, Protocol


class KGTimeoutError(Exception):
    """Raised when the connection to the Knowledge Graph times out."""
    pass


class KGClient(Protocol):
    """
    Protocol defining the stable API contract for Knowledge Graph interactions.
    """
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Searches for an entity by exact name."""
        ...

    def fetch_relationships(
        self, entity_id: str, direction: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetches relationships for a given entity ID."""
        ...


class RAGClient(Protocol):
    """
    Protocol defining the stable API contract for Hybrid RAG interactions.
    """
    def search_documents(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Executes a hybrid search against code and documentation indices."""
        ...