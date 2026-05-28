from unittest.mock import patch

import pytest

from src.clotho.orchestrator import create_clotho_graph, wait_for_l0


def test_l0_gate_missing_task():
    state = {"l0_approved": True}
    res = wait_for_l0(state)
    assert res["l0_approved"] is False
    print("\n[SUCCESS] L0 Gate rejected state with missing task.")


def test_l0_gate_not_approved():
    state = {"task": "test", "l0_approved": False}
    res = wait_for_l0(state)
    assert res["l0_approved"] is False
    print("[SUCCESS] L0 Gate rejected unapproved state.")


def test_l0_gate_passed():
    state = {"task": "test", "l0_approved": True}
    res = wait_for_l0(state)
    assert res["l0_approved"] is True
    print("[SUCCESS] L0 Gate passed valid approved state.")


@pytest.mark.asyncio
async def test_sqlite_saver_hard_stop():
    # Mock sqlite3.connect to fail
    with patch("sqlite3.connect", side_effect=Exception("DB Corrupted")):
        with pytest.raises(RuntimeError) as excinfo:
            create_clotho_graph()
        assert "Axis 13 persistence failure" in str(excinfo.value)
    print("[SUCCESS] SqliteSaver hard-stop verified on failure.")


if __name__ == "__main__":
    test_l0_gate_missing_task()
    test_l0_gate_not_approved()
    test_l0_gate_passed()
    import asyncio

    asyncio.run(test_sqlite_saver_hard_stop())
