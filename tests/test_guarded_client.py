from unittest.mock import AsyncMock, patch

import pytest

from src.utils.ollama_utils import (
    GuardedAsyncClient,
    get_ollama_client,
    register_vram_guard_callback,
)


def test_get_ollama_client_returns_guarded_client():
    client = get_ollama_client()
    assert isinstance(client, GuardedAsyncClient)


@pytest.mark.asyncio
async def test_guarded_client_chat_triggers_callback_success():
    client = get_ollama_client()
    mock_callback = AsyncMock(return_value=True)
    register_vram_guard_callback(mock_callback)

    with patch("ollama.AsyncClient.chat", new_callable=AsyncMock) as mock_super_chat:
        mock_super_chat.return_value = {"message": {"content": "ok"}}

        resp = await client.chat(
            model="phi-4-mini-ud:latest", messages=[{"role": "user", "content": "hello"}]
        )

        mock_callback.assert_called_once_with("phi-4-mini-ud:latest")
        mock_super_chat.assert_called_once()
        assert resp["message"]["content"] == "ok"


@pytest.mark.asyncio
async def test_guarded_client_chat_raises_error_on_guard_failure():
    client = get_ollama_client()
    mock_callback = AsyncMock(return_value=False)  # VRAMBudgetGuard rejects loading
    register_vram_guard_callback(mock_callback)

    with patch("ollama.AsyncClient.chat", new_callable=AsyncMock) as mock_super_chat:
        with pytest.raises(RuntimeError) as exc_info:
            await client.chat(model="qwen3.5-9b-ud:latest", messages=[])

        assert "VRAM budget exceeded" in str(exc_info.value)
        mock_super_chat.assert_not_called()
        mock_callback.assert_called_once_with("qwen3.5-9b-ud:latest")


@pytest.mark.asyncio
async def test_guarded_client_embeddings_triggers_callback_success():
    client = get_ollama_client()
    mock_callback = AsyncMock(return_value=True)
    register_vram_guard_callback(mock_callback)

    with patch("ollama.AsyncClient.embeddings", new_callable=AsyncMock) as mock_super_embeddings:
        mock_super_embeddings.return_value = {"embeddings": [[0.1, 0.2]]}

        resp = await client.embeddings(model="nomic-embed-text-v2-moe-q8:latest", prompt="test")

        mock_callback.assert_called_once_with("nomic-embed-text-v2-moe-q8:latest")
        mock_super_embeddings.assert_called_once()
        assert resp["embeddings"] == [[0.1, 0.2]]
