import uuid

import pytest

from cognition.mnemosyne.episodic_store import EpisodicStore
from cognition.mnemosyne.session_log import SessionLog


# [SRC:axis_4]
@pytest.mark.asyncio
async def test_session_log_append_and_get():
    log = SessionLog("test_recovery_session")
    assert log.append("task.start", {"objective": "Recovery test"}) >= 0
    assert log.append("tool.call", {"tool": "ls", "args": ["/"]}) >= 0

    history = log.get_history(limit=10)
    assert len(history) >= 2
    assert history[0]["type"] == "task.start"
    assert history[1]["type"] == "tool.call"


@pytest.mark.asyncio
async def test_session_log_wake_new():
    log = SessionLog("test_recovery_new")
    result = log.wake()
    assert result["status"] == "new"
    assert result["last_seq"] == -1


@pytest.mark.asyncio
async def test_session_log_wake_recovered():
    log = SessionLog("test_recovery_wake")
    log.append("task.start", {"objective": "Wake test"})
    log.append("tool.call", {"tool": "ls"})
    result = log.wake()
    assert result["status"] == "recovered"
    assert result["last_seq"] >= 0
    assert result["event_count"] >= 2


@pytest.mark.asyncio
async def test_session_log_compact():
    sid = f"test_compact_{uuid.uuid4().hex[:8]}"
    log = SessionLog(sid)
    for i in range(20):
        log.append("tool.call", {"tool": f"tool_{i % 5}", "step": i})
    result = log.compact(max_tokens=8000)
    assert "summary" in result
    assert result["event_count"] >= 20
    assert result["truncated"] is True
    assert "Tools used" in result["summary"]


@pytest.mark.asyncio
async def test_event_model_persists():
    store = EpisodicStore()
    seq = store.log_event("test_persist", "unit.test", '{"key":"value"}', "test_agent")
    assert seq >= 0
    events = store.get_events("test_persist")
    assert len(events) >= 1
    assert events[-1].event_type == "unit.test"
    assert events[-1].agent_id == "test_agent"
