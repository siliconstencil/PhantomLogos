import os
import sqlite3

from src.utils.project_path import get_project_root


def migrate():
    db_path = os.path.join(get_project_root(), "data/reliability.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}. Skipping migration.")
        return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add total_successes
        try:
            cursor.execute(
                "ALTER TABLE agent_reliability ADD COLUMN total_successes INTEGER DEFAULT 0"
            )
            print("Added column: total_successes")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column total_successes already exists.")
            else:
                raise

        # Add cycle_count
        try:
            cursor.execute("ALTER TABLE agent_reliability ADD COLUMN cycle_count INTEGER DEFAULT 0")
            print("Added column: cycle_count")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column cycle_count already exists.")
            else:
                raise

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
