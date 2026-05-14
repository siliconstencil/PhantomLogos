import sqlite3

db_path = "D:/Hank/data/mnemosyne.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Schema for meta_cognition:")
cursor.execute("PRAGMA table_info(meta_cognition)")
for col in cursor.fetchall():
    print(col)

print("\nTrying to find reliability score...")
# Try common column names if meta_value failed
cols = ["value", "meta_value", "content", "data"]
for col in cols:
    try:
        query = f"SELECT {col} FROM meta_cognition WHERE meta_key = 'reliability_score_sophia'"
        res = conn.execute(query).fetchone()
        if res:
            print(f"Reliability Score (Sophia) found in column '{col}': {res[0]}")
            break
    except Exception:
        continue

conn.close()
