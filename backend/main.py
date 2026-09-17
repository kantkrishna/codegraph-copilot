# backend/main.py

# This file defines the main FastAPI application instance and routing,
# including the minimal health check and basic LLM test endpoints.

from typing import Dict
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict
import openai

from backend.llm import call_llm

app = FastAPI(
    title="CodeGraph Engineering Copilot",
    description="AI-Augmented Engineering Platform Chatbot MVP",
    version="0.1.0",
)


class LLMTestRequest(BaseModel):
    """Request contract for the LLM test endpoint."""

    prompt: str
    model_config = ConfigDict(strict=True)


class LLMTestResponse(BaseModel):
    """Response contract for the LLM test endpoint."""

    response: str
    model_config = ConfigDict(strict=True)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Minimal health check endpoint."""
    return {"status": "ok"}


@app.post("/api/v1/chat/test", response_model=LLMTestResponse)
def test_llm_integration(request: LLMTestRequest) -> LLMTestResponse:
    """
    Basic test endpoint to verify LLM API connectivity and authentication.
    """
    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty."
        )

    try:
        response_text = call_llm(request.prompt)
        return LLMTestResponse(response=response_text)

    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream authentication failure: Invalid API Key.",
        )
    except openai.APITimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream timeout failure.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
