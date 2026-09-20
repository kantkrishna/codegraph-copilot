# scripts/verify_chat.py

# CLI utility to run functional chat cycles against the live Neo4j Knowledge Graph.

from backend.orchestrator import run_chat_cycle
from backend.kgtools.neo4j_client import Neo4jKGClient

def main() -> None:
    print("=== Connecting to Neo4j Knowledge Graph (CodeGraph AI) ===")
    
    # Initialize the real database client
    real_client = Neo4jKGClient()
    
    print("Connected successfully! (Using REAL CodeGraph Data)")
    print("Type your microservices queries below, or 'exit' to quit.\n")

    try:
        while True:
            user_input = input("Developer > ").strip()
            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            # The real_client now handles both KG and RAG interfaces
            answer = run_chat_cycle(user_input, kg_client=real_client, rag_client=real_client)
            print(f"\nCopilot >\n{answer}\n")
            print("-" * 50)
    finally:
        real_client.close()

if __name__ == "__main__":
    main()