# tests/unit/kgtools/test_evaluation.py

# This file contains the TDD unit tests for Epic 5: Evaluation and Handoff.
# It validates the benchmark dataset structure, the evaluation runner logic,
# and the presence of required documentation sections.

import os
import json
from unittest.mock import patch, MagicMock
from typing import Any
import pytest

# Constants for paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
BENCHMARK_PATH = os.path.join(PROJECT_ROOT, "tests", "evaluation", "benchmark.json")
README_PATH = os.path.join(PROJECT_ROOT, "README.md")

def test_benchmark_dataset_validity() -> None:
    """US-5.1 AC1 & AC2: Validates the benchmark dataset has 20 unique questions and correct schema."""
    assert os.path.exists(BENCHMARK_PATH), f"Benchmark dataset missing at {BENCHMARK_PATH}"
    
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert isinstance(data, list), "Dataset must be a JSON array."
    assert len(data) == 20, f"Expected 20 questions, found {len(data)}."
    
    valid_categories = {"Structural", "Semantic", "Hybrid", "Out-of-Scope"}
    seen_questions = set()
    
    for item in data:
        assert "question" in item, "Missing 'question' key."
        assert "expected_answer" in item, "Missing 'expected_answer' key."
        assert "category" in item, "Missing 'category' key."
        
        assert isinstance(item["question"], str) and item["question"].strip(), "Invalid question."
        assert isinstance(item["expected_answer"], str) and item["expected_answer"].strip(), "Invalid expected_answer."
        assert item["category"] in valid_categories, f"Invalid category: {item['category']}"
        
        seen_questions.add(item["question"])
        
    assert len(seen_questions) == 20, "Questions must be unique."

@patch("urllib.request.urlopen")
def test_evaluation_runner_success(mock_urlopen: MagicMock, tmp_path: Any) -> None:
    """US-5.2 AC1 & AC2: Evaluator processes dataset and writes report."""
    from scripts.run_evaluation import run_evaluator
    
    # Setup mock API response
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"response": "Mocked Copilot Answer"}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # Dummy dataset
    dummy_data = [
        {"question": "Q1", "expected_answer": "A1", "category": "Structural"},
        {"question": "Q2", "expected_answer": "A2", "category": "Semantic"}
    ]
    dummy_in = tmp_path / "dummy_in.json"
    dummy_out = tmp_path / "dummy_out.json"
    
    with open(dummy_in, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)
        
    run_evaluator(str(dummy_in), str(dummy_out), "http://fake-api/chat")
    
    assert os.path.exists(dummy_out)
    with open(dummy_out, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    assert len(results) == 2
    assert results[0]["question"] == "Q1"
    assert results[0]["actual_response"] == "Mocked Copilot Answer"
    assert results[0]["status_code"] == 200

@patch("urllib.request.urlopen")
def test_evaluation_runner_api_failure(mock_urlopen: MagicMock, tmp_path: Any) -> None:
    """US-5.2 AC3: Evaluator handles 500 errors and timeouts without crashing."""
    from scripts.run_evaluation import run_evaluator
    from urllib.error import HTTPError
    
    # Mock the API call to raise an HTTPError (e.g., Neo4j OOM crash simulation)
    mock_urlopen.side_effect = HTTPError("http://fake-api", 500, "Internal Server Error", {}, None)
    
    dummy_data = [{"question": "Q1", "expected_answer": "A1", "category": "Structural"}]
    dummy_in = tmp_path / "dummy_in_fail.json"
    dummy_out = tmp_path / "dummy_out_fail.json"
    
    with open(dummy_in, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)
        
    run_evaluator(str(dummy_in), str(dummy_out), "http://fake-api/chat")
    
    assert os.path.exists(dummy_out)
    with open(dummy_out, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    assert len(results) == 1
    assert results[0]["status_code"] == 500
    assert "Internal Server Error" in results[0]["actual_response"]

def test_readme_contains_required_sections() -> None:
    """US-5.3 AC1, AC2, AC3: README contains required documentation headers."""
    assert os.path.exists(README_PATH), f"README missing at {README_PATH}"
    
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "## Setup Instructions" in content, "Missing Setup Instructions header"
    assert "## Architecture" in content, "Missing Architecture header"
    assert "## Known Limitations" in content, "Missing Known Limitations header"
    assert "## Evaluation Summary" in content, "Missing Evaluation Summary header"