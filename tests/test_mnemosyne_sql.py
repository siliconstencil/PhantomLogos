import sqlite3
import os
import pytest

# [SRC:axis_10]
@pytest.mark.asyncio
async def test_mnemosyne_sql_connectivity():
    """Verify basic SQLite connectivity for the Mnemosyne memory store."""
    db_path = os.path.join("data", "mnemosyne.db")
    os.makedirs("data", exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS test_infra (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test_infra (name) VALUES (?)", ("Firmitas Test",))
        conn.commit()
        cursor.execute("SELECT * FROM test_infra WHERE name=?", ("Firmitas Test",))
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == "Firmitas Test"
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
