import sqlite3
import time
from datetime import UTC, datetime

from cognition.mnemosyne.memory_arbitrator import MemoryArbitrator
from cognition.mnemosyne.reflection_store import ReflectionStore
from cognition.morpheus.sweeper import VRAMSweeper


def test_memory_arbitrator_ebbinghaus():
    # Test base initialization
    arb = MemoryArbitrator(base_decay_hours=24.0, sensitivity=1.0)

    # importance=0.0 -> decay should be 24h * 3600
    decay_0 = arb._get_adaptive_decay(importance=0.0)
    assert decay_0 == 24.0 * 3600

    # importance=1.0 -> decay should be 48h * 3600 (base * 2.0)
    decay_1 = arb._get_adaptive_decay(importance=1.0)
    assert decay_1 == 48.0 * 3600

    # Test scoring recency decay
    now = time.time()
    # 24h ago
    time_24h_ago = now - (24.0 * 3600)

    # For importance=0.0: age = 24h, decay = 24h -> exp(-1) = 0.3678
    # importance * exp(-1) = 0.0
    score_0 = arb.score(importance=0.0, timestamp=time_24h_ago)
    assert score_0 == 0.0

    # For importance=1.0: age = 24h, decay = 48h -> exp(-0.5) = 0.6065
    # score = 1.0 * 1.0 (freq) * 0.6065 * 1.0 (rel) = 0.6065
    score_1 = arb.score(importance=1.0, timestamp=time_24h_ago)
    assert score_1 == 0.6065


def test_reflection_store_importance():
    from src.utils.project_path import to_absolute_path

    db_path = to_absolute_path("data/mnemosyne.db")

    store = ReflectionStore(db_path=db_path)

    # Store reflection with custom importance
    session_id = "test_ebbinghaus_session"
    insight = "This is a very unique test insight for testing importance insertion."

    # Clear old reflections of this session if any
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM reflections WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

    success = store.store_reflection(session_id, insight, category="test", importance=0.8)
    assert success is True

    # Retrieve and check importance
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT importance FROM reflections WHERE session_id = ? AND insight = ?",
            (session_id, insight),
        )
        row = cursor.fetchone()
        assert row is not None
        assert abs(row[0] - 0.8) < 1e-5
    finally:
        conn.close()


def test_sweeper_ebbinghaus_prune():
    from src.utils.project_path import to_absolute_path

    db_path = to_absolute_path("data/mnemosyne.db")

    # Initialize store and insert test rows
    store = ReflectionStore(db_path=db_path)
    session_id = "test_ebbinghaus_prune"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM reflections WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM episodes WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

    # 1. Reflections
    # Kept: New reflection
    store.store_reflection(
        session_id,
        "Very new reflection that should be preserved in Mnemosyne.",
        category="test",
        importance=0.8,
    )

    # Pruned: Very old reflection with low importance
    old_time = datetime.fromtimestamp(time.time() - (100 * 3600), UTC).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO reflections (insight, category, session_id, created_at, importance) VALUES (?, ?, ?, ?, ?)",
            (
                "Very old reflection that is expired based on Ebbinghaus forgetting curve.",
                "test",
                session_id,
                old_time,
                0.1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # 2. Episodes
    # Kept: recent success episode (current time)
    # Pruned: old pending episodes (100h and 150h ago, beyond 3-day retention)
    now_time = datetime.fromtimestamp(time.time(), UTC).isoformat()
    older_time = datetime.fromtimestamp(time.time() - (150 * 3600), UTC).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO episodes (session_id, action, outcome, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "test_action_success", "success", now_time),
        )
        conn.execute(
            "INSERT INTO episodes (session_id, action, outcome, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "test_action_pending", "pending", old_time),
        )
        conn.execute(
            "INSERT INTO episodes (session_id, action, outcome, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "test_action_pending_older", "pending", older_time),
        )
        conn.commit()
    finally:
        conn.close()

    # Execute time-based SQLite prune via VRAMSweeper (_prune_ebbinghaus was removed in v1.1.25)
    sweeper = VRAMSweeper()
    gov = {"retention_days": 3, "row_limit": 10000, "exclude_tables": []}
    stats = {"pruned_sqlite": 0}

    sweeper._prune_sqlite(gov, stats)

    # Assertions
    conn = sqlite3.connect(db_path)
    try:
        # Check reflections
        reflections = conn.execute(
            "SELECT insight FROM reflections WHERE session_id = ?", (session_id,)
        ).fetchall()
        insights = [r[0] for r in reflections]
        assert "Very new reflection that should be preserved in Mnemosyne." in insights
        assert (
            "Very old reflection that is expired based on Ebbinghaus forgetting curve."
            not in insights
        )

        # Check episodes
        episodes = conn.execute(
            "SELECT action FROM episodes WHERE session_id = ?", (session_id,)
        ).fetchall()
        actions = [e[0] for e in episodes]
        assert "test_action_success" in actions
        assert "test_action_pending_older" not in actions
    finally:
        conn.close()
