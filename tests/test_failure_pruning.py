import pytest

from cognition.mnemosyne.reflection_store import ReflectionStore
from cognition.morpheus.sweeper import VRAMSweeper


# [SRC:axis_8]
@pytest.mark.asyncio
async def test_pruning():
    """Verify that the VRAMSweeper correctly prunes old failure memory entries."""
    store = ReflectionStore()

    # Insert a failure with old timestamp to simulate aged entry
    with store._get_conn() as conn:
        c = conn.cursor()
        old_ts = "2025-01-01 00:00:00"
        recent_ts = "2026-12-31 00:00:00"

        c.execute(
            "INSERT INTO failure_memory (error_type, root_cause, prevention_rule, severity, recurrence_count, status, context_hash, updated_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "test_old",
                "old error",
                "Old prevention rule",
                1,
                5,
                "active",
                "deadbeef00000001",
                old_ts,
                old_ts,
            ),
        )
        c.execute(
            "INSERT INTO failure_memory (error_type, root_cause, prevention_rule, severity, recurrence_count, status, context_hash, updated_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "test_recent",
                "recent error",
                "Recent prevention rule",
                3,
                2,
                "active",
                "deadbeef00000002",
                recent_ts,
                recent_ts,
            ),
        )
        conn.commit()

    # Run sweeper
    sweeper = VRAMSweeper()
    sweeper.prune_databases()

    after = store.get_prevention_rules(limit=10)

    # Clean up test records
    with store._get_conn() as conn:
        conn.execute("DELETE FROM failure_memory WHERE error_type LIKE 'test_%'")
        conn.commit()

    # Verify: old should be gone, recent should stay
    has_old = any(r["error_type"] == "test_old" for r in after)
    has_recent = any(r["error_type"] == "test_recent" for r in after)

    assert not has_old, "Old failure should be pruned"
    assert has_recent, "Recent failure should survive"
