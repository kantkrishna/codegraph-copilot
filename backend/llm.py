# backend/llm.py

# This file encapsulates the interaction with the LLM API using an OpenAI-compatible client,
# supporting local providers like Ollama as configured in environment settings.

import openai
from backend.config import settings

# Initialize client with configured base_url and api_key
client = openai.Client(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

def call_llm(prompt: str) -> str:
    """
    Sends a basic text prompt to the LLM and returns the string response.
    """
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        timeout=30.0  # Slightly longer timeout for local model spin-up
    )
    return response.choices[0].message.content or ""