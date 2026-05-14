import sqlite3

db_path = "D:/Hank/data/mnemosyne.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"Checking Database: {db_path}")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables found: {tables}")

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"Table '{table}': {count} rows")

conn.close()
