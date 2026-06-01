from unittest.mock import AsyncMock, patch

import pytest

from src.muscle.reranker import JinaReranker


def test_reranker_path_hardening():
    # Verify reranker model name matches standard
    r = JinaReranker()
    assert r.rerank_model == "jina-reranker-v3:latest"


@pytest.mark.asyncio
async def test_reranker_fallback_normalization_async():
    r = JinaReranker()

    # Mock self.client.embeddings
    # We have 1 query + 3 documents = 4 items to embed
    mock_embeddings = [
        {"embedding": [1.0, 0.0]},  # query (python programming)
        {"embedding": [0.9, 0.1]},  # doc 1 (Python is great)
        {"embedding": [0.1, 0.9]},  # doc 2 (Java is old)
        {"embedding": [0.0, 1.0]},  # doc 3 (The sky is blue)
    ]

    mock_embeddings_fn = AsyncMock()
    mock_embeddings_fn.side_effect = mock_embeddings

    with patch.object(r.client, "embeddings", mock_embeddings_fn):
        query = "python programming"
        docs = ["Python is great", "Java is old", "The sky is blue"]
        results = await r.rerank_async(query, docs)

        assert "results" in results
        assert len(results["results"]) == 3
        assert results["results"][0]["text"] == "Python is great"
        assert results["results"][1]["text"] == "Java is old"
        assert results["results"][2]["text"] == "The sky is blue"


def test_reranker_fallback_normalization_sync():
    r = JinaReranker()

    mock_embeddings = [
        {"embedding": [1.0, 0.0]},
        {"embedding": [0.9, 0.1]},
        {"embedding": [0.1, 0.9]},
        {"embedding": [0.0, 1.0]},
    ]

    mock_embeddings_fn = AsyncMock()
    mock_embeddings_fn.side_effect = mock_embeddings

    with patch.object(r.client, "embeddings", mock_embeddings_fn):
        query = "python programming"
        docs = ["Python is great", "Java is old", "The sky is blue"]
        results = r.rerank(query, docs)

        assert "results" in results
        assert len(results["results"]) == 3
        assert results["results"][0]["text"] == "Python is great"


def test_registry_alignment():
    from src.architrave.model_registry import ROLE_TO_MODEL

    assert ROLE_TO_MODEL["reranker"]["primary"] == "jina-reranker-v3:latest"
