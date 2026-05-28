"""
Phantom Logos system cross-check tool.
Directly queries SQLite and LanceDB tables to verify data persistence.
"""

import sqlite3
import sys
from pathlib import Path

import lancedb

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))


def _sqlite_check(db_path: Path) -> None:
    """Queries SQLite database for table row counts and session breakdowns."""
    print(f"\n[1] Checking SQLite Database at: {db_path}")
    if not db_path.exists():
        print("[FAIL] Database file does not exist!")
        return

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        print(f"Detected Tables ({len(table_names)}): {', '.join(table_names)}")

        print("\nTable Statistics (Row Counts):")
        for table in sorted(table_names):
            # Table name comes directly from sqlite_master (read-only system catalog).
            # Additional alphanumeric filter applied as defence-in-depth.
            safe_table = "".join(c for c in table if c.isalnum() or c == "_")
            cnt = cursor.execute(
                f"SELECT COUNT(*) FROM {safe_table}"  # noqa: S608
            ).fetchone()[0]
            print(f"  - {safe_table:25}: {cnt} rows")

            try:
                sessions = cursor.execute(
                    f"SELECT session_id, COUNT(*) FROM {safe_table}"  # noqa: S608
                    " GROUP BY session_id"
                ).fetchall()
                if sessions:
                    sess_str = ", ".join(f"'{s[0]}': {s[1]}" for s in sessions)
                    print(f"    (Sessions -> {sess_str})")
            except sqlite3.OperationalError:
                # Table has no session_id column - expected for some system tables.
                pass

        print("[SUCCESS] SQLite structure and persistence verified.")
    except sqlite3.DatabaseError as e:
        print(f"[FAIL] SQLite verification failed: {e}")
    finally:
        if conn:
            conn.close()


def _lancedb_check(db_dir: Path) -> None:
    """Queries LanceDB tables for row counts and sample entries."""
    print("\n[2] Checking LanceDB Semantic Memory Table...")
    if not db_dir.exists():
        print("[WARN] LanceDB directory (data/lancedb) does not exist yet.")
        return

    try:
        db = lancedb.connect(str(db_dir))
        tables = db.table_names()
        print(f"LanceDB Tables ({len(tables)}): {tables}")
        for table_name in tables:
            tbl = db.open_table(table_name)
            df = tbl.to_pandas()
            print(f"  - {table_name:25}: {len(df)} rows")
            if len(df) > 0:
                print(f"\nLatest {table_name} Entries:")
                for _, row in df.tail(3).iterrows():
                    raw_text = row.get("text", row.get("prevention_rule", row.get("content", "")))
                    text = str(raw_text or "")
                    axis = row.get("axis", "unknown")
                    timestamp = row.get("timestamp", "unknown")
                    print(f"    * [Axis {axis}] [{timestamp}] {text[:150]}...")
        print("[SUCCESS] LanceDB semantic persistence verified.")
    except (OSError, RuntimeError, ValueError) as e:
        print(f"[FAIL] LanceDB verification failed: {e}")


def run_cross_check() -> None:
    """Queries SQLite and LanceDB databases to print row counts and latest records."""
    print("==================================================")
    print("      PHANTOM LOGOS SYSTEM CROSS-CHECK REPORT     ")
    print("==================================================")

    _sqlite_check(root / "data" / "mnemosyne.db")
    _lancedb_check(root / "data" / "lancedb")

    print("\n==================================================")


if __name__ == "__main__":
    run_cross_check()
