import asyncio
import os
import time
from typing import Any

import httpx
from google.genai import types

from ..utils.logging_config import setup_logger
from .kratos import async_retry, build_safety_settings
from .nomos import log_cache_metrics

logger = setup_logger(__name__)


class AriadneAsyncGateway:
    def __init__(self, gateway: Any) -> None:
        self._gateway = gateway

    async def generate_async(self, prompt: str, **kwargs: Any) -> Any:
        session_id = kwargs.pop("session_id", "default")
        if "safety_settings" not in kwargs:
            kwargs["safety_settings"] = build_safety_settings()

        threshold = int(os.getenv("CLOUD_TOKEN_THRESHOLD", "4000"))
        system_instruction = kwargs.get("system_instruction")
        total_len = len(prompt) + len(system_instruction or "")

        if total_len > threshold * 4:
            logger.info(
                f"Ariadne: Joint Content Guard triggered (total_len={total_len}). Distilling locally..."
            )
            if system_instruction and len(system_instruction) > 6000:
                logger.info(
                    "Ariadne: System instruction exceeds 1500 tokens budget. Distilling system instruction..."
                )
                system_instruction = await self._gateway._local_distill(
                    system_instruction, target_tokens=1500
                )
                kwargs["system_instruction"] = system_instruction

            remaining_chars = (threshold * 4) - len(system_instruction or "")
            remaining_tokens = max(1000, remaining_chars // 4)

            if len(prompt) > remaining_chars:
                logger.info(
                    f"Ariadne: Prompt exceeds remaining budget. Distilling prompt to {remaining_tokens} tokens..."
                )
                prompt = await self._gateway._local_distill(prompt, target_tokens=remaining_tokens)

        if (
            self._gateway.client is None and self._gateway._secondary_client is None
        ) or not await self._gateway.is_gateway_healthy():
            logger.warning(
                "Ariadne: All gateways unhealthy or disabled. Using local fallback directly."
            )
            return await self._gateway._local_fallback(prompt, kwargs.get("system_instruction"))

        model = kwargs.pop("model", self._gateway.default_model)
        thinking_budget = kwargs.pop("thinking_budget", None)
        if thinking_budget is not None:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
        elif kwargs.pop("thinking", False):
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

        now = time.time()
        primary_blocked = now < self._gateway._breaker._cb_until_primary
        resp = None

        if self._gateway.client and not primary_blocked:
            try:

                @async_retry(max_attempts=2, base_delay=2.0)
                async def _call_primary() -> Any:
                    if self._gateway.client is None:
                        raise ValueError("Client is not initialized")
                    cached_content = kwargs.pop("cached_content", None)
                    if cached_content:
                        cache_name = cached_content
                    else:
                        cache_name = await asyncio.to_thread(self._gateway.get_active_cache_name)
                    safety_settings = kwargs.get("safety_settings")
                    other_config = {k: v for k, v in kwargs.items() if k != "safety_settings"}
                    if cache_name:
                        other_config["cached_content"] = cache_name
                    actual_safety = safety_settings or build_safety_settings()
                    client_aio_models: Any = self._gateway.client.aio.models
                    return await client_aio_models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            safety_settings=actual_safety, **other_config
                        ),
                        safety_settings=actual_safety,
                    )

                t0 = time.time()
                resp = await asyncio.wait_for(_call_primary(), timeout=90.0)
                latency_ms = (time.time() - t0) * 1000.0

                if hasattr(resp, "usage_metadata") and resp.usage_metadata is not None:
                    usage = resp.usage_metadata
                    log_cache_metrics(session_id, prompt, usage, latency_ms)
                    cached = getattr(usage, "cached_content_token_count", 0)
                    total = getattr(usage, "total_token_count", 0)
                    if isinstance(cached, (int, float)) and isinstance(total, (int, float)):
                        if cached > 0:
                            logger.info(
                                f"Ariadne: Primary Cache HIT! {cached}/{total} tokens reused ({cached / total:.1%})."
                            )
                        else:
                            logger.info(f"Ariadne: Primary Usage: {total} tokens.")
                return resp

            except asyncio.CancelledError:
                raise
            except TimeoutError:
                logger.warning("Ariadne: Primary generate_async timeout (90s). Triggering CB...")
                self._gateway.trigger_circuit_breaker(30, url_type="primary")
            except (
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                ConnectionRefusedError,
            ) as conn_err:
                self._gateway.trigger_circuit_breaker(30, url_type="primary")
                logger.error(f"Ariadne: Primary connection error -> CB triggered: {conn_err}")
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
                logger.error(
                    f"Ariadne: Primary generate_async API call failed ({type(e).__name__}: {e})"
                )

        secondary_blocked = now < self._gateway._breaker._cb_until_secondary
        if self._gateway._secondary_client and not secondary_blocked:
            try:
                secondary_timeout = float(os.getenv("ANTIGRAVITY_GATEWAY_SECONDARY_TIMEOUT", "2.0"))
                logger.info(f"Ariadne: Calling secondary gateway (timeout={secondary_timeout}s)...")

                @async_retry(max_attempts=1, base_delay=1.0)
                async def _call_secondary() -> Any:
                    if self._gateway._secondary_client is None:
                        raise ValueError("Secondary client is not initialized")
                    safety_settings = kwargs.get("safety_settings")
                    other_config = {k: v for k, v in kwargs.items() if k != "safety_settings"}
                    actual_safety = safety_settings or build_safety_settings()
                    secondary_aio_models: Any = self._gateway._secondary_client.aio.models
                    return await secondary_aio_models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            safety_settings=actual_safety, **other_config
                        ),
                        safety_settings=actual_safety,
                    )

                t0 = time.time()
                resp = await asyncio.wait_for(_call_secondary(), timeout=secondary_timeout)
                latency_ms = (time.time() - t0) * 1000.0

                if hasattr(resp, "usage_metadata") and resp.usage_metadata is not None:
                    usage = resp.usage_metadata
                    log_cache_metrics(session_id, prompt, usage, latency_ms)
                    cached = getattr(usage, "cached_content_token_count", 0)
                    total = getattr(usage, "total_token_count", 0)
                    if isinstance(cached, (int, float)) and isinstance(total, (int, float)):
                        if cached > 0:
                            logger.info(
                                f"Ariadne: Secondary Cache HIT! {cached}/{total} tokens reused ({cached / total:.1%})."
                            )
                        else:
                            logger.info(f"Ariadne: Secondary Usage: {total} tokens.")
                return resp

            except asyncio.CancelledError:
                raise
            except TimeoutError:
                logger.warning("Ariadne: Secondary generate_async timeout. Triggering CB...")
                self._gateway.trigger_circuit_breaker(30, url_type="secondary")
            except (
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                ConnectionRefusedError,
            ) as conn_err:
                self._gateway.trigger_circuit_breaker(30, url_type="secondary")
                logger.error(f"Ariadne: Secondary connection error -> CB triggered: {conn_err}")
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
                logger.error(
                    f"Ariadne: Secondary generate_async API call failed ({type(e).__name__}: {e})"
                )

        return await self._gateway._local_fallback(
            prompt,
            kwargs.get("system_instruction"),
            "Dual-Gateway failover local backup.",
        )
