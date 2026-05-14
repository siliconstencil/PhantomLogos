import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

import asyncio

from cognition.sophia.gnosis import get_dynamic_context


async def run_full_diag():
    sid = "test_session"
    hint = "test task"

    print("Starting Full Context Diagnostic...")
    start = time.time()
    try:
        stable, dynamic, _ = await get_dynamic_context(
            agent_id="sophia", task_hint=hint, session_id=sid
        )
        context = f"{stable}\n\n{dynamic}"
        print(f"Full Context Generation: OK ({time.time() - start:.2f}s)")
        print(f"Context Length: {len(context)} chars")
        # print(context[:500] + "...")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_full_diag())
