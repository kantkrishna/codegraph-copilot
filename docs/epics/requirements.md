# Codegraph Copilot Epics and User Stories: AI Chatbot for Codegraph

## Table of Contents

* [Epic 1: System Analysis and Foundation](#epic-1-system-analysis-and-foundation)
  * [US-1.1: Technical Spike — Analyze CodeGraph AI Architecture and Define API Contracts](#us-11-technical-spike--analyze-codegraph-ai-architecture-and-define-api-contracts)
  * [US-1.2: Initialize Python REST API Backend Skeleton](#us-12-initialize-python-rest-api-backend-skeleton)
  * [US-1.3: Implement Basic LLM Integration and Test Endpoint](#us-13-implement-basic-llm-integration-and-test-endpoint)
* [Epic 2: Knowledge Graph Tool Implementation](#epic-2-knowledge-graph-tool-implementation)
  * [US-2.1: Knowledge Graph Entity Search for Valid Context Retrieval](#us-21-knowledge-graph-entity-search-for-valid-context-retrieval)
  * [US-2.2: Retrieve Entity Relationships for Contextual Answers](#us-22-retrieve-entity-relationships-for-contextual-answers)
  * [US-2.3: Trace Entity Dependencies for Impact Analysis](#us-23-trace-entity-dependencies-for-impact-analysis)
  * [US-2.4: Validate LLM Function Calling with KG Tools](#us-24-validate-llm-function-calling-with-kg-tools)
* [Epic 3: Hybrid RAG Integration & Context Orchestration](#epic-3-hybrid-rag-integration--context-orchestration)
* [Epic 4: Minimal Viable User Interface](#epic-4-minimal-viable-user-interface)
* [Epic 5: MVP Evaluation and Handoff](#epic-5-mvp-evaluation-and-handoff)

---

# Epic 1: System Analysis and Foundation

* **Objective:** Understand the existing Codegraph AI architecture, define the API boundaries, and establish the minimal chatbot backend.
* **Key Deliverables:**
* Inspection report of existing Knowledge Graph and Hybrid RAG capabilities in the Codegraph AI repository.
* Definition of stable API contracts between the chatbot and Codegraph AI.
* A basic Python (FastAPI) backend skeleton.
* Successful end-to-end test call from a local API endpoint to the LLM.

### Analysis of Epic 1 Scope

Epic 1 (System Analysis and Foundation) focuses strictly on project scaffolding, defining the architectural boundaries, and proving the critical integration path to the LLM. Based on your Master Prompt, Epic 1 must deliver:

1. An inspection report and stable API contracts referencing the existing CodeGraph AI systems.
2. A minimal Python REST API skeleton (e.g., FastAPI).
3. A successful, testable end-to-end call from the API to the LLM.

To achieve this without prescribing unnecessary implementation details, I have broken this down into **three minimal user stories**: one technical spike for analysis/contracts, one for the backend skeleton, and one for the LLM integration.

### Assumptions & Clarifications

* **Assumption:** The "inspection report" and "API contracts" can be delivered as Markdown documentation and JSON schemas within the new project repository.
* **Assumption:** We are using a mock/stub strategy for the LLM during TDD to avoid hitting live APIs during automated test runs.
* **Clarification:** Do you have a specific LLM provider (e.g., OpenAI, Google Gemini, Anthropic) in mind for the MVP, or should the LLM integration story remain generic to any provider via a standard interface? (The stories below are written generically).

Here are the renumbered User Stories for Epic 1:

### US-1.1: Technical Spike — Analyze CodeGraph AI Architecture and Define API Contracts

**User Story:** As an AI engineer, I want to inspect the existing CodeGraph AI repository to identify available Knowledge Graph and Hybrid RAG capabilities, so that I can define stable API contracts for the chatbot without tightly coupling to the existing internal implementation.
**Business Value:** Ensures the chatbot MVP remains cleanly decoupled from the existing system, minimizing regression risks and defining a clear boundary for future scaling.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Documentation Generation**
* **Given** access to the existing CodeGraph AI repository
* **When** the architectural inspection is complete
* **Then** an inspection report (Markdown) must be committed to the chatbot repository detailing the chosen graph database, vector database, and available internal APIs.

* **Scenario 2: Contract Definition**
* **Given** the capabilities identified in the inspection
* **When** defining the interface for the chatbot's tools
* **Then** a defined API contract (e.g., OpenAPI spec or Pydantic schemas) must be created for `find_entity`, `get_relationships`, and `hybrid_search`.

**TDD Test Scenarios:**

* *Test:* `test_api_contracts_are_valid_schemas` -> Verify that the defined JSON/Pydantic schemas for the internal boundaries compile and pass schema validation without errors.

**Dependencies:** Access to the existing CodeGraph AI repository and documentation.
**Definition of Done:**

* Inspection report is peer-reviewed (or self-reviewed for a solo dev) and committed to the `docs/` folder.
* Tool interface schemas/contracts are defined in code (e.g., `contracts.py` or `schemas.py`).
* Code compiles and schema tests pass.

**Priority:** 1 (Highest — Must be completed before development begins).


### US-1.2: Initialize Python REST API Backend Skeleton

**User Story:** As a developer, I want to set up the minimal Python REST API project structure with basic routing and logging, so that I have a foundation to build the chatbot endpoints and automated tests.
**Business Value:** Provides the foundational infrastructure required to host the chatbot orchestrator and exposes a stable REST interface for the eventual UI/CLI.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Health Check Endpoint**
* **Given** the backend server is running locally
* **When** a GET request is sent to the `/health` endpoint
* **Then** the server responds with a `200 OK` status and a JSON payload indicating the service is healthy (e.g., `{"status": "ok"}`).

* **Scenario 2: Project Structure and Environment**
* **Given** a fresh clone of the new repository
* **When** following the setup instructions in the README
* **Then** the local development environment initializes successfully and the test suite can be run.

**TDD Test Scenarios:**

* *Test:* `test_health_endpoint_returns_200` -> Assert GET `/health` yields status code 200.
* *Test:* `test_health_endpoint_payload` -> Assert GET `/health` response body strictly matches `{"status": "ok"}`.
* *Test:* `test_unhandled_route_returns_404` -> Assert GET `/invalid-route` returns a standard 404 response.

**Dependencies:** US-1.1 (Only to ensure the repo structure aligns with the architectural decisions).
**Definition of Done:**

* REST API framework (e.g., FastAPI/Flask) is installed and configured.
* `/health` endpoint is implemented and functional.
* Test framework (e.g., `pytest`) is configured.
* All TDD tests pass.
* Minimal `README.md` includes local setup commands (e.g., `pip install -r requirements.txt`, `pytest`).

**Priority:** 2 (High).


### US-1.3: Implement Basic LLM Integration and Test Endpoint

**User Story:** As an AI engineer, I want to integrate the backend with the target LLM API and expose a basic test endpoint, so that I can verify the application can successfully authenticate, send prompts, and receive responses from the LLM.
**Business Value:** Proves the critical technical path for natural language processing, validating API keys, network access, and basic client implementation before adding complex RAG context.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Successful LLM Invocation**
* **Given** a valid LLM API key and configuration
* **When** a POST request containing a simple text prompt is sent to `/api/v1/chat/test`
* **Then** the API forwards the prompt to the LLM and returns the LLM's text response with a `200 OK` status.

* **Scenario 2: Missing or Invalid Authentication**
* **Given** an invalid or missing LLM API key
* **When** the `/api/v1/chat/test` endpoint is invoked
* **Then** the system catches the authentication error gracefully and returns a `500 Internal Server Error` (or `502 Bad Gateway`) with a clean error message detailing an "upstream authentication failure."

**TDD Test Scenarios:**

* *Test:* `test_llm_test_endpoint_success` -> Mock the LLM client to return a static string; assert the endpoint returns 200 and matches the mocked string.
* *Test:* `test_llm_test_endpoint_auth_failure` -> Mock the LLM client to raise an authentication exception; assert the endpoint catches it and returns the expected 500/502 HTTP status and error JSON.
* *Test:* `test_llm_test_endpoint_timeout` -> Mock the LLM client to raise a timeout exception; assert the endpoint returns a `504 Gateway Timeout` or equivalent handled response.
* *Test:* `test_llm_test_endpoint_empty_prompt` -> Assert POSTing an empty prompt returns a `400 Bad Request` prior to calling the LLM.

**Dependencies:** US-1.2 (Requires the API skeleton and test framework).
**Definition of Done:**

* LLM client (e.g., OpenAI Python SDK or standard HTTP client) is integrated.
* `POST /api/v1/chat/test` is implemented.
* Environment variables (e.g., `.env`) are configured to handle API keys securely (never hardcoded).
* All TDD tests pass (using mocks for external LLM calls).

**Priority:** 3 (High).

---

# Epic 2: Knowledge Graph Tool Implementation

* **Objective:** Enable the LLM to query the existing Knowledge Graph by implementing focused, deterministic function-calling tools.
* **Key Deliverables:**
* Implementation of `find_entity(name)` to locate specific codebase elements.
* Implementation of `get_relationships(entity, relationship_type, direction)`.
* Implementation of `find_dependencies(entity)` and `find_dependents(entity)`.
* Validation that the LLM can successfully use these tools to extract facts from the graph database.

### Analysis of Epic 2 Scope

Epic 2 (Knowledge Graph Tool Implementation) is focused strictly on building the deterministic functions that will allow the LLM to query the existing Knowledge Graph, and validating that the LLM can successfully invoke them. According to the Master Prompt, this requires implementing four specific tools (`find_entity`, `get_relationships`, `find_dependencies`, `find_dependents`) and ensuring they return verifiable facts without hallucination.

**Assumptions & Clarifications:**

* **Assumption:** The underlying CodeGraph AI APIs or graph database queries required to fetch this data are already functional and accessible based on the API contracts defined in Epic 1 (US-1.1). These stories focus on building the *wrapper tools* for the LLM, not rebuilding the graph queries themselves.
* **Assumption:** `find_dependencies` and `find_dependents` are treated as specialized, convenience wrappers (likely built on top of `get_relationships`) designed to reduce the cognitive load and multi-step reasoning required by the LLM for impact analysis queries.
* **Assumption:** To adhere to TDD, we will mock the actual CodeGraph AI backend responses during testing to ensure these tools are tested in isolation.

Here is the smallest logical set of user stories to deliver Epic 2 end-to-end.


### US-2.1: Knowledge Graph Entity Search for Valid Context Retrieval

**User Story:** As a chatbot orchestrator, I want a specialized tool to search for a specific entity by name in the Knowledge Graph, so that I can establish a valid starting node for context retrieval without hallucinating entity names.
**Business Value:** This is the foundational tool. It grounds the LLM in reality by forcing it to verify the existence and exact identifier of a codebase component before attempting to traverse its relationships.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Entity exists**
* **Given** a valid entity name exists in the Knowledge Graph
* **When** the `find_entity(name)` tool is invoked
* **Then** it returns the standard entity object (including its unique ID, type, and exact name) as a JSON-serializable dictionary.

* **Scenario 2: Entity does not exist**
* **Given** an entity name that does not exist in the Knowledge Graph
* **When** the `find_entity(name)` tool is invoked
* **Then** it returns a clear "not found" response indicator rather than throwing an unhandled exception.

**TDD Test Scenarios:**

* *Test:* `test_find_entity_exact_match` -> Mock the backend API to return an entity; assert the tool parses and returns the expected dictionary.
* *Test:* `test_find_entity_not_found` -> Mock the backend API to return empty/404; assert the tool returns a graceful "not found" payload.
* *Test:* `test_find_entity_backend_timeout` -> Mock a timeout from the backend API; assert the tool catches it and returns a standard error message string suitable for the LLM.

**Dependencies:** US-1.1 (API Contracts).
**Definition of Done:**

* `find_entity` Python function is implemented.
* Function includes clear docstrings formatted for LLM tool consumption.
* All TDD test cases pass using mocked backend responses.
* Tool strictly adheres to the input/output schema defined in US-1.1.
**Priority:** 1 (Highest — Prerequisite for all other traversals).


### US-2.2: Retrieve Entity Relationships for Contextual Answers

**User Story:** As a chatbot orchestrator, I want a tool to retrieve the surrounding relationships for a verified entity, so that I can extract structural context and connections to provide detailed engineering answers.
**Business Value:** Enables the LLM to answer "how does this work" or "what connects to this" by traversing the graph database iteratively.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Valid retrieval**
* **Given** a valid entity ID and relationship direction (inbound, outbound, or both)
* **When** the `get_relationships(entity, relationship_type, direction)` tool is invoked
* **Then** it returns a structured list of connected nodes and the specific edge types connecting them.

* **Scenario 2: No relationships found**
* **Given** a valid entity ID that has no connections matching the requested parameters
* **When** the tool is invoked
* **Then** it returns an empty list `[]`.

**TDD Test Scenarios:**

* *Test:* `test_get_relationships_outbound_success` -> Provide mock entity and "outbound" direction; assert correct connected nodes are returned.
* *Test:* `test_get_relationships_inbound_success` -> Provide mock entity and "inbound" direction; assert correct connected nodes are returned.
* *Test:* `test_get_relationships_empty_result` -> Mock an entity with no connections; assert an empty list is returned.
* *Test:* `test_get_relationships_invalid_entity` -> Provide a null or malformed entity ID; assert a validation error is returned.

**Dependencies:** US-2.1 (Depends on the entity schema).
**Definition of Done:**

* `get_relationships` Python function is implemented with LLM-friendly docstrings.
* All TDD test cases pass.
* Tool response data is minimized to exclude unnecessary graph metadata, keeping the LLM context window clean.
**Priority:** 2 (High).


### US-2.3: Trace Entity Dependencies for Impact Analysis

**User Story:** As a chatbot orchestrator, I want dedicated tools for finding what an entity depends on and what depends on it, so that the LLM can efficiently answer impact analysis questions without needing to manually map complex relationship queries.
**Business Value:** Greatly improves the reliability and speed of answering "what is impacted if I change X?" queries by providing a simplified, direct interface for the LLM.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Find Dependencies (Downstream)**
* **Given** a valid entity ID
* **When** `find_dependencies(entity)` is invoked
* **Then** it returns a list of components that the given entity relies upon to function.

* **Scenario 2: Find Dependents (Upstream / Impact)**
* **Given** a valid entity ID
* **When** `find_dependents(entity)` is invoked
* **Then** it returns a list of components that rely on the given entity.

**TDD Test Scenarios:**

* *Test:* `test_find_dependencies_returns_list` -> Mock downstream components; assert function returns them.
* *Test:* `test_find_dependents_returns_list` -> Mock upstream components; assert function returns them.
* *Test:* `test_find_dependencies_none_exist` -> Assert empty list returned when no dependencies exist.

**Dependencies:** US-2.1 (Entity schema). May internally reuse logic from US-2.2.
**Definition of Done:**

* Both functions are implemented with clear, distinct docstrings.
* All TDD tests pass.
**Priority:** 2 (High).


### US-2.4: Validate LLM Function Calling with KG Tools

**User Story:** As an AI engineer, I want to bind the implemented Knowledge Graph tools to the LLM client, so that the LLM can autonomously recognize when to use a tool, format the execution request, and process the resulting tool output into a conversational response.
**Business Value:** This is the integration point that proves the core mechanics of the Agentic architecture. It transforms the system from a simple text-generator into an active retriever of CodeGraph facts.

**Acceptance Criteria — Given/When/Then:**

* **Scenario 1: Autonomous Tool Selection**
* **Given** an LLM initialized with the 4 KG tools
* **When** prompted with "Find the PaymentService entity"
* **Then** the LLM pauses generation and outputs a structured tool call request specifically for `find_entity("PaymentService")`.

* **Scenario 2: Handling Tool Responses**
* **Given** an active tool call generated by the LLM
* **When** the backend executes the tool and returns the JSON result to the LLM
* **Then** the LLM resumes generation and incorporates the factual tool result into its final text response.

**TDD Test Scenarios:**

* *Test:* `test_llm_tool_binding` -> Assert that the tool schemas are correctly formatted and accepted by the LLM provider's API during initialization without validation errors.
* *Test:* `test_llm_invokes_correct_tool` -> Using a mocked LLM response, assert that the orchestrator correctly parses a tool-call request and routes it to the correct local Python function.
* *Test:* `test_orchestrator_returns_tool_data_to_llm` -> Assert that the orchestrator correctly formats the tool's return value into the necessary `tool_message` structure required by the LLM to continue the conversation.

**Dependencies:** US-1.3 (Base LLM integration), US-2.1, US-2.2, US-2.3.
**Definition of Done:**

* LLM orchestration logic is updated to handle multi-turn function calling (Tool Call -> Tool Execution -> Tool Response -> Final Answer).
* All tools are successfully bound to the LLM client.
* TDD tests for the orchestrator routing logic pass.
**Priority:** 3 (High — Completes Epic 2).

---

# Epic 3: Hybrid RAG Integration & Context Orchestration

* **Objective:** Connect the existing document/source code vector retrieval system and build the intelligence layer that decides how to fetch and combine information.
* **Key Deliverables:**
* Implementation of the `hybrid_search(query, filters)` tool leveraging the existing Codegraph AI Vector DB.
* Context Orchestrator that allows the LLM to choose between KG retrieval, Hybrid RAG, or both.
* Prompt engineering to ensure responses strictly follow the "Grounded Answer" format (Answer, Flow, Evidence, Confidence) without exposing chain-of-thought.

---

# Epic 4: Minimal Viable User Interface

* **Objective:** Build a simple, functional interface (Web UI or CLI) for developers to interact with the Copilot.
* **Key Deliverables:**
* A basic chat interface supporting session-based conversation history.
* Clear visual distinction between the LLM's explanation and the retrieved evidence/sources.
* Implementation of loading states and error handling for missing information.

---

# Epic 5: MVP Evaluation and Handoff

* **Objective:** Validate the chatbot's effectiveness, ensure it meets the "Definition of Done," and package the project for future iterations.
* **Key Deliverables:**
* Creation of a 20-question engineering benchmark dataset (covering architecture, dependencies, impacts, etc.).
* Evaluation results focusing on correctness, grounding, and hallucination rates.
* Finalized documentation including a README, setup instructions, known limitations, and an architecture diagram.