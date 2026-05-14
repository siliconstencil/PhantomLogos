import os
import sqlite3

db_path = "data/reliability.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Tables in {db_path}: {tables}")
    conn.close()
else:
    print(f"{db_path} not found")
