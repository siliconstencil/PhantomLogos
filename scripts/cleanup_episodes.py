import os
import sqlite3


def cleanup_episodes():
    db_path = "data/mnemosyne.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Delete stability_test entries
        cursor.execute(
            "DELETE FROM episodes WHERE action LIKE '%stability_test%' OR session_id LIKE '%test_session%'"
        )
        deleted_count = cursor.rowcount

        conn.commit()
        print(f"Success: {deleted_count} test episodes deleted from Mnemosyne Axis 1.")

        conn.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    cleanup_episodes()
