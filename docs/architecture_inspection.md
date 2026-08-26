# docs/architecture_inspection.md

# Architecture Inspection & Chatbot Boundaries
**Project:** CodeGraph AI Engineering Copilot MVP  
**Epic:** 1 / **Story:** US-1.1

## 1. Existing System State (Phases 1 & 2)
The existing CodeGraph AI platform successfully operates two core retrieval layers:
*   **Knowledge Graph (KG):** Contains verified facts modeled as nodes (`Class`, `Service`, `Function`, `Module`, `API`, etc.) and edges (`CALLS`, `DEPENDS_ON`, `IMPLEMENTS`). Graph databases typical to this pattern (e.g., Neo4j/NetworkX) are accessible via internal query structures.
*   **Hybrid RAG Index:** A vector database (e.g., Chroma/pgvector) containing chunked embeddings of source code files, READMEs, and technical documentation, queryable via BM25 + Vector similarity.

## 2. API Contract Boundaries
To avoid tightly coupling our 7-day Copilot MVP to internal CodeGraph dependencies (which violates the one-week scope constraint), we will interact with the core engine exclusively through standard REST/Function patterns via Pydantic `BaseModel` schemas.

### Designed Tool Interfaces:
*   **`find_entity`**: Resolves ambiguous LLM queries to explicit Graph Nodes.
*   **`get_relationships`**: Navigates 1-hop architecture patterns (inbound/outbound).
*   **`find_dependencies` / `find_dependents`**: Executes localized impact analysis. 
*   **`hybrid_search`**: Fetches unstructured context for "how" and "why" questions.

## 3. Recommended Implementation Strategy
*   **Decoupling:** The chatbot orchestrator (FastAPI) will not import CodeGraph's DB clients directly. It will instantiate lightweight service adapters that satisfy the Pydantic contracts.
*   **Orchestration Logic:** The LLM uses tool calling (function calling) restricted exclusively to the 5 tools above.
*   **Prompting Boundary:** Hidden system prompts will format all final user output according to the strict `GroundedAnswerResponse` contract (Answer, Flow, Evidence, Confidence) established in `backend/contracts.py`.