# CodeGraph Engineering Copilot

## Prerequisites
* Docker Desktop installed on your machine.
* Docker Compose installed.
* Python 3.x installed.
* Make sure your local Neo4j database [Codegraph AI](https://github.com/kantkrishna/codegraph) is running via Docker Desktop.
* LLM_API_KEY set in your environment variables or set in your `.env` file.
* Ensure your `.env` file is set up with necessary environment variables.

## Setup Instructions

1. Install dependencies using `uv sync`.
2. Ensure your local Neo4j database (Codegraph AI) is running via Docker Desktop.
3. Configure your `.env` file with `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and `LLM_API_KEY`.
4. **To run the Web UI and API:** Execute `make run`, then access the Copilot via `http://localhost:8002`.
5. **To run the CLI Chat:** Execute `make chat` (or `uv run python -m scripts.verify_chat`) to launch the interactive terminal REPL.
6. **To run the Automated Evaluation:** Execute `uv run python scripts/run_evaluation.py` to test the Copilot against the benchmark dataset.

## RAGAS Evaluation Pipeline

To ensure the Copilot's answers remain strictly grounded in the Neo4j Knowledge Graph without hallucination, this project includes a custom-built, thread-isolated evaluation microservice powered by the [Ragas](https://docs.ragas.io/) framework.

The evaluator acts as an LLM-as-a-Judge, scoring the Copilot against a benchmark dataset (`tests/evaluation/benchmark.json`) across three primary metrics:
* **Faithfulness:** Ensures every claim in the Copilot's Answer is explicitly supported by its Evidence block.
* **Context Precision:** Verifies that the Graph traversal tools retrieved highly relevant context for the user's query.
* **Answer Relevancy:** Measures how accurately the Copilot's answer addresses the original prompt without omitting information or pivoting subjects.

### Architectural Highlights
Integrating Ragas with FastAPI and Langchain presents severe asynchronous event loop challenges. This pipeline implements several enterprise patterns to guarantee stability:
* **Dedicated Immortal Worker Thread:** Bypasses FastAPI's thread-pool recycling. All evaluations are fed via a thread-safe queue into a single, permanent background loop. This completely eliminates LangChain `httpx` cache leaks and `Event loop is closed` crashes.
* **Judge Model Override:** Advanced reasoning models (like `o1`, `o3`, or `luna`) reject the `temperature=1e-8` parameter forced by Ragas. The evaluator automatically detects reasoning models and dynamically overrides the Judge to use `gpt-4o-mini`, ensuring deterministic grading without HTTP 400 crashes.
* **Telemetry & Async Isolation:** Aggressively disables Ragas background tracking and neuters `nest_asyncio` at the module level to prevent rogue tasks from throwing `Timeout should be used inside a task` errors.
* **Unified Context Chunking:** Passes the Copilot's entire `### Evidence` block to the judge as a single cohesive chunk, preventing formatting headers (e.g., "Source:") from unfairly penalizing the Context Precision score.

### Running the Evaluation

The evaluation process requires two separate terminals to run the judge microservice and the orchestrator concurrently. 

1. **Start the Evaluator Service (Terminal 1):**
   ```bash
   make rag_eval
   # Runs: uv run python -m scripts.rag_evaluator
   # Hosts the evaluation worker on [http://0.0.0.0:8001](http://0.0.0.0:8001)

2. **Execute the Benchmark Suite (Terminal 2):**

    ```Bash
    make run_eval
    # Runs: uv run python -m scripts.run_evaluation
    # Triggers the Copilot and sends responses to the Evaluator

## Architecture
The Copilot is built using a Python/FastAPI backend connected to a Neo4j Knowledge Graph. It utilizes an Agentic Orchestrator loop enforcing strict LLM routing:
* Structural inquiries route to `find_entity` and `find_dependents` (Cypher Graph traversals).
* Semantic inquiries route to `hybrid_search` (Tokenized Keyword retrieval).
* The web UI is a vanilla HTML/JS implementation utilizing `marked.js` to render the agent's Markdown responses natively.

### 1. High-Level Component & System Architecture
Illustrates how user requests enter through the presentation layers, pass through the FastAPI backend, and interact with the agentic orchestrator, deterministic tools, the Neo4j Knowledge Graph, and the upstream LLM.

```mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        UI["Web UI (frontend/index.html)<br/>• Vanilla HTML5 / ES6<br/>• marked.js Markdown Parser<br/>• Evidence / Confidence CSS"]
        CLI["CLI Tool (scripts/verify_chat.py)<br/>• Interactive REPL Loop"]
        EVAL["Benchmark Runner (scripts/run_evaluation.py)<br/>• 20-Q Engineering Dataset"]
    end

    subgraph BackendApp["FastAPI Application Layer (backend/)"]
        API["FastAPI Server (main.py)<br/>• Lifespan Driver Management<br/>• POST /api/v1/chat<br/>• GET / (Static Index)"]
        
        subgraph Orchestration["Agentic Orchestration Core"]
            ORCH["Chat Orchestrator (orchestrator.py)<br/>• Multi-turn Agentic Loop (max 5)<br/>• System Prompt & Safety Guardrails<br/>• Tool Dispatcher & CoT Stripper"]
            CIRCUIT["Circuit Breakers<br/>• Empty Result Interceptors<br/>• Anti-Looping Enforcers"]
        end

        subgraph Tooling["Knowledge Graph & Retrieval Tools (kgtools/)"]
            SCHEMAS["Tool Schemas (tool_schemas.py)<br/>• KG_TOOLS Function Definitions"]
            TOOLS["Tool Implementations (tools.py)<br/>• find_entity<br/>• get_relationships<br/>• find_dependencies<br/>• find_dependents<br/>• hybrid_search"]
            CLIENTS["Graph & Retrieval Engine (neo4j_client.py)<br/>• Dynamic Property Cypher Traversal<br/>• NLP Tokenized Keyword Search"]
        end

        CONFIG["Config Layer (config.py)<br/>• Pydantic Settings (.env)"]
    end

    subgraph External["External Infrastructure & Providers"]
        NEO4J[("Neo4j Graph Database<br/>• Bolt Protocol (:7687)<br/>• Google Microservices Dataset")]
        LLM["Upstream LLM Engine<br/>• OpenAI-Compatible API Endpoint<br/>• Function / Tool-Calling API"]
    end

    UI -->|HTTP POST /api/v1/chat| API
    EVAL -->|HTTP POST /api/v1/chat| API
    CLI -->|Direct Ingestion| ORCH
    API -->|run_chat_cycle| ORCH
    ORCH --- CIRCUIT
    ORCH -->|KG_TOOLS Definitions| SCHEMAS
    ORCH -->|Function Invocations| TOOLS
    ORCH <-->|Chat Completion + Tool Calling| LLM
    TOOLS --> CLIENTS
    CLIENTS -->|Bolt / Cypher Queries| NEO4J
    CONFIG -.->|Injects Settings| API
    CONFIG -.->|Injects Settings| ORCH
    CONFIG -.->|Injects Settings| CLIENTS

```

### 2. Static Module & Interface Hierarchy

Captures the code-level structure, object orientation, and strict typing contracts (`mypy` strict) across the backend modules.

```mermaid
classDiagram
    direction TB

    class Settings {
        +neo4j_uri: str
        +neo4j_user: str
        +neo4j_password: str
        +llm_base_url: str
        +llm_api_key: str
        +llm_model: str
    }

    class KGClient {
        <<interface>>
        +search_entity(name: str)* Optional[Dict]
        +fetch_relationships(entity_id: str, direction: str, relationship_type: Optional[str])* List[Dict]
    }

    class RAGClient {
        <<interface>>
        +search_documents(query: str, top_k: int, filters: Optional[Dict])* List[Dict]
    }

    class Neo4jKGClient {
        -driver: GraphDatabase.driver
        +search_entity(name: str) Optional[Dict]
        +fetch_relationships(entity_id: str, direction: str, relationship_type: Optional[str]) List[Dict]
        +search_documents(query: str, top_k: int, filters: Optional[Dict]) List[Dict]
        +close() None
    }

    class tools {
        <<module>>
        +find_entity(name, kg_client)
        +get_relationships(entity_id, direction, kg_client, rel_type)
        +find_dependencies(entity_id, kg_client)
        +find_dependents(entity_id, kg_client)
        +hybrid_search(query, rag_client, top_k, filters)
    }

    class orchestrator {
        <<module>>
        +SYSTEM_PROMPT: str
        +execute_tool_call(func_name, args, kg_client, rag_client) str
        +run_chat_cycle(prompt, kg_client, rag_client) str
        +strip_cot_tags(text) str
    }

    class main {
        <<module>>
        +app: FastAPI
        +lifespan(app) AsyncGenerator
        +chat_endpoint(request: ChatRequest) ChatResponse
        +serve_index() FileResponse
    }

    Neo4jKGClient ..|> KGClient : implements
    Neo4jKGClient ..|> RAGClient : implements
    tools ..> KGClient : depends on
    tools ..> RAGClient : depends on
    orchestrator ..> tools : executes
    main ..> orchestrator : invokes
    main ..> Neo4jKGClient : instantiates in lifespan
    Neo4jKGClient ..> Settings : loads config
    orchestrator ..> Settings : loads config

```

### 3. Key Runtime Execution Flow (Agentic Chat Cycle)

Illustrates the dynamic request-response flow, showing how user prompts trigger an autonomous, multi-turn tool-calling loop until a grounded Markdown response is returned.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer (Browser / CLI)
    participant UI as Web Frontend (index.html)
    participant API as FastAPI Router (main.py)
    participant Orch as Orchestrator (orchestrator.py)
    participant LLM as Upstream LLM Engine
    participant Tools as Tools Router (tools.py)
    participant DB as Neo4j Driver (neo4j_client.py)

    Dev->>UI: Submit query ("What calls currencyservice?")
    UI->>UI: Append user message bubble & show "Thinking..."
    UI->>API: POST /api/v1/chat {"prompt": "..."}
    API->>Orch: run_chat_cycle(prompt, kg_client, rag_client)

    loop Multi-Turn Agentic Loop (max_turns = 5)
        Orch->>LLM: chat.completions.create(messages, tools=KG_TOOLS)
        
        alt LLM requests Tool Execution
            LLM-->>Orch: tool_calls: [find_entity("currencyservice")]
            Orch->>Tools: execute_tool_call("find_entity", {"name": "currencyservice"})
            Tools->>DB: search_entity("currencyservice")
            DB-->>Tools: Node Record (id: "4:dcefac...", name: "currencyservice")
            Tools-->>Orch: Tool Result JSON
            Orch->>Orch: Append assistant tool_call & tool response message
        else LLM requests Subsequent Tool Execution
            Orch->>LLM: chat.completions.create(updated_messages)
            LLM-->>Orch: tool_calls: [find_dependents("4:dcefac...")]
            Orch->>Tools: execute_tool_call("find_dependents", {"entity_id": ...})
            Tools->>DB: fetch_relationships(entity_id, "inbound")
            DB-->>Tools: Callers list: [checkoutservice, frontend]
            Tools-->>Orch: Tool Result JSON
            Orch->>Orch: Append assistant tool_call & tool response message
        else LLM provides Final Synthesis
            Orch->>LLM: chat.completions.create(updated_messages)
            LLM-->>Orch: Grounded response (### Answer, Flow, Evidence, Confidence)
        end
    end

    Orch->>Orch: strip_cot_tags(content)
    Orch-->>API: Grounded Markdown text
    API-->>UI: 200 OK {"response": "### Answer..."}
    UI->>UI: formatGroundedResponse() & marked.parse()
    UI-->>Dev: Display rendered Answer card, Evidence block, and Confidence tag

```

### 4. Runtime Environment & Deployment Topology

Details the local development and container runtime infrastructure, highlighting the network boundaries, ports, and memory configurations required to prevent OOM failures.

```mermaid
flowchart TB
    subgraph Host["Host Machine (Windows Workstation)"]
        subgraph UserSpace["User Space"]
            BROWSER["Web Browser<br/>http://localhost:8000"]
            TERMINAL["PowerShell / Terminal<br/>• make chat<br/>• make test<br/>• make run"]
        end

        subgraph PythonEnv["Python 3.14 Runtime (uv virtual environment)"]
            APP["FastAPI Application Process<br/>Uvicorn Server (:8000)"]
            SCRIPTS["CLI / Evaluation Scripts"]
        end

        subgraph WSL["WSL 2 Engine (.wslconfig: >=10GB RAM)"]
            subgraph DockerEngine["Docker Desktop Daemon"]
                subgraph BridgeNet["Docker Network: codegraph"]
                    N4J["Neo4j 5.15 Container<br/>• Bolt Protocol: 0.0.0.0:7687<br/>• HTTP Browser: 0.0.0.0:7474<br/>• Graph Storage Volume"]
                    STACK["Microservice Pipeline<br/>• Kafka (:9092)<br/>• Redis (:6379)<br/>• Postgres (:5432)<br/>• Builder / Worker / API"]
                end
            end
        end
    end

    subgraph Cloud["External Network Boundary"]
        UPSTREAM["Upstream LLM Provider<br/>(OpenAI API / Local Inference Server)"]
    end

    BROWSER -->|HTTP :8000| APP
    TERMINAL -->|uv run| APP
    TERMINAL -->|uv run| SCRIPTS
    APP -->|Bolt Protocol :7687| N4J
    SCRIPTS -->|Bolt Protocol :7687| N4J
    APP -->|HTTPS / REST API| UPSTREAM
    N4J ~~~ STACK

```

## Known Limitations

* **Docker Memory Exhaustion:** Querying large graphs requires increasing WSL 2 memory limits in `.wslconfig` to `10GB+` to prevent Neo4j OOM `ConnectionResetError`s.
* **Exact-Match RAG Constraints:** To prevent Hallucinations without a vector database, `hybrid_search` currently utilizes an NLP stop-word tokenizer and explicit substring checks.

## Evaluation Summary

The MVP achieves robust adherence to strict safety guardrails. When tested against the `tests/evaluation/benchmark.json` dataset using `scripts/run_evaluation.py`:

* **Hallucination Rate:** 0%. Out-of-Scope queries accurately return the exact required rejection string.
* **Grounding:** High. Responses consistently cite valid filepath and node IDs extracted directly from the knowledge graph.
