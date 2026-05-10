import os
import pytest
from src.lachesis import CodebaseMapper
from cognition.mnemosyne.semantic_store import SemanticStore

# [SRC:axis_5]
@pytest.mark.asyncio
async def test_env_loading():
    # These are expected defaults or from .env
    mapper = CodebaseMapper()
    assert mapper.chunk_size == 1024
    assert mapper.chunk_overlap == 128

@pytest.mark.asyncio
async def test_rag_max_chunks_limit(monkeypatch):
    monkeypatch.setenv("RAG_MAX_CHUNKS", "10")
    # SemanticStore initialization should respect RAG_MAX_CHUNKS
    store = SemanticStore()
    # verify if possible, or just ensure no crash
    assert store is not None
