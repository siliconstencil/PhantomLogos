import asyncio
import secrets
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import httpx
from google.genai import types

from ..utils.logging_config import setup_logger

logger = setup_logger(__name__)


def build_safety_settings() -> list[types.SafetySetting]:
    return [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ]


def async_retry(
    max_attempts: int = 3, base_delay: float = 1.5
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
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
                        logger.error(
                            f"Kratos: Critical channel/quota error detected, retry cancelled: {e}"
                        )
                        break
                    if attempt < max_attempts:
                        delay = (
                            base_delay * (2 ** (attempt - 1))
                        ) + secrets.SystemRandom().uniform(0.5, 2.0)
                        logger.warning(
                            f"Kratos: Async retry {attempt}/{max_attempts} ({delay:.1f}s) -> {e}"
                        )
                        await asyncio.sleep(delay)
            if last_err:
                raise last_err
            raise RuntimeError("Kratos: Async retry failed without an exception recorded.")

        return wrapper

    return decorator


def retry(
    max_attempts: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_attempts:
                        delay = (
                            base_delay * (2 ** (attempt - 1))
                        ) + secrets.SystemRandom().uniform(0.5, 2.0)
                        logger.warning(
                            f"Kratos: Sync retry {attempt}/{max_attempts} ({delay:.1f}s) -> {e}"
                        )
                        time.sleep(delay)
            if last_err:
                raise last_err
            raise RuntimeError("Kratos: Sync retry failed without an exception recorded.")

        return wrapper

    return decorator


class CircuitBreaker:
    def __init__(
        self,
        gateway_url: str,
        secondary_gateway_url: str | None = None,
        has_secondary: bool = False,
    ) -> None:
        self.gateway_url = gateway_url
        self.secondary_gateway_url = secondary_gateway_url
        self._has_secondary = has_secondary
        self._cb_until_primary: float = 0
        self._cb_until_secondary: float = 0
        self._health_cache_primary: dict = {"status": True, "time": 0}
        self._health_cache_secondary: dict = {"status": True, "time": 0}

    def trigger(self, duration: int = 30, url_type: str = "primary") -> None:
        logger.error(
            f"Kratos: Circuit Breaker triggered! Endpoint '{url_type}' disabled for {duration}s."
        )
        if url_type == "primary":
            self._cb_until_primary = int(time.time() + duration)
        else:
            self._cb_until_secondary = int(time.time() + duration)

    async def _check_endpoint_health(self, url: str, timeout_sec: float = 2.0) -> bool:
        try:
            async with httpx.AsyncClient(timeout=timeout_sec, trust_env=False) as client:
                resp = await client.get(url)
                return resp.status_code < 500
        except Exception:
            return False

    async def is_healthy(self) -> bool:
        now = time.time()
        primary_blocked = now < self._cb_until_primary
        primary_healthy = False
        if not primary_blocked:
            if now - self._health_cache_primary["time"] < 10:
                primary_healthy = self._health_cache_primary["status"]
            else:
                primary_healthy = await self._check_endpoint_health(
                    self.gateway_url, timeout_sec=2.0
                )
                if not primary_healthy:
                    self.trigger(30, url_type="primary")
                self._health_cache_primary = {"status": primary_healthy, "time": int(now)}
        secondary_blocked = True
        secondary_healthy = False
        if self._has_secondary and self.secondary_gateway_url:
            secondary_blocked = now < self._cb_until_secondary
            if not secondary_blocked:
                if now - self._health_cache_secondary["time"] < 5:
                    secondary_healthy = self._health_cache_secondary["status"]
                else:
                    secondary_healthy = await self._check_endpoint_health(
                        self.secondary_gateway_url, timeout_sec=2.0
                    )
                    if not secondary_healthy:
                        self.trigger(30, url_type="secondary")
                    self._health_cache_secondary = {"status": secondary_healthy, "time": int(now)}
        is_primary_ok = (not primary_blocked) and primary_healthy
        is_secondary_ok = (
            (not secondary_blocked) and secondary_healthy if self._has_secondary else False
        )
        return is_primary_ok or is_secondary_ok
