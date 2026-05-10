import os
import pytest
from src.muscle.reranker import JinaReranker

def test_reranker_path_hardening():
    # Verify paths are dynamic
    r = JinaReranker()
    assert os.getenv("ANTIGRAVITY_ROOT") in r.model_path or os.getenv("LLM_MODEL_DIR") in r.model_path
    assert "jina-reranker-v3-Q8_0.gguf" in r.model_path

def test_reranker_fallback_normalization():
    r = JinaReranker()
    # Mocking fallback trigger by setting model_path to non-existent
    r._available = False
    query = "python programming"
    docs = ["Python is great", "Java is old", "The sky is blue"]
    results = r.rerank(query, docs)
    
    for res in results:
        assert 0 <= res["score"] <= 1
        assert res["text"] in docs

def test_registry_alignment():
    from src.architrave.model_registry import ROLE_TO_MODEL
    assert ROLE_TO_MODEL["reranker"]["primary"] == "jina-reranker-v3-q8_0:latest"
