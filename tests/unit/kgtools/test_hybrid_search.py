# tests/unit/kgtools/test_hybrid_search.py

# This file contains the unit tests for the hybrid_search tool wrapper.

from typing import Dict, Any, List, Optional
from backend.kgtools.tools import hybrid_search
from backend.kgtools.client import RAGClient

class MockRAGClientForSearch:
    def search_documents(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if query == "auth flow":
            return [
                {"title": "AuthService", "snippet": "Handles JWT...", "filepath": "auth.py"},
                {"title": "Auth Docs", "snippet": "OAuth2 flow...", "filepath": "auth.md"}
            ]
        if filters and filters.get("file_type") == "python":
            return [{"title": "Filtered", "snippet": "Python code", "filepath": "main.py"}]
        return []

def test_hybrid_search_success() -> None:
    """Test US-3.1 Scenario 1: Relevant Documents Found."""
    client: RAGClient = MockRAGClientForSearch()
    results = hybrid_search("auth flow", client)
    
    assert len(results) == 2
    assert results[0]["filepath"] == "auth.py"
    assert results[1]["filepath"] == "auth.md"

def test_hybrid_search_empty() -> None:
    """Test US-3.1 Scenario 2: No Documents Found."""
    client: RAGClient = MockRAGClientForSearch()
    results = hybrid_search("unknown query", client)
    
    assert isinstance(results, list)
    assert len(results) == 0

def test_hybrid_search_handles_filters() -> None:
    """Test US-3.1 Edge Case: Filters are correctly passed to client."""
    client: RAGClient = MockRAGClientForSearch()
    results = hybrid_search("anything", client, filters={"file_type": "python"})
    
    assert len(results) == 1
    assert results[0]["filepath"] == "main.py"

def test_hybrid_search_empty_query_string() -> None:
    """Test US-3.1 Edge Case: Empty query string returns empty list immediately."""
    client: RAGClient = MockRAGClientForSearch()
    results = hybrid_search("   ", client)
    
    assert isinstance(results, list)
    assert len(results) == 0