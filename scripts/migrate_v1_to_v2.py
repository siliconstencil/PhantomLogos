import os
import sqlite3


def migrate():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check if v1 table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operational_logs'")
    if not cursor.fetchone():
        print("Table 'operational_logs' (v1) does not exist. Skipping migration.")
        conn.close()
        return

    # 2. Ensure v2 table has session_id (Task 1.1 should have handled this, but safety first)
    try:
        cursor.execute("SELECT session_id FROM operational_logs_v2 LIMIT 1")
    except sqlite3.OperationalError:
        print("Table 'operational_logs_v2' does not have 'session_id' column. Adding it...")
        cursor.execute(
            "ALTER TABLE operational_logs_v2 ADD COLUMN session_id TEXT DEFAULT 'default'"
        )

    # 3. Migrate data
    print("Migrating data from v1 to v2...")
    try:
        # v1: id, timestamp, name, level, message
        # v2: id, timestamp, session_id, agent_id, tool_name, name, level, message
        cursor.execute("""
            INSERT INTO operational_logs_v2 (timestamp, session_id, agent_id, tool_name, name, level, message)
            SELECT timestamp, 'legacy_v1', 'system', NULL, name, level, message
            FROM operational_logs
        """)
        row_count = cursor.rowcount
        print(f"Successfully migrated {row_count} rows.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        conn.close()
        return

    # 4. Drop v1 table
    print("Dropping legacy table 'operational_logs'...")
    try:
        cursor.execute("DROP TABLE operational_logs")
        print("Legacy table dropped.")
    except Exception as e:
        print(f"Failed to drop legacy table: {e}")
        conn.rollback()
        conn.close()
        return

    # 5. Commit and Vacuum
    conn.commit()
    print("Compacting database (VACUUM)...")
    conn.execute("VACUUM")
    print("Database optimized.")

    conn.close()
    print("Migration Phase 11.15 completed successfully.")


if __name__ == "__main__":
    migrate()
