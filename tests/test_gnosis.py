"""Unit tests for Gnosis context assembly logic and AgentRegistry."""

import hashlib
import sqlite3
from unittest.mock import AsyncMock, patch

import pytest

from cognition.sophia.gnosis.base import _context_cache_local, get_dynamic_context
from src.architrave.context_cache import ContextCacheStore


def clear_caches(agent_id: str, task_hint: str, session_id: str) -> None:
    """Clear local and disk context caches for a given agent and session."""
    cache_key = f"{agent_id}:{task_hint[:40]}:{session_id}"
    if cache_key in _context_cache_local:
        del _context_cache_local[cache_key]

    hashed_key = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    disk_cache = ContextCacheStore(start_sweep=False)
    with disk_cache._lock:  # pylint: disable=protected-access
        conn = sqlite3.connect(disk_cache.db_path)
        conn.execute("DELETE FROM context_cache WHERE key = ?", (hashed_key,))
        conn.commit()
        conn.close()


@pytest.mark.anyio
async def test_assemble_context_basic() -> None:
    """Test basic context assembly with episodic data."""
    clear_caches("sophia", "Verify SLM memory retrieval", "test_gnosis_sess")

    from cognition.mnemosyne.episodic_store import EpisodicStore

    store = EpisodicStore()
    store.log(session_id="test_gnosis_sess", action="test_action", outcome="success")

    stable, dynamic, block_signal = await get_dynamic_context(
        agent_id="sophia", task_hint="Verify SLM memory retrieval", session_id="test_gnosis_sess"
    )

    assert isinstance(stable, str)
    assert isinstance(dynamic, str)
    assert isinstance(block_signal, dict)

    assert "AXIS 1" in dynamic
    assert "AXIS 8" in dynamic
    assert "test_action -> success" in dynamic


@pytest.mark.anyio
async def test_assemble_context_slm_recall() -> None:
    """Test context assembly using mocked SLM search results."""
    clear_caches("sophia", "Verify SLM recall", "test_gnosis_sess")

    mock_results = [
        {"axis_id": 1, "text": "SLM Recalled Episode 1", "session_id": "test_gnosis_sess"},
        {"axis_id": 8, "text": "SLM Recalled Reflection 1", "session_id": "test_gnosis_sess"},
    ]

    with (
        patch("src.architrave.mcp.slm_client.SLMClient.health", return_value=True),
        patch(
            "src.architrave.mcp.slm_client.SLMClient.asearch", new_callable=AsyncMock
        ) as mock_asearch,
    ):
        mock_asearch.return_value = mock_results

        _, dynamic, _ = await get_dynamic_context(
            agent_id="sophia", task_hint="Verify SLM recall", session_id="test_gnosis_sess"
        )

        assert "SLM Recalled Episode 1" in dynamic
        assert "SLM Recalled Reflection 1" in dynamic
        assert mock_asearch.call_count >= 2


@pytest.mark.anyio
async def test_gnosis_context_cache_store() -> None:
    """Test Gnosis caching mechanism (both memory and disk-cache)."""
    import json

    _context_cache_local.clear()

    agent_id = "test_cache_agent"
    task_hint = "Disk caching test task hint"
    session_id = "test_cache_sess"

    cache_key = f"{agent_id}:{task_hint[:40]}:{session_id}"
    hashed_key = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

    disk_cache = ContextCacheStore(start_sweep=False)
    with disk_cache._lock:  # pylint: disable=protected-access
        conn = sqlite3.connect(disk_cache.db_path)
        conn.execute("DELETE FROM context_cache WHERE key = ?", (hashed_key,))
        conn.commit()
        conn.close()

    stable1, dynamic1, block1 = await get_dynamic_context(
        agent_id=agent_id, task_hint=task_hint, session_id=session_id
    )

    cached_val = disk_cache.get_by_key(hashed_key)
    assert cached_val is not None
    cached_data = json.loads(cached_val)
    assert cached_data["stable_context"] == stable1
    assert cached_data["dynamic_context"] == dynamic1
    assert cached_data["block_signal"] == block1

    if cache_key in _context_cache_local:
        del _context_cache_local[cache_key]

    stable2, dynamic2, block2 = await get_dynamic_context(
        agent_id=agent_id, task_hint=task_hint, session_id=session_id
    )

    assert stable2 == stable1
    assert dynamic2 == dynamic1
    assert block2 == block1


def test_sophia_yaml_prune_tool() -> None:
    """Test that 'prune' is in sophia's loaded tools config."""
    from src.clotho.agent_loader import AgentRegistry

    AgentRegistry._instance = None  # pylint: disable=protected-access
    registry = AgentRegistry.get_instance()
    sophia = registry.get("sophia")
    assert sophia is not None
    assert "prune" in sophia.tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
