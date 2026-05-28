import hashlib
import time
from typing import Any

from src.architrave.context_cache import ContextCacheStore
from src.architrave.sovereign_middleware import (
    MiddlewareHook,
    MiddlewareRequest,
    MiddlewareResponse,
    NextHandler,
)
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class ContextCacheMiddleware(MiddlewareHook):
    def __init__(self, ttl_seconds: int = 3600, _max_size_bytes: int = 50 * 1024 * 1024) -> None:
        self.cache = ContextCacheStore(start_sweep=True, sweep_interval=300.0)
        self.ttl_seconds = ttl_seconds

    async def around(self, req: MiddlewareRequest, next: NextHandler, _log: list[dict]) -> Any:
        cache_key = self._build_cache_key(req)
        t_hook = time.time()

        cached = self.cache.get_by_key(cache_key)
        if cached is not None:
            _log.append(
                {
                    "hook": "ContextCache",
                    "action": "hit",
                    "cache_key": cache_key[:16],
                    "ts": time.time() - t_hook,
                }
            )
            logger.info(f"ContextCache: HIT for key {cache_key[:16]}...")
            return MiddlewareResponse(
                text=cached,
                session_id=req.session_id,
                latency_ms=0.0,
                middleware_log=[{"hook": "ContextCache", "action": "hit"}],
            )

        _log.append(
            {
                "hook": "ContextCache",
                "action": "miss",
                "cache_key": cache_key[:16],
                "ts": time.time() - t_hook,
            }
        )
        logger.info(f"ContextCache: MISS for key {cache_key[:16]}...")

        result = await next(req)

        if isinstance(result, MiddlewareResponse) and result.text:
            self.cache.set_by_key(cache_key, result.text, ttl_seconds=self.ttl_seconds)
            _log.append(
                {
                    "hook": "ContextCache",
                    "action": "stored",
                    "cache_key": cache_key[:16],
                    "ts": time.time() - t_hook,
                }
            )

        return result

    def _build_cache_key(self, req: MiddlewareRequest) -> str:
        import re

        prompt = req.prompt or ""
        normalized = re.sub(r"\s+", " ", prompt.strip())
        normalized = re.sub(r"\[?\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?\s*PT\]?", "", normalized)
        normalized = re.sub(
            r"#\s*(Generated|timestamp|Time).*", "", normalized, flags=re.IGNORECASE
        )
        raw = f"{normalized}|{req.system_instruction or ''}|{req.model or ''}|{req.temperature or 0.1}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
