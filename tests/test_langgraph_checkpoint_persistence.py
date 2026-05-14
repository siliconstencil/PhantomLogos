import os
import sqlite3

import pytest

from src.clotho.orchestrator import create_clotho_graph


# [SRC:axis_13]
@pytest.mark.asyncio
async def test_langgraph_persistence():
    """Verify that Clotho graph persists state to SQLite checkpointer."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "langgraph_checkpoints.sqlite")

    # 1. Clear existing DB for clean test
    if os.path.exists(db_path):
        os.remove(db_path)

    app = create_clotho_graph()

    config = {"configurable": {"thread_id": "test_thread_persist"}}
    initial_state = {
        "task": "Persistence Test",
        "iteration": 0,
        "max_iterations": 2,
        "session_id": "persist_session",
        "l0_approved": True,
    }

    # Run graph. It should stop at wait_for_l0 (interrupt_before)
    await app.ainvoke(initial_state, config=config)

    # 2. Check if DB file exists and has tables
    assert os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()

    # Checkpoints table is often named 'checkpoints' or 'checkpoint' depending on version
    assert any("checkpoint" in t for t in tables)

    # 3. Verify state can be recovered
    state = await app.aget_state(config)
    assert state.values["task"] == "Persistence Test"
    assert state.values["session_id"] == "persist_session"
