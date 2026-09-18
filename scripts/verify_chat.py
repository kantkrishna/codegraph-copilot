# scripts/verify_chat.py

# CLI utility to run functional chat cycles against the live Neo4j Knowledge Graph.

import sys
import os
from pathlib import Path

# Add project root directory to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.orchestrator import run_chat_cycle
from backend.kgtools.neo4j_client import Neo4jKGClient

def main() -> None:
    print("=== Connecting to Neo4j Knowledge Graph (CodeGraph AI) ===")
    kg_client = Neo4jKGClient()
    
    print("Connected successfully!")
    print("Type your microservices queries below, or 'exit' to quit.\n")

    try:
        while True:
            user_input = input("Developer > ").strip()
            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            answer = run_chat_cycle(user_input, kg_client)
            print(f"\nCopilot >\n{answer}\n")
            print("-" * 50)
    finally:
        kg_client.close()

if __name__ == "__main__":
    main()