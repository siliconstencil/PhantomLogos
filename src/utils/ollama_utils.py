import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

import ollama

logger = logging.getLogger(__name__)

# [SRC:axis_11] Callback interface to avoid higher layer violations (src.utils -> src.clotho)
_vram_guard_callback = None


def register_vram_guard_callback(callback: Callable) -> None:
    """Registers a VRAM budget guard callback function from the higher layer."""
    global _vram_guard_callback
    _vram_guard_callback = callback
    logger.info("OllamaUtils: VRAM Guard callback successfully registered.")


class GuardedAsyncClient(ollama.AsyncClient):
    """
    [SRC:axis_11] Safeguarded Ollama Async Client.
    Intercepts all direct chat and embeddings calls to enforce Morpheus VRAMBudgetGuard.
    """

    async def chat(self, model: str, *args: Any, **kwargs: Any) -> Any:
        # 1. Enforce Morpheus VRAMBudgetGuard via registered callback
        global _vram_guard_callback
        if _vram_guard_callback:
            try:
                success = await _vram_guard_callback(model)
                if not success:
                    logger.critical(
                        f"VRAMBudgetGuard: Morpheus VRAMBudgetGuard rejected loading model '{model}' to protect hardware."
                    )
                    raise RuntimeError(
                        f"VRAM budget exceeded. Morpheus VRAMBudgetGuard rejected loading model '{model}' to protect hardware."
                    )
            except RuntimeError:
                raise
            except Exception as e:
                logger.warning(f"GuardedAsyncClient: Safeguard callback failed ({e})")

        return await super().chat(model, *args, **kwargs)

    async def generate(self, model: str, *args: Any, **kwargs: Any) -> Any:
        # 1.5 Enforce Morpheus VRAMBudgetGuard via registered callback
        global _vram_guard_callback
        if _vram_guard_callback:
            try:
                success = await _vram_guard_callback(model)
                if not success:
                    logger.critical(
                        f"VRAMBudgetGuard: Morpheus VRAMBudgetGuard rejected loading model '{model}' to protect hardware."
                    )
                    raise RuntimeError(
                        f"VRAM budget exceeded. Morpheus VRAMBudgetGuard rejected loading model '{model}' to protect hardware."
                    )
            except RuntimeError:
                raise
            except Exception as e:
                logger.warning(f"GuardedAsyncClient: Safeguard callback failed ({e})")

        return await super().generate(model, *args, **kwargs)

    async def embeddings(self, model: str, *args: Any, **kwargs: Any) -> Any:
        # 2. Enforce Morpheus VRAMBudgetGuard via registered callback
        global _vram_guard_callback
        if _vram_guard_callback:
            try:
                success = await _vram_guard_callback(model)
                if not success:
                    logger.critical(
                        f"VRAMBudgetGuard: Morpheus VRAMBudgetGuard rejected loading embedding model '{model}' to protect hardware."
                    )
                    raise RuntimeError(
                        f"VRAM budget exceeded. Morpheus VRAMBudgetGuard rejected loading embedding model '{model}' to protect hardware."
                    )
            except RuntimeError:
                raise
            except Exception as e:
                logger.warning(f"GuardedAsyncClient: Safeguard callback failed ({e})")

        return await super().embeddings(model, *args, **kwargs)


_client: GuardedAsyncClient | None = None
_client_loop_id: int | None = None


def _get_current_loop_id() -> int:
    try:
        loop = asyncio.get_running_loop()
        return id(loop)
    except RuntimeError:
        return -1


def get_ollama_client() -> GuardedAsyncClient:
    """
    Returns a singleton instance of GuardedAsyncClient to prevent socket leaks and protect hardware.
    Recreates the client if the event loop has changed (prevents 'Event loop is closed' errors).
    """
    global _client, _client_loop_id
    current_loop = _get_current_loop_id()
    if _client is not None and _client_loop_id is not None and _client_loop_id != current_loop:
        logger.info("OllamaUtils: Event loop changed, recreating client.")
        _client = None
    if _client is None:
        _client = GuardedAsyncClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        _client_loop_id = current_loop
    return _client
