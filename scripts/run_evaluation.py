# scripts/run_evaluation.py

# This script automates the evaluation of the Copilot against a benchmark dataset.
# It reads benchmark.json, executes POST requests, and writes an evaluation_report.json.

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any

def run_evaluator(dataset_path: str, output_path: str, api_url: str = "http://localhost:8000/api/v1/chat") -> None:
    """
    Reads a JSON dataset, POSTs each question to the API, and writes the results.
    Catches and logs HTTP errors and timeouts to maintain resilience (US-5.2 AC3).
    """
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, str]] = json.load(f)

    results: List[Dict[str, Any]] = []

    print(f"Starting evaluation of {len(dataset)} questions...")

    for item in dataset:
        question = item["question"]
        expected = item["expected_answer"]
        
        payload = json.dumps({"prompt": question}).encode("utf-8")
        req = urllib.request.Request(
            api_url, 
            data=payload, 
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        status_code = 500
        actual_response = ""
        
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                status_code = response.getcode()
                response_body = response.read().decode("utf-8")
                actual_response = json.loads(response_body).get("response", "")
        except urllib.error.HTTPError as e:
            status_code = e.code
            actual_response = f"HTTP Error: {e.reason}"
        except Exception as e:
            status_code = 500
            actual_response = f"Exception: {str(e)}"
            
        results.append({
            "question": question,
            "expected_answer": expected,
            "category": item["category"],
            "actual_response": actual_response,
            "status_code": status_code
        })
        print(f"Processed: '{question}' -> Status: {status_code}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Evaluation complete. Results saved to {output_path}")

if __name__ == "__main__":
    import os
    project_root = os.path.dirname(os.path.dirname(__file__))
    dataset = os.path.join(project_root, "tests", "evaluation", "benchmark.json")
    output = os.path.join(project_root, "evaluation_report.json")
    run_evaluator(dataset, output)