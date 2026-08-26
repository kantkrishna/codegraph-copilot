# backend/kgtools/client.py

# This file defines the Knowledge Graph Client interface and common exceptions.

from typing import Dict, Any, List, Optional, Protocol

class KGTimeoutError(Exception):
    """Raised when the connection to the Knowledge Graph times out."""
    pass

class KGClient(Protocol):
    """
    Protocol defining the stable API contract for Knowledge Graph interactions.
    This ensures the tools remain decoupled from the underlying database implementation.
    """
    
    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Searches for an entity by exact name."""
        ...
        
    def fetch_relationships(
        self, 
        entity_id: str, 
        direction: str, 
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetches relationships for a given entity ID."""
        ...