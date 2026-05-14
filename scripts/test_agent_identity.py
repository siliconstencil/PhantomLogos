import os
import sqlite3
import time

from src.utils.logging_config import setup_logger


def test_identity_logging():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")

    logger = setup_logger("test_identity")

    test_session = f"session_{int(time.time())}"
    test_agent = "sophia_test"

    print("--- Agent Identity Logging Test ---")
    print(f"Logging test event for agent '{test_agent}' in session '{test_session}'...")

    # 1. Log event with extra params
    logger.info(
        "Identity verification event",
        extra={"agent_id": test_agent, "session_id": test_session, "tool_name": "test_tool"},
    )

    # Give it a tiny bit to commit
    time.sleep(0.5)

    # 2. Verify in DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT session_id, agent_id, tool_name, message
        FROM operational_logs_v2
        WHERE session_id = ? AND agent_id = ?
        ORDER BY id DESC LIMIT 1
    """,
        (test_session, test_agent),
    )

    result = cursor.fetchone()

    if result:
        print("  [PASS] Log found in database.")
        print(f"  [DATA] Session: {result[0]}")
        print(f"  [DATA] Agent:   {result[1]}")
        print(f"  [DATA] Tool:    {result[2]}")
        print(f"  [DATA] Message: {result[3]}")

        if result[0] == test_session and result[1] == test_agent:
            print("  [SUCCESS] Identity and Session correctly preserved.")
        else:
            print("  [FAIL] Data mismatch in database.")
    else:
        print("  [FAIL] Log not found in database!")

    conn.close()
    print("--- Test Complete ---")


if __name__ == "__main__":
    test_identity_logging()
