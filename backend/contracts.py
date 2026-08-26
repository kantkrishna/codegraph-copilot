# backend/contracts.py

# This file defines the strict Pydantic v2 API schemas and contracts 
# for the CodeGraph AI Engineering Copilot tools.

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class DirectionEnum(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BOTH = "both"

class ConfidenceEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = "None"

class BaseToolRequest(BaseModel):
    """Base configuration for all tool requests."""
    model_config = ConfigDict(strict=True, extra="forbid")

class FindEntityRequest(BaseToolRequest):
    """Contract for the find_entity tool."""
    name: str = Field(..., description="The name of the entity to search for (e.g., 'PaymentService').")
    entity_type: Optional[str] = Field(None, description="Optional type of the entity (e.g., 'class', 'function').")

class GetRelationshipsRequest(BaseToolRequest):
    """Contract for the get_relationships tool."""
    entity_name: str = Field(..., description="The name of the target entity.")
    relationship_type: Optional[str] = Field(None, description="Filter by edge type (e.g., 'CALLS', 'IMPLEMENTS').")
    direction: DirectionEnum = Field(default=DirectionEnum.BOTH, description="Traversal direction.")

class FindDependenciesRequest(BaseToolRequest):
    """Contract for the find_dependencies tool (what this component depends on)."""
    entity_name: str = Field(..., description="The entity name to find dependencies for.")
    depth: int = Field(default=1, ge=1, le=5, description="Graph traversal depth.")

class FindDependentsRequest(BaseToolRequest):
    """Contract for the find_dependents tool (what depends on this component)."""
    entity_name: str = Field(..., description="The entity name to find dependents for.")
    depth: int = Field(default=1, ge=1, le=5, description="Graph traversal depth.")

class HybridSearchRequest(BaseToolRequest):
    """Contract for the hybrid_search tool."""
    query: str = Field(..., description="Natural language search query.")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to return.")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters (e.g., repository or file type).")

class GroundedAnswerResponse(BaseModel):
    """The structured response contract enforced upon the LLM."""
    model_config = ConfigDict(strict=True)
    
    answer: str = Field(..., description="The concise engineering answer.")
    flow: List[str] = Field(default_factory=list, description="Ordered steps representing system flow or architecture.")
    evidence: List[str] = Field(..., description="List of specific sources and Knowledge Graph facts used.")
    confidence: ConfidenceEnum = Field(..., description="Confidence level based on available evidence.")