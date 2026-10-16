# scripts/rag_evaluator.py

"""
RAGAS Evaluation Service
This script provides a FastAPI endpoint to evaluate the quality of code generation answers using the RAGAS framework.
It accepts a POST request with the following JSON payload:
{
    "developer_query": "string",
    "codegraph_contexts": ["string"],
    "copilot_answer": "string",
    "ground_truth": "string"
}
It returns a JSON response with the evaluation results:
{
    "faithfulness": 0.0,
    "answer_relevance": 0.0,
    "context_precision": 0.0
}
"""

# scripts/rag_evaluator.py

import os
import sys
import math
import asyncio
import threading
import queue
import concurrent.futures
from unittest.mock import MagicMock

# ==============================================================================
# 1. DISABLE BACKGROUND TELEMETRY & NEUTER NEST_ASYNCIO
# Prevents Ragas from spawning background tracking tasks that leak across loops.
# Neutering nest_asyncio prevents "Timeout should be used inside a task" crashes.
# ==============================================================================
os.environ["RAGAS_DO_NOT_TRACK"] = "true"
os.environ["DO_NOT_TRACK"] = "true"

import nest_asyncio
nest_asyncio.apply = lambda *args, **kwargs: None

sys.modules['langchain_community.chat_models.vertexai'] = MagicMock()
sys.modules['langchain_community.chat_models.vertexai'].ChatVertexAI = MagicMock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datasets import Dataset

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from ragas.run_config import RunConfig

from backend.config import settings

app = FastAPI(title="RAGAS Evaluation Service")

class EvaluationRequest(BaseModel):
    developer_query: str
    codegraph_contexts: List[str]
    copilot_answer: str
    ground_truth: str

def safe_extract(val: float, metric_name: str) -> float:
    if val is None or math.isnan(val):
        return 0.0
    return round(float(val), 4)

# ==============================================================================
# 2. THE BULLETPROOF ARCHITECTURE: DEDICATED EVALUATION THREAD
# FastAPI worker threads are recycled, causing stale loops and crashes.
# By feeding all evaluations into a single background thread with ONE immortal 
# event loop, we completely eliminate all asyncio and memory state bugs.
# ==============================================================================
eval_queue = queue.Queue()

def ragas_evaluation_worker():
    """
    Permanent background thread. Initializes ONE event loop and keeps it open forever.
    Processes Ragas evaluations synchronously to prevent any async collisions.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        task = eval_queue.get()
        if task is None:
            break
            
        data, llm_model_name, key_val, base_url, future = task
        
        try:
            # Explicitly force Connection: close to bypass HTTPX keep-alive bugs
            custom_llm = ChatOpenAI(
                model=llm_model_name, 
                api_key=key_val, 
                base_url=base_url, 
                temperature=0,
                default_headers={"Connection": "close"}
            )
            
            custom_embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small", 
                api_key=key_val, 
                base_url=base_url,
                default_headers={"Connection": "close"}
            )

            ragas_llm = LangchainLLMWrapper(custom_llm)
            ragas_emb = LangchainEmbeddingsWrapper(custom_embeddings)
            dataset = Dataset.from_dict(data)

            # Limit to 1 worker to prevent internal Ragas task starvation
            config = RunConfig(timeout=300, max_workers=1)

            evaluation_result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision],
                llm=ragas_llm,
                embeddings=ragas_emb,
                run_config=config,
                raise_exceptions=True
            )

            df = evaluation_result.to_pandas()

            f_val = df["faithfulness"].iloc[0] if "faithfulness" in df.columns else float('nan')
            r_val = df["answer_relevancy"].iloc[0] if "answer_relevancy" in df.columns else (
                df["response_relevancy"].iloc[0] if "response_relevancy" in df.columns else float('nan')
            )
            p_val = df["context_precision"].iloc[0] if "context_precision" in df.columns else float('nan')

            scores = {
                "faithfulness": safe_extract(f_val, "faithfulness"),
                "answer_relevance": safe_extract(r_val, "answer_relevancy"),
                "context_precision": safe_extract(p_val, "context_precision"),
            }

            if "faithfulness_reasoning" in df.columns:
                scores["faithfulness_reasoning"] = str(df["faithfulness_reasoning"].iloc[0])
            if "context_precision_reasoning" in df.columns:
                scores["context_precision_reasoning"] = str(df["context_precision_reasoning"].iloc[0])

            future.set_result(scores)
            
        except Exception as e:
            future.set_exception(e)
            
        finally:
            eval_queue.task_done()

# Start the immortal background worker thread when the server initializes
worker_thread = threading.Thread(target=ragas_evaluation_worker, daemon=True)
worker_thread.start()

@app.post("/evaluate")
def run_ragas_evaluation(request: EvaluationRequest):
    raw_key = getattr(settings, "llm_api_key", None)
    if not raw_key:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not set.")

    key_val = raw_key.get_secret_value() if hasattr(raw_key, "get_secret_value") else str(raw_key)
    base_url = getattr(settings, "llm_base_url", None)
    llm_model_name = getattr(settings, "llm_model", "gpt-4o-mini")

    # Override reasoning models for the Judge to prevent temperature API crashes
    if any(m in llm_model_name.lower() for m in ["luna", "o1", "o3", "reasoning"]):
        llm_model_name = "gpt-4o-mini"

    data = {
        "user_input": [request.developer_query],
        "retrieved_contexts": [request.codegraph_contexts], 
        "response": [request.copilot_answer],
        "reference": [request.ground_truth]
    }

    # 3. Drop the job into the thread-safe queue and wait for the result
    future = concurrent.futures.Future()
    eval_queue.put((data, llm_model_name, key_val, base_url, future))

    try:
        # Halt the HTTP request until the background thread resolves the future
        scores = future.result(timeout=600)
        return scores
    except concurrent.futures.TimeoutError:
        raise HTTPException(status_code=504, detail="RAGAS Evaluation Error: Request timed out in queue.")
    except Exception as e:
        print(f"[EVALUATOR CRASH] {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAGAS Evaluation Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)