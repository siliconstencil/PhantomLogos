import time
import sqlite3
import os
import pytest
from cognition.morpheus.sweeper import VRAMSweeper

# [SRC:axis_7]
@pytest.fixture
def sweeper_db():
    db_path = "cognition/mnemosyne/mnemosyne.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS operational_logs (id INTEGER PRIMARY KEY, timestamp REAL, name TEXT, level TEXT, message TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp REAL, session_id TEXT, event_type TEXT)")
    conn.commit()
    conn.close()
    
    yield db_path

@pytest.mark.asyncio
async def test_sqlite_pruning_retention(sweeper_db):
    sweeper = VRAMSweeper()
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    
    now = time.time()
    old_time = now - (31 * 24 * 3600) # 31 days ago
    
    cursor.execute("INSERT INTO operational_logs (timestamp) VALUES (?)", (old_time,))
    cursor.execute("INSERT INTO events (timestamp) VALUES (?)", (old_time,))
    cursor.execute("INSERT INTO operational_logs (timestamp) VALUES (?)", (now,))
    conn.commit()
    conn.close()
    
    # Run pruning
    sweeper.prune_databases()
    
    # Verify
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM operational_logs WHERE timestamp < ?", (now - (29 * 24 * 3600),))
    old_count = cursor.fetchone()[0]
    conn.close()
    
    assert old_count == 0, "Old records should be pruned"

@pytest.mark.asyncio
async def test_sqlite_row_limit(sweeper_db):
    sweeper = VRAMSweeper()
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operational_logs")
    
    now = time.time()
    data = [(now - i,) for i in range(1200)]
    cursor.executemany("INSERT INTO operational_logs (timestamp) VALUES (?)", data)
    conn.commit()
    conn.close()
    
    # Run pruning
    sweeper.prune_databases()
    
    # Verify limit
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM operational_logs")
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 1000, "Table should be capped at 1000 rows"
