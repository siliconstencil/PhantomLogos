import os
import sqlite3

db_path = "data/reliability.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT * FROM agent_experience").fetchall()
    print(f"Records in agent_experience: {rows}")
    conn.close()
