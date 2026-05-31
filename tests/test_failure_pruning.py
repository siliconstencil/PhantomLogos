import pytest
from sqlalchemy import text

from cognition.mnemosyne.reflection_store import ReflectionStore
from cognition.morpheus.sweeper import VRAMSweeper


# [SRC:axis_8]
@pytest.mark.asyncio
async def test_pruning():
    """Verify that the VRAMSweeper correctly prunes old failure memory entries."""
    store = ReflectionStore()

    # Insert a failure with old timestamp to simulate aged entry
    old_ts = "2025-01-01 00:00:00"
    recent_ts = "2026-12-31 00:00:00"
    _session = store.Session()
    try:
        _session.execute(
            text(
                "INSERT INTO failure_memory (error_type, root_cause, prevention_rule, severity, recurrence_count, status, context_hash, updated_at, created_at)"
                " VALUES (:et, :rc, :pr, :sev, :rcc, :st, :ch, :ua, :ca)"
            ),
            {
                "et": "test_old",
                "rc": "old error",
                "pr": "Old prevention rule",
                "sev": 1,
                "rcc": 5,
                "st": "active",
                "ch": "deadbeef00000001",
                "ua": old_ts,
                "ca": old_ts,
            },
        )
        _session.execute(
            text(
                "INSERT INTO failure_memory (error_type, root_cause, prevention_rule, severity, recurrence_count, status, context_hash, updated_at, created_at)"
                " VALUES (:et, :rc, :pr, :sev, :rcc, :st, :ch, :ua, :ca)"
            ),
            {
                "et": "test_recent",
                "rc": "recent error",
                "pr": "Recent prevention rule",
                "sev": 3,
                "rcc": 2,
                "st": "active",
                "ch": "deadbeef00000002",
                "ua": recent_ts,
                "ca": recent_ts,
            },
        )
        _session.commit()
    finally:
        _session.close()

    # Run sweeper
    sweeper = VRAMSweeper()
    sweeper.prune_databases()

    after = store.get_prevention_rules(limit=10)

    # Clean up test records
    _session = store.Session()
    try:
        _session.execute(text("DELETE FROM failure_memory WHERE error_type LIKE 'test_%'"))
        _session.commit()
    finally:
        _session.close()

    # Verify: old should be gone, recent should stay
    has_old = any(r["error_type"] == "test_old" for r in after)
    has_recent = any(r["error_type"] == "test_recent" for r in after)

    assert not has_old, "Old failure should be pruned"
    assert has_recent, "Recent failure should survive"
