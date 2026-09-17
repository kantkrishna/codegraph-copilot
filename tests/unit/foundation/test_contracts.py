# tests/test_contracts.py

# This file contains the unit tests for validating the Pydantic API contracts
# between the Chatbot Orchestrator and the CodeGraph AI tools.

import pytest
from pydantic import ValidationError

from backend.contracts import (
    FindEntityRequest,
    GetRelationshipsRequest,
    FindDependenciesRequest,
    HybridSearchRequest,
    DirectionEnum,
    ConfidenceEnum,  # <-- ADDED IMPORT
    GroundedAnswerResponse,
)


def test_find_entity_request_valid() -> None:
    req = FindEntityRequest(name="PaymentService", entity_type="class")
    assert req.name == "PaymentService"
    assert req.entity_type == "class"


def test_find_entity_request_invalid_strict_type() -> None:
    with pytest.raises(ValidationError):
        # Tell mypy to ignore this intentional type violation
        FindEntityRequest(name=123)  # type: ignore


def test_get_relationships_request_valid() -> None:
    req = GetRelationshipsRequest(
        entity_name="UserService",
        relationship_type="CALLS",
        direction=DirectionEnum.OUTBOUND,
    )
    assert req.entity_name == "UserService"
    assert req.direction == DirectionEnum.OUTBOUND


def test_get_relationships_request_invalid_direction() -> None:
    with pytest.raises(ValidationError):
        # Tell mypy to ignore this intentional type violation
        GetRelationshipsRequest(entity_name="UserService", direction="diagonal")  # type: ignore


def test_dependency_requests_default_depth() -> None:
    dep_req = FindDependenciesRequest(entity_name="AuthService")
    assert dep_req.depth == 1

    with pytest.raises(ValidationError):
        # Tell mypy to ignore this intentional type violation
        FindDependenciesRequest(entity_name="AuthService", depth="two")  # type: ignore


def test_hybrid_search_request_valid() -> None:
    req = HybridSearchRequest(
        query="How does auth work?", top_k=3, filters={"module": "auth"}
    )
    assert req.query == "How does auth work?"
    assert req.top_k == 3
    assert req.filters == {"module": "auth"}


def test_grounded_answer_schema() -> None:
    req = GroundedAnswerResponse(
        answer="Auth starts in AuthController.",
        flow=["AuthController", "AuthService"],
        evidence=[
            "Knowledge Graph: AuthController -> AuthService",
            "Source: AuthController.java",
        ],
        confidence=ConfidenceEnum.HIGH,
    )
    assert len(req.flow) == 2
    assert "AuthController.java" in req.evidence[1]
    assert req.confidence == ConfidenceEnum.HIGH
