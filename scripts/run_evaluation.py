# scripts/run_evaluation.py

"""
Automated evaluation runner for Codegraph Copilot.
Queries the live Copilot API, parses grounded markdown responses, sends
payloads to the RAGAS evaluator microservice, and logs detailed diagnostic reports.
"""

import os
import re
import json
import httpx

project_root = os.path.dirname(os.path.dirname(__file__))

# API Endpoints
COPILOT_URL = "http://localhost:8002/api/v1/chat"
EVAL_URL = "http://localhost:8001/evaluate"

# File Paths
BENCHMARK_FILE = os.path.join(project_root, "tests", "evaluation", "benchmark.json")
REPORT_FILE = os.path.join(project_root, "tests", "evaluation", "evaluation_report.json")


def parse_grounded_response(raw_text: str) -> dict:
    """
    Normalizes Windows/Unix line endings and extracts the Answer and Evidence.
    """
    if not raw_text or not raw_text.strip():
        return {
            "answer": "No response returned.",
            "contexts": ["No context provided."]
        }

    # Normalize Windows CRLF to standard LF
    text = raw_text.replace("\r\n", "\n").strip()

    # 1. Extract Answer section
    answer_match = re.search(r"###\s*Answer\s*\n(.*?)(?=\n###|\Z)", text, re.DOTALL)
    answer = answer_match.group(1).strip() if answer_match else text

    # 2. Extract Evidence section
    evidence_match = re.search(r"###\s*Evidence\s*\n(.*?)(?=\n###|\Z)", text, re.DOTALL)
    if evidence_match:
        evidence_block = evidence_match.group(1).strip()
        # Split individual bullet points into separate context strings
        # bullet_items = [
        #     line.lstrip("-* ").strip()
        #     for line in evidence_block.split("\n")
        #     if line.strip() and not line.strip().startswith("#")
        # ]
        # contexts = bullet_items if bullet_items else [evidence_block]
        contexts = [evidence_block]
    else:
        contexts = [text]

    return {
        "answer": answer,
        "contexts": contexts
    }


def query_copilot(client: httpx.Client, question: str) -> dict:
    """
    Calls the Copilot API endpoint and returns both raw and parsed structures.
    """
    payload = {"prompt": question}
    try:
        response = client.post(COPILOT_URL, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        raw_response = data.get("response", "")
        parsed = parse_grounded_response(raw_response)
        parsed["raw_response"] = raw_response
        return parsed

    except httpx.RequestError as e:
        print(f"  [ERROR] Network error contacting Copilot: {e}")
        return {"answer": "", "contexts": [], "raw_response": f"Network Error: {e}"}
    except httpx.HTTPStatusError as e:
        print(f"  [ERROR] Copilot returned HTTP {e.response.status_code}: {e.response.text}")
        return {"answer": "", "contexts": [], "raw_response": f"HTTP {e.response.status_code}"}


def run_batch_evaluation():
    if not os.path.exists(BENCHMARK_FILE):
        print(f"Error: {BENCHMARK_FILE} not found.")
        return

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)

    evaluation_results = []
    total = len(benchmark_data)
    print(f"\n==================================================")
    print(f" Starting Evaluation for {total} Benchmark Cases")
    print(f"==================================================\n")

    with httpx.Client(timeout=120.0) as client:
        for idx, item in enumerate(benchmark_data, start=1):
            question = item["question"]
            expected_answer = item["expected_answer"]
            category = item.get("category", "General")

            print(f"[{idx}/{total}] [{category.upper()}] Query: \"{question}\"")
            print(f"  Expected Answer: {expected_answer}")

            # 1. Fetch Copilot answer
            copilot_data = query_copilot(client, question)
            print(f"  Copilot Answer:  {copilot_data['answer']}")
            print(f"  Context Chunks:  {len(copilot_data['contexts'])} retrieved")
            for c_idx, chunk in enumerate(copilot_data["contexts"], 1):
                clean_chunk = (chunk[:100] + "...") if len(chunk) > 100 else chunk
                print(f"    - Chunk {c_idx}: {clean_chunk}")

            # 2. Guard against empty submissions
            if not copilot_data["answer"].strip():
                print("  [SKIP] Copilot produced empty answer.\n")
                continue

            # 3. Payload to Evaluator
            eval_payload = {
                "developer_query": question,
                "codegraph_contexts": copilot_data["contexts"],
                "copilot_answer": copilot_data["answer"],
                "ground_truth": expected_answer,
            }

            try:
                eval_resp = client.post(EVAL_URL, json=eval_payload, timeout=120.0)
                eval_resp.raise_for_status()
                scores = eval_resp.json()

                f_score = scores.get("faithfulness", 0.0)
                r_score = scores.get("answer_relevance", 0.0)
                p_score = scores.get("context_precision", 0.0)

                print(f"  Scores: Faithfulness: {f_score:.2f} | Relevancy: {r_score:.2f} | Precision: {p_score:.2f}")

                evaluation_results.append({
                    "case_id": idx,
                    "category": category,
                    "question": question,
                    "expected_answer": expected_answer,
                    "copilot_answer": copilot_data["answer"],
                    "raw_response": copilot_data["raw_response"],
                    "contexts_used": copilot_data["contexts"],
                    "scores": scores
                })

            except httpx.RequestError as e:
                print(f"  [EVAL ERROR] Network error contacting Evaluator: {e}")
            except httpx.HTTPStatusError as e:
                print(f"  [EVAL ERROR] Evaluator HTTP {e.response.status_code}: {e.response.text}")

            print("-" * 50)

    # Save detailed evaluation report
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, indent=4)

    print(f"\nEvaluation Complete! Full diagnostics saved to:\n{REPORT_FILE}\n")


if __name__ == "__main__":
    run_batch_evaluation()