import sqlite3
import os

def check():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")
    
    print(f"--- Schema Integrity Check (Phase 1) ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check v2 table and columns
    print("Checking operational_logs_v2...")
    cursor.execute("PRAGMA table_info(operational_logs_v2)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    required = ["id", "timestamp", "session_id", "agent_id", "tool_name", "name", "level", "message"]
    missing = [c for c in required if c not in columns]
    
    if not missing:
        print("  [PASS] All required columns exist.")
        if columns["session_id"] == "TEXT":
            print("  [PASS] session_id is TEXT type.")
    else:
        print(f"  [FAIL] Missing columns: {missing}")

    # 2. Check v1 table removal
    print("Checking legacy table removal...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operational_logs'")
    if not cursor.fetchone():
        print("  [PASS] operational_logs (v1) successfully dropped.")
    else:
        print("  [FAIL] operational_logs (v1) still exists!")

    # 3. Check data presence
    cursor.execute("SELECT COUNT(*) FROM operational_logs_v2")
    count = cursor.fetchone()[0]
    print(f"  [INFO] Total rows in operational_logs_v2: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM operational_logs_v2 WHERE session_id='legacy_v1'")
    legacy_count = cursor.fetchone()[0]
    print(f"  [INFO] Migrated legacy rows: {legacy_count}")

    conn.close()
    print("--- Check Complete ---")

if __name__ == "__main__":
    check()
