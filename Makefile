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
	uv run python scripts/verify_chat.py

# Run the local REST API server
run:
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Clean cache directories
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +