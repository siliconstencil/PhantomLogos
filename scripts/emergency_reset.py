import os
import sqlite3


def reset_reliability():
    db_path = "data/reliability.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Reset Sophia
        cursor.execute(
            "UPDATE agent_reliability SET reliability_score = 1.0, total_violations = 0 WHERE agent_id = 'sophia'"
        )
        # Reset verify_node
        cursor.execute(
            "UPDATE agent_reliability SET reliability_score = 1.0, total_violations = 0 WHERE agent_id = 'verify_node'"
        )

        conn.commit()
        print("Success: Reliability scores for 'sophia' and 'verify_node' have been reset to 1.0.")

        # Verify
        cursor.execute(
            "SELECT agent_id, reliability_score FROM agent_reliability WHERE agent_id IN ('sophia', 'verify_node')"
        )
        rows = cursor.fetchall()
        for row in rows:
            print(f"Agent: {row[0]}, Score: {row[1]}")

        conn.close()
    except Exception as e:
        print(f"Error during reset: {e}")


def reset_failure_memory():
    db_path = "data/mnemosyne.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE failure_memory SET status = 'resolved' WHERE status = 'active'")
        resolved = cursor.rowcount
        conn.commit()
        print(f"Success: Resolved {resolved} active failure-memory rows.")
        conn.close()
    except Exception as e:
        print(f"Error during failure-memory reset: {e}")


if __name__ == "__main__":
    reset_reliability()
    reset_failure_memory()
