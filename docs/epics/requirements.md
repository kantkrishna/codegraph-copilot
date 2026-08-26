# Codegraph Copilot Epics and User Stories: AI Chatbot for Codegraph

## Table of Contents

* [Epic 1: System Analysis and Foundation](#epic-1-system-analysis-and-foundation)
  * [US-1.1: Technical Spike — Analyze CodeGraph AI Architecture and Define API Contracts](#us-11-technical-spike--analyze-codegraph-ai-architecture-and-define-api-contracts)
  * [US-1.2: Initialize Python REST API Backend Skeleton](#us-12-initialize-python-rest-api-backend-skeleton)
  * [US-1.3: Implement Basic LLM Integration and Test Endpoint](#us-13-implement-basic-llm-integration-and-test-endpoint)

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

**Epic 2: Knowledge Graph Tool Implementation**

* **Objective:** Enable the LLM to query the existing Knowledge Graph by implementing focused, deterministic function-calling tools.
* **Key Deliverables:**
* Implementation of `find_entity(name)` to locate specific codebase elements.
* Implementation of `get_relationships(entity, relationship_type, direction)`.
* Implementation of `find_dependencies(entity)` and `find_dependents(entity)`.
* Validation that the LLM can successfully use these tools to extract facts from the graph database.



**Epic 3: Hybrid RAG Integration & Context Orchestration**

* **Objective:** Connect the existing document/source code vector retrieval system and build the intelligence layer that decides how to fetch and combine information.
* **Key Deliverables:**
* Implementation of the `hybrid_search(query, filters)` tool leveraging the existing Codegraph AI Vector DB.
* Context Orchestrator that allows the LLM to choose between KG retrieval, Hybrid RAG, or both.
* Prompt engineering to ensure responses strictly follow the "Grounded Answer" format (Answer, Flow, Evidence, Confidence) without exposing chain-of-thought.



**Epic 4: Minimal Viable User Interface**

* **Objective:** Build a simple, functional interface (Web UI or CLI) for developers to interact with the Copilot.
* **Key Deliverables:**
* A basic chat interface supporting session-based conversation history.
* Clear visual distinction between the LLM's explanation and the retrieved evidence/sources.
* Implementation of loading states and error handling for missing information.



**Epic 5: MVP Evaluation and Handoff**

* **Objective:** Validate the chatbot's effectiveness, ensure it meets the "Definition of Done," and package the project for future iterations.
* **Key Deliverables:**
* Creation of a 20-question engineering benchmark dataset (covering architecture, dependencies, impacts, etc.).
* Evaluation results focusing on correctness, grounding, and hallucination rates.
* Finalized documentation including a README, setup instructions, known limitations, and an architecture diagram.