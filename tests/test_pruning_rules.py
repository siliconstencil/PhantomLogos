import os
import sqlite3
import time
from unittest.mock import patch

import pytest

from cognition.morpheus.sweeper import VRAMSweeper


# [SRC:axis_7]
@pytest.fixture
def sweeper_db():
    db_path = "data/test_mnemosyne.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS operational_logs_v2 (id INTEGER PRIMARY KEY, timestamp TEXT, session_id TEXT, agent_id TEXT, tool_name TEXT, name TEXT, level TEXT, message TEXT)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, created_at TEXT, session_id TEXT, event_type TEXT)"
    )
    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_sqlite_pruning_retention(sweeper_db):
    sweeper = VRAMSweeper()

    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()

    now = time.time()
    old_time = now - (31 * 24 * 3600)  # 31 days ago

    # Format ISO-like strings since it is text_iso type
    old_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(old_time))
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now))

    cursor.execute("INSERT INTO operational_logs_v2 (timestamp) VALUES (?)", (old_time_str,))
    cursor.execute("INSERT INTO events (created_at) VALUES (?)", (old_time_str,))
    cursor.execute("INSERT INTO operational_logs_v2 (timestamp) VALUES (?)", (now_str,))
    conn.commit()
    conn.close()

    # Capture original functions to prevent recursion in mock side effects
    orig_exists = os.path.exists
    orig_connect = sqlite3.connect

    # Patch os.path.exists and sqlite3.connect
    # so when VRAMSweeper._prune_sqlite tries to open data/mnemosyne.db, it actually opens sweeper_db
    with patch(
        "os.path.exists", side_effect=lambda p: True if "mnemosyne.db" in p else orig_exists(p)
    ):
        with patch(
            "sqlite3.connect",
            side_effect=lambda p: (
                orig_connect(sweeper_db) if "mnemosyne.db" in p else orig_connect(p)
            ),
        ):
            sweeper.prune_databases()

    # Verify
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cutoff_time = now - (29 * 24 * 3600)
    cutoff_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(cutoff_time))

    cursor.execute("SELECT COUNT(*) FROM operational_logs_v2 WHERE timestamp < ?", (cutoff_str,))
    old_count = cursor.fetchone()[0]
    conn.close()

    assert old_count == 0, "Old records should be pruned"


@pytest.mark.asyncio
async def test_sqlite_row_limit(sweeper_db):
    sweeper = VRAMSweeper()
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operational_logs_v2")

    now = time.time()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now))
    data = [(now_str,) for _ in range(5200)]  # 5200 rows to exceed 5000 limit
    cursor.executemany("INSERT INTO operational_logs_v2 (timestamp) VALUES (?)", data)
    conn.commit()
    conn.close()

    # Capture original functions to prevent recursion in mock side effects
    orig_exists = os.path.exists
    orig_connect = sqlite3.connect

    # Run pruning with patched DB path and governance config
    with patch(
        "os.path.exists", side_effect=lambda p: True if "mnemosyne.db" in p else orig_exists(p)
    ):
        with patch(
            "sqlite3.connect",
            side_effect=lambda p: (
                orig_connect(sweeper_db) if "mnemosyne.db" in p else orig_connect(p)
            ),
        ):
            with patch.object(
                sweeper,
                "_load_governance_config",
                return_value={"retention_days": 30, "row_limit": 5000, "exclude_tables": []},
            ):
                sweeper.prune_databases()

    # Verify limit
    conn = sqlite3.connect(sweeper_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM operational_logs_v2")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 5000, "Table should be capped at 5000 rows"
