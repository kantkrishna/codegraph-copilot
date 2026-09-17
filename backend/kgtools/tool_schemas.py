# backend/kgtools/tool_schemas.py

# This file defines the OpenAI-compatible tool schemas for the KG tools.

from typing import List
from openai.types.chat import ChatCompletionToolParam

KG_TOOLS: List[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "find_entity",
            "description": "Search for a specific entity by name in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The exact name of the entity.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relationships",
            "description": "Retrieve the surrounding relationships for a verified entity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "direction": {
                        "type": "string",
                        "enum": ["inbound", "outbound", "both"],
                    },
                    "relationship_type": {"type": "string"},
                },
                "required": ["entity_id", "direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_dependencies",
            "description": "Determine what an entity depends on (downstream components).",
            "parameters": {
                "type": "object",
                "properties": {"entity_id": {"type": "string"}},
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_dependents",
            "description": "Determine what depends on a component (upstream / impact analysis).",
            "parameters": {
                "type": "object",
                "properties": {"entity_id": {"type": "string"}},
                "required": ["entity_id"],
            },
        },
    },
]
