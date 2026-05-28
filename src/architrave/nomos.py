import asyncio
import hashlib
import os
import re
import sqlite3
import time
from types import SimpleNamespace
from typing import Any

import numpy as np
from google.genai import types

from ..utils.logging_config import setup_logger
from ..utils.run_async import run_async
from .kratos import build_safety_settings, retry

logger = setup_logger(__name__)


def log_cache_metrics(session_id: str, prompt: str, usage: Any, latency_ms: float) -> None:
    try:
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        cached_tokens = getattr(usage, "cached_content_token_count", 0) or 0
        prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", 0) or 0

        if cached_tokens == 0:
            hit_status = "miss"
        elif cached_tokens >= prompt_tokens and prompt_tokens > 0:
            hit_status = "hit"
        else:
            hit_status = "partial"

        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base, "data", "mnemosyne.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path, timeout=10.0)
        try:
            conn.execute(
                """
                INSERT INTO axis_12_cache_metrics (session_id, prompt_hash, cached_tokens, total_tokens, latency_ms, hit_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (session_id, prompt_hash, cached_tokens, total_tokens, latency_ms, hit_status),
            )
            conn.commit()
        except Exception as db_err:
            logger.warning(f"Nomos: DB insertion failed in log_cache_metrics ({db_err})")
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Nomos: Failed to log cache metrics ({e})")


class MockResponse:
    def __init__(
        self,
        text: str,
        thoughts: str = "Reasoning performed locally (without API).",
        usage: Any = None,
        model: str = "Unknown",
    ) -> None:
        self.text = text
        self.thoughts = thoughts
        self.usage_metadata = usage
        self.model = model


async def local_distill(text: str, target_tokens: int = 3000) -> str:
    try:
        from src.utils.service_locator import get_matryoshka

        matryoshka = get_matryoshka()
        if not matryoshka:
            return text[: target_tokens * 4]

        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(chunks) <= 3:
            chunks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        if len(chunks) > 50:
            chunks = chunks[:50]

        if len(chunks) <= 5:
            return text[: target_tokens * 4]

        valid_chunks = [c for c in chunks if len(c) >= 20]
        if not valid_chunks:
            return text[: target_tokens * 4]

        tasks = [matryoshka.embed_document(text[:8192])]
        tasks.extend(matryoshka.embed_document(c) for c in valid_chunks)

        vectors = await asyncio.gather(*tasks)
        full_vec = vectors[0]
        chunk_vecs = vectors[1:]

        scored_chunks = []
        for c, c_vec in zip(valid_chunks, chunk_vecs, strict=False):
            score = np.dot(full_vec, c_vec)
            scored_chunks.append((score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        first = chunks[0]
        last = chunks[-1]

        distilled = [first]
        current_len = len(first)

        for _, c in scored_chunks:
            if c in (first, last):
                continue
            if current_len + len(c) < target_tokens * 4:
                distilled.append(c)
                current_len += len(c)

        if first != last and last not in distilled:
            distilled.append(last)

        logger.info(f"Nomos: Distillation complete ({len(chunks)} -> {len(distilled)} chunks).")
        return " ... ".join(distilled)
    except Exception as e:
        logger.warning(f"Nomos: Distillation failed ({e})")
        return text[: target_tokens * 4]


async def _local_fallback(
    prompt: str,
    system_instruction: str | None = None,
    thoughts: str | None = None,
    model: str | None = None,
    local_fallback_timeout: float = 60.0,
) -> MockResponse:
    try:
        from ..utils.ollama_utils import get_ollama_client

        client = get_ollama_client()
        from .base_models import FALLBACK_MODEL, LOCAL_REASONING_MODEL

        fallback_model = model or FALLBACK_MODEL or LOCAL_REASONING_MODEL

        response = await asyncio.wait_for(
            client.chat(
                model=fallback_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction
                        or "You are a local sovereign reasoning agent.",
                    },
                    {"role": "user", "content": prompt},
                ],
            ),
            timeout=local_fallback_timeout,
        )
        usage = {
            "prompt_token_count": response.get("prompt_eval_count", 0),
            "candidates_token_count": response.get("eval_count", 0),
            "total_token_count": response.get("prompt_eval_count", 0)
            + response.get("eval_count", 0),
        }
        usage_obj = SimpleNamespace(**usage)

        return MockResponse(
            response["message"]["content"],
            thoughts=thoughts,
            usage=usage_obj,
            model=fallback_model,
        )
    except TimeoutError:
        logger.error(f"Nomos: Local execution timeout ({local_fallback_timeout}s)")
        return MockResponse(
            f"[SYSTEM GUARD] Gateway connection lost and local model timed out ({local_fallback_timeout}s).",
            thoughts="Local timeout protection triggered.",
        )
    except Exception as e:
        logger.error(f"Nomos: Local execution failed ({e})")
        return MockResponse(
            f"[SYSTEM GUARD] Local execution error: {e}", thoughts="Critical local error."
        )


class NomosSyncGateway:
    def __init__(self, gateway: Any) -> None:
        self._gateway = gateway

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        session_id = kwargs.pop("session_id", "default")
        model = kwargs.pop("model", self._gateway.default_model)
        thinking_budget = kwargs.pop("thinking_budget", None)
        if thinking_budget is not None:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
        elif kwargs.pop("thinking", False):
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

        if "safety_settings" not in kwargs:
            kwargs["safety_settings"] = build_safety_settings()

        def _run_sync(coro: Any) -> Any:
            return run_async(coro, timeout=120.0)

        threshold = int(os.getenv("CLOUD_TOKEN_THRESHOLD", "4000"))
        system_instruction = kwargs.get("system_instruction")
        total_len = len(prompt) + len(system_instruction or "")

        if total_len > threshold * 4:
            logger.info(
                f"Nomos: Sync Joint Content Guard triggered (total_len={total_len}). Distilling locally..."
            )

            if system_instruction and len(system_instruction) > 6000:
                logger.info(
                    "Nomos: Sync system instruction exceeds 1500 tokens budget. Distilling system instruction..."
                )
                system_instruction = _run_sync(
                    local_distill(system_instruction, target_tokens=1500)
                )
                kwargs["system_instruction"] = system_instruction

            remaining_chars = (threshold * 4) - len(system_instruction or "")
            remaining_tokens = max(1000, remaining_chars // 4)

            if len(prompt) > remaining_chars:
                logger.info(
                    f"Nomos: Sync prompt exceeds remaining budget. Distilling prompt to {remaining_tokens} tokens..."
                )
                prompt = _run_sync(local_distill(prompt, target_tokens=remaining_tokens))

        now = time.time()
        _breaker = self._gateway._breaker
        primary_blocked = now < _breaker._cb_until_primary

        if self._gateway.client and not primary_blocked:
            try:

                @retry(max_attempts=2, base_delay=1.5)
                def _call_primary_sync() -> Any:
                    if self._gateway.client is None:
                        raise ValueError("Client is not initialized")
                    cached_content = kwargs.pop("cached_content", None)
                    cache_name = (
                        cached_content if cached_content else self._gateway.get_active_cache_name()
                    )
                    safety_settings = kwargs.get("safety_settings")
                    other_config = {k: v for k, v in kwargs.items() if k != "safety_settings"}
                    if cache_name:
                        other_config["cached_content"] = cache_name
                    actual_safety = safety_settings or build_safety_settings()
                    client_models: Any = self._gateway.client.models
                    return client_models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            safety_settings=actual_safety, **other_config
                        ),
                        safety_settings=actual_safety,
                    )

                t0 = time.time()
                resp = _call_primary_sync()
                latency_ms = (time.time() - t0) * 1000.0
                if hasattr(resp, "usage_metadata") and resp.usage_metadata is not None:
                    log_cache_metrics(session_id, prompt, resp.usage_metadata, latency_ms)
                return resp
            except Exception as e:
                if "ValidationError" in type(e).__name__:
                    raise
                err_msg = str(e).lower()
                if any(
                    kw in err_msg
                    for kw in [
                        "channel is full",
                        "500",
                        "503",
                        "429",
                        "quota",
                        "limit",
                        "exhausted",
                        "overloaded",
                    ]
                ):
                    self._gateway.trigger_circuit_breaker(30, url_type="primary")
                logger.error(f"Nomos: Primary synchronous generate error: {e}")

        secondary_blocked = now < _breaker._cb_until_secondary
        if self._gateway._secondary_client and not secondary_blocked:
            try:
                logger.info("Nomos: Calling secondary gateway synchronously...")

                @retry(max_attempts=1, base_delay=1.0)
                def _call_secondary_sync() -> Any:
                    if self._gateway._secondary_client is None:
                        raise ValueError("Secondary client is not initialized")
                    safety_settings = kwargs.get("safety_settings")
                    other_config = {k: v for k, v in kwargs.items() if k != "safety_settings"}
                    actual_safety = safety_settings or build_safety_settings()
                    secondary_models: Any = self._gateway._secondary_client.models
                    return secondary_models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            safety_settings=actual_safety, **other_config
                        ),
                        safety_settings=actual_safety,
                    )

                t0 = time.time()
                resp = _call_secondary_sync()
                latency_ms = (time.time() - t0) * 1000.0
                if hasattr(resp, "usage_metadata") and resp.usage_metadata is not None:
                    log_cache_metrics(session_id, prompt, resp.usage_metadata, latency_ms)
                return resp
            except Exception as e:
                if "ValidationError" in type(e).__name__:
                    raise
                err_msg = str(e).lower()
                if any(
                    kw in err_msg
                    for kw in [
                        "channel is full",
                        "500",
                        "503",
                        "429",
                        "quota",
                        "limit",
                        "exhausted",
                        "overloaded",
                    ]
                ):
                    self._gateway.trigger_circuit_breaker(30, url_type="secondary")
                logger.error(f"Nomos: Secondary synchronous generate error: {e}")

        return run_async(
            self._gateway._local_fallback(
                prompt,
                kwargs.get("system_instruction"),
                "Dual-Gateway synchronous failover local backup.",
            ),
            timeout=120.0,
        )
