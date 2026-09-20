# backend/main.py

# This file defines the main FastAPI application instance and routing,
# now updated to serve the production orchestrator endpoint and static UI files.

import os
from contextlib import asynccontextmanager
from typing import Dict, AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
import openai

from backend.llm import call_llm
from backend.orchestrator import run_chat_cycle
from backend.kgtools.neo4j_client import Neo4jKGClient

# Global database client initialized during the app lifespan
kg_client_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global kg_client_instance
    try:
        kg_client_instance = Neo4jKGClient()
    except Exception as e:
        print(f"Warning: Could not connect to Neo4j on startup: {e}")
        kg_client_instance = None
    yield
    if kg_client_instance:
        kg_client_instance.close()

app = FastAPI(
    title="CodeGraph Engineering Copilot",
    description="AI-Augmented Engineering Platform Chatbot MVP",
    version="0.1.0",
    lifespan=lifespan
)

class LLMTestRequest(BaseModel):
    prompt: str
    model_config = ConfigDict(strict=True)

class LLMTestResponse(BaseModel):
    response: str
    model_config = ConfigDict(strict=True)

class ChatRequest(BaseModel):
    prompt: str
    model_config = ConfigDict(strict=True)

class ChatResponse(BaseModel):
    response: str
    model_config = ConfigDict(strict=True)

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/v1/chat/test", response_model=LLMTestResponse)
def test_llm_integration(request: LLMTestRequest) -> LLMTestResponse:
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

@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Main production endpoint bridging the frontend to the Copilot Orchestrator."""
    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty."
        )
    try:
        # kg_client_instance acts as both KG and RAG client
        ans = run_chat_cycle(request.prompt, kg_client_instance, kg_client_instance)  # type: ignore
        return ChatResponse(response=ans)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
os.makedirs(frontend_dir, exist_ok=True)

@app.get("/")
def serve_index() -> FileResponse:
    """Serves the primary web interface."""
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_path)

# Serve any additional static assets if created
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")