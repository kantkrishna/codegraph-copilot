# backend/orchestrator.py

# This file handles the conversation loop and tool execution binding for the chatbot.

import json
import logging
import re
from typing import List, Any, cast, Optional
import openai
from openai.types.chat import ChatCompletionMessageParam
from backend.config import settings
from backend.kgtools.tool_schemas import KG_TOOLS
from backend.kgtools.tools import find_entity, get_relationships, find_dependencies, find_dependents
from backend.kgtools.client import KGClient

logger = logging.getLogger(__name__)

client = openai.Client(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

SYSTEM_PROMPT = (
    "You are CodeGraph Engineering Copilot. You MUST use the provided Knowledge Graph tools "
    "to inspect the codebase. When asked about entities, services, dependencies, or impacts, "
    "call `find_entity` first to locate entity IDs, then call `find_dependencies` or `find_dependents`. "
    "Ground all answers strictly in the tool results."
)

def _parse_raw_text_tool_calls(content: Optional[str]) -> List[dict[str, Any]]:
    """Fallback parser for local models that output tool JSON inside message content."""
    if not content:
        return []
    
    parsed_calls: List[dict[str, Any]] = []
    # Match JSON objects that contain "name" and "arguments"
    matches = re.findall(r'\{[^{}]*"name"\s*:\s*["\']?(\w+)["\']?\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}', content)
    
    # Try finding line-delimited or embedded JSON
    candidate_blocks = re.findall(r'\{.*?"name".*?"arguments".*?\}', content, re.DOTALL)
    for idx, block in enumerate(candidate_blocks):
        try:
            # Clean common unquoted key issues from local models
            sanitized = re.sub(r'(\s*)name(\s*):', r'\1"name":', block)
            sanitized = re.sub(r':\s*([a-zA-Z_]\w*)(\s*[,}])', r': "\1"\2', sanitized)
            data = json.loads(sanitized)
            if "name" in data and "arguments" in data:
                parsed_calls.append({
                    "id": f"fallback_call_{idx}",
                    "function_name": str(data["name"]),
                    "arguments": data["arguments"] if isinstance(data["arguments"], dict) else json.loads(data["arguments"])
                })
        except Exception:
            continue
            
    return parsed_calls

def execute_tool_call(func_name: str, args: dict[str, Any], kg_client: KGClient) -> str:
    """Routes a tool call request to the actual Python function."""
    try:
        if func_name == "find_entity":
            result = find_entity(args["name"], kg_client)
        elif func_name == "get_relationships":
            result = get_relationships(
                args["entity_id"], 
                args["direction"], 
                kg_client, 
                args.get("relationship_type")
            )
        elif func_name == "find_dependencies":
            result = find_dependencies(args["entity_id"], kg_client)
        elif func_name == "find_dependents":
            result = find_dependents(args["entity_id"], kg_client)
        else:
            return json.dumps({"error": f"Unknown tool: {func_name}"})
            
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error executing {func_name}: {e}")
        return json.dumps({"error": str(e)})

def run_chat_cycle(prompt: str, kg_client: KGClient) -> str:
    """
    Executes a multi-turn chat cycle, handling autonomous tool selection
    and passing tool responses back to the LLM.
    """
    messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    
    max_turns = 5
    
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=KG_TOOLS,
            tool_choice="auto",
        )
        
        response_message = response.choices[0].message
        
        # 1. Check native tool calls
        if response_message.tool_calls:
            assistant_entry: dict[str, Any] = {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in response_message.tool_calls
                ],
            }
            messages.append(cast(ChatCompletionMessageParam, assistant_entry))
            
            for tool_call in response_message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_result = execute_tool_call(tool_call.function.name, args, kg_client)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })
            continue

        # 2. Check fallback for raw text JSON tool calls (common in smaller local models)
        fallback_calls = _parse_raw_text_tool_calls(response_message.content)
        if fallback_calls and turn < max_turns - 1:
            messages.append({
                "role": "assistant",
                "content": response_message.content,
            })
            for fc in fallback_calls:
                tool_result = execute_tool_call(fc["function_name"], fc["arguments"], kg_client)
                messages.append({
                    "role": "user",
                    "content": f"[Tool Result for {fc['function_name']}]: {tool_result}",
                })
            continue
            
        # 3. Model produced actual textual answer
        return response_message.content or ""
            
    return "Error: Maximum tool iterations reached without final answer."