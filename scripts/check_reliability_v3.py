import sqlite3

db_path = "D:/Hank/data/reliability.db"
conn = sqlite3.connect(db_path)
res = conn.execute(
    "SELECT reliability_score FROM agent_reliability WHERE agent_id = 'sophia'"
).fetchone()
conn.close()
if res:
    print(f"Reliability Score (Sophia): {res[0]:.2f}")
else:
    print("Sophia reliability record not found.")
