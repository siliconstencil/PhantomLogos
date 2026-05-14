import asyncio
import os
import sqlite3
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clotho.ergon.theoria import reflection_node


async def test_extraction():
    print("Initializing E2E Reflection Test (Authorized)...")

    test_text = """
    The Antigravity system uses Mnemosyne for 14-axis memory management.
    Clotho is responsible for orchestrating the agents.
    The project is configured in config.yaml and depends on Ollama for LLM tasks.
    """

    # Mock state for LangGraph node
    state = {
        "task": "Test semantic extraction",
        "draft": test_text,
        "session_id": "test_e2e_session_v2",
        "tool_results": [],
        "critique": {"overall_score": 0.8},
    }

    print("\n--- Executing reflection_node ---")
    result = await reflection_node(state)
    print(f"Node result: {result}")

    # Verify DB
    db_path = "D:/Hank/data/mnemosyne.db"
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM semantic_relations WHERE session_id = 'test_e2e_session_v2'"
    ).fetchone()[0]
    conn.close()

    print("\n--- Summary ---")
    print(f"Total Relations for this session in DB: {count}")
    if count > 0:
        print("SUCCESS: E2E Pipeline (Extraction + Storage) is working.")
    else:
        # Check if anything at all is in DB
        conn = sqlite3.connect(db_path)
        total_count = conn.execute("SELECT COUNT(*) FROM semantic_relations").fetchone()[0]
        conn.close()
        print(f"Total Relations (Global): {total_count}")
        print("FAILURE: DB session record missing.")


if __name__ == "__main__":
    asyncio.run(test_extraction())
