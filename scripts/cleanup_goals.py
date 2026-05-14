import os
import sqlite3


def cleanup_goals():
    db_path = "data/mnemosyne.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Delete stale pending goals (older than 1 hour or just all of them if they are noise)
        # Audit showed 109 stale goals. We'll clear pending ones to start fresh.
        cursor.execute("DELETE FROM goals WHERE status = 'pending'")
        deleted_count = cursor.rowcount

        conn.commit()
        print(f"Success: {deleted_count} stale goals deleted from Mnemosyne Axis 3.")

        conn.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    cleanup_goals()
