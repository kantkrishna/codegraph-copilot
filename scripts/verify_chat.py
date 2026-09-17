# scripts/verify_chat.py

# CLI utility to run functional chat cycles against local or live KG.

import sys
from backend.orchestrator import run_chat_cycle
from tests.integration.test_chat_functional import FunctionalMockKGClient


def main() -> None:
    kg_client = FunctionalMockKGClient()
    print("=== CodeGraph Engineering Copilot (KG Tools Verification CLI) ===")
    print("Type your query or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("Developer > ").strip()
            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            answer = run_chat_cycle(user_input, kg_client)
            print(f"\nCopilot >\n{answer}\n")
            print("-" * 50)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()