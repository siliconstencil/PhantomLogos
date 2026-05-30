import os
import sqlite3

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

possible_db_paths = [
    os.path.join(project_root, "data", "reliability.db"),
    os.path.join(project_root, "data", "mnemosyne.db"),
    os.path.join(project_root, "data", "snapshots", "reliability.db"),
    os.path.join(project_root, "data", "snapshots", "mnemosyne.db"),
    os.path.join(project_root, "reliability.db"),
    os.path.join(project_root, "mnemosyne.db"),
]

print("SUCCESS:")
found_dbs = []
for root, _dirs, files in os.walk(project_root):
    if ".venv" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith((".db", ".sqlite")):
            found_dbs.append(os.path.join(root, f))

print(f"Found databases in workspace: {found_dbs}")

for db in found_dbs + possible_db_paths:
    if os.path.exists(db):
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_reliability'"
            )
            if cursor.fetchone():
                print(f"\n=== Found agent_reliability in {db} ===")
                cursor.execute(
                    "SELECT agent_id, reliability_score, total_violations, last_violation_type, last_violation_at FROM agent_reliability"
                )
                rows = cursor.fetchall()
                for r in rows:
                    print(
                        f" Agent: {r[0]} | Score: {r[1]} | Violations: {r[2]} | Last type: {r[3]} | Last time: {r[4]}"
                    )
            conn.close()
        except Exception as e:
            print(f"Error checking {db}: {e}")
