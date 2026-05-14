import asyncio
import sqlite3
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.gnosis.axis_8_meta import _build_axis_8_failures


async def test_reliability_enforcement():
    print("=== Phase 5 Verification: Reliability Enforcement ===")

    db_path = "data/reliability.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Force low reliability
        print("Simulating critical reliability failure (0.0)...")
        cursor.execute(
            "UPDATE agent_reliability SET reliability_score = 0.0 WHERE agent_id = 'sophia'"
        )
        conn.commit()

        # 2. Check enforcement
        lines, block_signal = await _build_axis_8_failures("test task")
        print(f"Block Signal: {block_signal}")

        if (
            block_signal["block"] == True
            and "reliability critical" in (block_signal["reason"] or "").lower()
        ):
            print("SUCCESS: Phase 5 Reliability lock verified.")
        else:
            print(
                f"FAILURE: Lock not triggered or reason incorrect. Reason: {block_signal['reason']}"
            )

        # 3. Restore reliability
        print("Restoring reliability to 1.0...")
        cursor.execute(
            "UPDATE agent_reliability SET reliability_score = 1.0 WHERE agent_id = 'sophia'"
        )
        conn.commit()

    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(test_reliability_enforcement())
