import asyncio
import sys
from pathlib import Path

import numpy as np

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.gnosis.axis_6_semantic import _build_axis_6


async def test_semantic():
    print("=== Phase 3 Verification: Semantic Store ===")

    # Use a dummy vector (zeros) for search - should still match seeded data due to hybrid/session
    dummy_vec = np.zeros(256)
    session_id = "system"  # seeded as system
    task_hint = "What is Phantom Logos?"

    lines = await _build_axis_6(task_hint, session_id, dummy_vec)

    print("Axis 6 Output:")
    for line in lines:
        print(f"  {line}")

    if any("MNEMOSYNE AXIS 6" in line for line in lines) and len(lines) > 1:
        print("SUCCESS: Phase 3 Semantic repair verified.")
    else:
        print("FAILURE: Semantic output missing or empty.")


if __name__ == "__main__":
    asyncio.run(test_semantic())
