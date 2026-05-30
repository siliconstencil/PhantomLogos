from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.atropos.matryoshka_service import MatryoshkaService


@pytest.mark.smoke
@pytest.mark.asyncio
@patch("src.architrave.mcp.get_slm_client")
@patch("src.atropos.matryoshka_service.get_ollama_client")
async def test_zero_vector_fallback_matryoshka(mock_ollama, mock_get_client):
    """
    K1.4 Zero-Vector Fallback Test:
    Verifies that when SLMClient.aembed() returns an empty list (zero-vector equivalent),
    MatryoshkaService successfully falls back to local Ollama.
    """
    # 1. Mock SLM client to return an empty list for aembed (async)
    mock_slm = MagicMock()
    mock_slm.health.return_value = True
    mock_slm.ahealth = AsyncMock(return_value=True)
    mock_slm.aembed = AsyncMock(return_value=[])  # Async mock returning empty list
    mock_get_client.return_value = mock_slm

    # 2. Mock local Ollama embedding client
    mock_ollama_client = AsyncMock()
    mock_ollama_client.embeddings.return_value = {"embedding": np.ones(768).tolist()}
    mock_ollama.return_value = mock_ollama_client

    # 3. Initialize MatryoshkaService
    service = MatryoshkaService()

    # 4. Request embedding
    vec = await service.embed("Test empty vector scenario")

    # 5. Assertions
    # Verify SLM aembed was attempted
    mock_slm.aembed.assert_called_once()
    # Verify local Ollama was called as fallback
    mock_ollama_client.embeddings.assert_called_once()
    # Verify sliced dimensions (256)
    assert vec.shape[0] == 256
    assert np.allclose(vec, np.ones(256) / np.linalg.norm(np.ones(256)))
