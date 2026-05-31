import pytest

from src.clotho.ergon.kathedra import anchor_inject_node


@pytest.mark.anyio
async def test_anchor_inject_node_basic():
    state = {
        "task": "Test mapping for SLM_ENABLED and TokenBudgetGuard context",
        "session_id": "test_session",
        "active_agent": {"id": "sophia"},
    }

    res = await anchor_inject_node(state)
    assert isinstance(res, dict)
    assert "anchors" in res
    assert "memory_sync" in res

    # Verify that the cache actually got populated
    from src.architrave.context_cache import ContextCacheStore

    cache = ContextCacheStore()
    cached_val = cache.get(res["anchors"])
    assert cached_val is not None
    # Verify cache contains stable content
    assert isinstance(cached_val, str) and len(cached_val) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
