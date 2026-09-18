# backend/kgtools/tool_schemas.py

# This file defines the OpenAI-compatible tool schemas for the KG tools.

from typing import List
from openai.types.chat import ChatCompletionToolParam

KG_TOOLS: List[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "find_entity",
            "description": "Searches the Knowledge Graph for a specific entity. Always use this first to get the entity_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name of the component (e.g., frontend, PaymentService)"},
                    "entity_type": {
                        "type": "string", 
                        "enum": ["Service", "Class", "Function", "File", "Database", "Unknown"],
                        "description": "If the user asks for a service, pass 'Service'."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_relationships",
            "description": "Retrieves all relationships for an entity. Use this specifically to find source code files belonging to a service by passing direction='inbound'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "direction": {"type": "string", "enum": ["outbound", "inbound", "both"]},
                    "relationship_type": {"type": "string", "nullable": True}
                },
                "required": ["entity_id", "direction"]
            }
        }
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
