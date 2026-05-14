import os
import sqlite3

from src.utils.project_path import get_project_root


def migrate():
    db_path = os.path.join(get_project_root(), "data/mnemosyne.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}. Skipping migration.")
        return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add session_id
        try:
            cursor.execute("ALTER TABLE goals ADD COLUMN session_id VARCHAR(64) DEFAULT ''")
            print("Added column: session_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column session_id already exists.")
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
