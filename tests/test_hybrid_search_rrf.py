import numpy as np
import pytest

from cognition.mnemosyne.semantic_store import SemanticStore


# [SRC:axis_6]
@pytest.fixture
def hybrid_store():
    store = SemanticStore()
    session_id = "test_hybrid_session"

    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Artificial intelligence is transforming the world",
        "Python is a versatile programming language",
        "Machine learning is a subset of AI",
        "The weather today is sunny and warm",
    ]
    vectors = [np.random.rand(256) for _ in texts]
    metadata = [{"axis": "test"} for _ in texts]

    store.add_memories(texts, vectors, metadata, session_id=session_id)
    return store, session_id


@pytest.mark.asyncio
async def test_fts_search(hybrid_store):
    store, session_id = hybrid_store
    res = store.search(np.random.rand(256), session_id, mode="fts", query_text="python")
    assert len(res) >= 1
    assert "Python" in res[0]["text"]


@pytest.mark.asyncio
async def test_rrf_merge_logic(hybrid_store):
    store, _ = hybrid_store
    res_vec = [{"text": "A"}, {"text": "B"}, {"text": "C"}]
    res_fts = [{"text": "C"}, {"text": "A"}, {"text": "D"}]

    merged = store._rrf_merge(res_vec, res_fts, limit=4)
    assert merged[0]["text"] == "A"
    assert merged[1]["text"] == "C"
    assert len(merged) == 4


@pytest.mark.asyncio
async def test_hybrid_search_execution(hybrid_store):
    store, session_id = hybrid_store
    query_vec = np.random.rand(256)
    query_text = "Artificial"

    res = store.search(query_vec, session_id, limit=2, mode="hybrid", query_text=query_text)
    assert len(res) > 0
    assert "Artificial" in res[0]["text"]
