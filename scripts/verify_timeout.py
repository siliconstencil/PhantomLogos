import asyncio
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.clotho.orchestrator import with_timeout


async def test_node_timeout():
    print("=== Testing Orchestrator Node Timeout ===")

    async def slow_node(state):
        await asyncio.sleep(2.0)
        return {"status": "done"}

    # Wrap with 1s timeout
    wrapped = with_timeout(slow_node, seconds=1.0)

    state = {"session_id": "test_timeout"}
    result = await wrapped(state)

    print(f"Result: {result}")

    if "reflection_insight" in result and "Node timeout" in result["reflection_insight"]:
        print("SUCCESS: Node timeout correctly caught and reported.")
        return True
    else:
        print("FAILED: Node timeout was not caught or returned wrong data.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_node_timeout())
    sys.exit(0 if success else 1)
