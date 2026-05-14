import os
import sqlite3
import sys


# Standard reliability reset utility
def reset_all(agent_id=None):
    db_path = "data/reliability.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if agent_id:
            cursor.execute(
                "UPDATE agent_reliability SET reliability_score = 1.0, total_violations = 0 WHERE agent_id = ?",
                (agent_id,),
            )
            print(f"Success: Reliability for '{agent_id}' reset to 1.0.")
        else:
            cursor.execute(
                "UPDATE agent_reliability SET reliability_score = 1.0, total_violations = 0"
            )
            print("Success: All agent reliability scores reset to 1.0.")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error during reliability reset: {e}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    reset_all(target)
