# Makefile

.PHONY: install test typecheck check chat run clean

# Install dependencies using uv
install:
	uv sync

# Run all tests with coverage
test:
	uv run pytest

# Run strict type checking
typecheck:
	uv run mypy .

# Run both type checks and tests
check: typecheck test

# Run the interactive CLI chat script
chat:
	uv run python -m scripts.verify_chat

rag_eval:
	uv run python -m scripts.rag_evaluator

run_eval:
	uv run python -m scripts.run_evaluation

# Run the local REST API server
run:
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8002

# Clean cache directories
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +