import os
import sqlite3
import time

import pytest

from cognition.mnemosyne.temporal_store import TemporalStore


@pytest.fixture
def store():
    db_path = "data/test_temporal.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    store = TemporalStore(db_path=db_path)
    yield store
    if os.path.exists(db_path):
        os.remove(db_path)


def test_supersede_logic(store):
    session_id = "test_session"
    event_key = "test_fact"

    # 1. First record
    id1 = store.supersede(session_id, "test_event", event_key, extra={"val": 1})
    assert id1 > 0

    # 2. Second record (supersedes first)
    time.sleep(0.1)
    id2 = store.supersede(session_id, "test_event", event_key, extra={"val": 2})
    assert id2 > id1

    # Check linkage
    history = store.get_fact_history(event_key)
    assert len(history) == 2
    assert history[0]["id"] == id2
    assert history[1]["id"] == id1
    assert history[1]["superseded_by"] == id2
    assert history[1]["valid_until"] is not None
    assert history[0]["valid_until"] is None


def test_get_fact_at(store):
    session_id = "test_session"
    event_key = "time_travel_fact"

    t1 = time.time()
    store.supersede(session_id, "test", event_key, extra={"v": "old"})

    time.sleep(0.2)
    t2 = time.time()
    store.supersede(session_id, "test", event_key, extra={"v": "new"})

    # Query at t1 + 0.1
    fact_at_t1 = store.get_fact_at(event_key, t1 + 0.05)
    assert fact_at_t1 is not None
    import json

    assert json.loads(fact_at_t1["metadata"])["v"] == "old"

    # Query at t2 + 0.1
    fact_at_t2 = store.get_fact_at(event_key, t2 + 0.05)
    assert fact_at_t2 is not None
    assert json.loads(fact_at_t2["metadata"])["v"] == "new"


def test_migration_integrity(store):
    # Verify columns exist
    conn = sqlite3.connect(store._db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(temporal_metrics)")
    columns = [info[1] for info in cursor.fetchall()]
    assert "event_key" in columns
    assert "valid_from" in columns
    assert "valid_until" in columns
    assert "superseded_by" in columns
    conn.close()
