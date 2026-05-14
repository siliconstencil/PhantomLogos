import asyncio
import os
import random
import time
from functools import wraps

import httpx
from google import genai
from google.genai import types

# Pydantic AI uyumlulugu icin
from pydantic_ai.providers import Provider

from ..utils.logging_config import setup_logger
from .base_models import FALLBACK_MODEL
from .model_registry import LOCAL_REASONING_MODEL, resolve_capability

logger = setup_logger(__name__)


class MockResponse:
    def __init__(
        self,
        text,
        thoughts="Muhakeme yerel olarak gerceklestirildi (API-siz).",
        usage=None,
        model="Unknown",
    ):
        self.text = text
        self.thoughts = thoughts
        self.usage_metadata = usage
        self.model = model


class SovereignProvider(Provider[genai.Client]):
    """Pydantic AI icin Antigravity Gateway saglayicisi."""

    def __init__(self, client: genai.Client, base_url: str, name: str = "sovereign-gateway"):
        self._client = client
        self._base_url = base_url
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def client(self) -> genai.Client:
        return self._client


def async_retry(max_attempts: int = 3, base_delay: float = 1.5):
    """Asenkron fonksiyonlar icin event loop'u bloke etmeyen retry dekoratoru."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    # Antigravity IDE "Channel is full" veya 500/503 durumlarinda agresif retry'dan kacin
                    if "channel is full" in str(e).lower() or "500" in str(e) or "503" in str(e):
                        logger.error(f"Architrave: Kritik kanal hatasi saptandi, retry iptal: {e}")
                        break
                    if attempt < max_attempts:
                        delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0.5, 2.0)
                        logger.warning(
                            f"Architrave: Asenkron yeniden deneme {attempt}/{max_attempts} ({delay:.1f}s) -> {e}"
                        )
                        await asyncio.sleep(delay)
            if last_err:
                raise last_err
            raise RuntimeError("Architrave: Async retry failed without an exception recorded.")

        return wrapper

    return decorator


def retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Senkron fonksiyonlar icin retry dekoratoru."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f"Architrave: Senkron yeniden deneme {attempt}/{max_attempts} ({delay:.1f}s) -> {e}"
                        )
                        time.sleep(delay)
            if last_err:
                raise last_err
            raise RuntimeError("Architrave: Sync retry failed without an exception recorded.")

        return wrapper

    return decorator


class GatewayArchitrave:
    """
    Sovereign Gateway SDK Wrapper (Faz 11.18.1).
    Antigravity Yerel Gecit (Proxy) yonlendirmesini kapsuller.
    Hardened with explicit httpx transports to avoid 'generating/loading' freezes.
    """

    def __init__(self):
        self.client: genai.Client | None = None
        self.sovereign_mode = True
        logger.info("Architrave: Sovereign Gateway Modunda baslatiliyor")

        self.gateway_url = os.getenv("ANTIGRAVITY_GATEWAY_URL", "http://localhost:32553")
        self._circuit_breaker_until = 0
        self._health_cache = {"status": True, "time": 0}
        self._local_fallback_timeout = float(os.getenv("LOCAL_FALLBACK_TIMEOUT", "30.0"))

        try:
            # S5.3: Simplified initialization to prevent IDE hangs
            self.client = genai.Client(
                api_key="antigravity-native",
                http_options=types.HttpOptions(
                    base_url=self.gateway_url,
                    timeout=30000,  # 30s timeout
                ),
            )
            self.default_model = resolve_capability("strategic")
        except Exception as e:
            logger.warning(f"Architrave: Gateway istemcisi baslatma hatasi ({e}).")
            self.client = None
            self.default_model = LOCAL_REASONING_MODEL

    async def is_gateway_healthy(self) -> bool:
        """Gateway'in erisilebilir olup olmadigini kontrol eder (Health Check)."""
        now = time.time()
        if now < self._circuit_breaker_until:
            return False

        if now - self._health_cache["time"] < 10:  # 10s cache (Hardened from 30s)
            return self._health_cache["status"]

        try:
            async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
                resp = await client.get(self.gateway_url)
                is_ok = resp.status_code < 500
                self._health_cache = {"status": is_ok, "time": int(now)}
                return is_ok
        except Exception:
            self.trigger_circuit_breaker(30)  # SoS Fix: Connection failure triggers CB
            self._health_cache = {"status": False, "time": int(now)}
            return False

    def trigger_circuit_breaker(self, duration: int = 30):
        """Gateway'i belirli bir sureligine devre disi birakir (Circuit Breaker)."""
        logger.error(
            f"Architrave: Circuit Breaker tetiklendi! Gateway {duration}s boyunca devre disi."
        )
        self._circuit_breaker_until = int(time.time() + duration)

    def get_gateway_client(self) -> genai.Client:
        return self.client

    def get_provider(self) -> SovereignProvider:
        """Pydantic AI icin SovereignProvider nesnesi doner."""
        client = self.client
        if client is None:
            raise RuntimeError("Architrave: Client baslatilamadigi icin Provider olusturulamaz.")
        return SovereignProvider(client, self.gateway_url)

    @retry(max_attempts=3, base_delay=1.5)
    def create_context_cache(self, anchor_content: str, model: str | None = None):
        if self.client is None:
            return None
        model_str: str = model or self.default_model or LOCAL_REASONING_MODEL
        try:
            # Type safety for IDE
            assert self.client is not None
            assert model_str is not None

            cache = self.client.caches.create(
                model=model_str,
                config=types.CreateCachedContentConfig(
                    contents=[types.Part.from_text(text=anchor_content)],
                    ttl="3600s",
                ),
            )
            return cache
        except Exception as e:
            logger.error(f"Architrave: Context cache creation failed ({e})")
            return None

    async def _local_fallback(
        self, prompt: str, system_instruction: str | None = None, thoughts: str | None = None
    ):
        try:
            # Phase 1.0.8: Relative imports and local constants to prevent hangs
            from ..utils.ollama_utils import get_ollama_client

            client = get_ollama_client()
            # VRAM Guard: Use TinyLlama (SSOT fallback) to prevent OOM/Hang during fallback
            fallback_model = FALLBACK_MODEL

            response = await asyncio.wait_for(
                client.chat(
                    model=fallback_model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_instruction
                            or "Siz yerel bir egemen muhakeme ajanisiniz.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                ),
                timeout=self._local_fallback_timeout,
            )
            usage = {
                "prompt_token_count": response.get("prompt_eval_count", 0),
                "candidates_token_count": response.get("eval_count", 0),
                "total_token_count": response.get("prompt_eval_count", 0)
                + response.get("eval_count", 0),
            }
            # Mock the structure of Google GenAI's UsageMetadata
            from types import SimpleNamespace

            usage_obj = SimpleNamespace(**usage)

            return MockResponse(
                response["message"]["content"],
                thoughts=thoughts,
                usage=usage_obj,
                model=fallback_model,
            )
        except TimeoutError:
            logger.error(
                f"Architrave: Yerel calistirma zaman asimi ({self._local_fallback_timeout}s)"
            )
            return MockResponse(
                f"[SYSTEM GUARD] Gateway baglantisi koptu ve yerel model ({self._local_fallback_timeout}s) zaman asimina ugradi.",
                thoughts="Yerel zaman asimi korumasi tetiklendi.",
            )
        except Exception as e:
            logger.error(f"Architrave: Yerel calistirma basarisiz ({e})")
            return MockResponse(
                f"[SYSTEM GUARD] Yerel calistirma hatasi: {e}", thoughts="Kritik yerel hata."
            )

    def generate(self, prompt: str, **kwargs):
        if self.client is None:
            return asyncio.run(self._local_fallback(prompt, kwargs.get("system_instruction")))
        model = kwargs.pop("model", self.default_model)

        if kwargs.pop("thinking", False):
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

        return self.client.models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(**kwargs)
        )

    async def generate_async(self, prompt: str, **kwargs):
        # Gateway health check ve circuit breaker kontrolu
        if self.client is None or not await self.is_gateway_healthy():
            if self.client:
                logger.warning(
                    "Architrave: Gateway sagliksiz veya devre disi. Dogrudan yerel yedek kullaniliyor."
                )
            return await self._local_fallback(prompt, kwargs.get("system_instruction"))

        model = kwargs.pop("model", self.default_model)
        if kwargs.pop("thinking", False):
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

        try:
            # Wrap the API call with async_retry
            @async_retry(max_attempts=2, base_delay=2.0)
            async def _call():
                return await self.client.aio.models.generate_content(
                    model=model, contents=prompt, config=types.GenerateContentConfig(**kwargs)
                )

            resp = await asyncio.wait_for(_call(), timeout=90.0)  # Hardened to 90s

            # Phase 11.21.3: Token Consumption Metrics
            if hasattr(resp, "usage_metadata"):
                usage = resp.usage_metadata
                cached = getattr(usage, "cached_content_token_count", 0) or 0
                total = getattr(usage, "total_token_count", 0) or 1
                if cached > 0:
                    logger.info(
                        f"Architrave: Cache HIT! {cached}/{total} tokens reused ({cached / total:.1%})."
                    )
                else:
                    logger.info(f"Architrave: Usage: {total} tokens (No cache hit).")

            return resp

        except asyncio.CancelledError:
            raise
        except TimeoutError:
            logger.warning("Architrave: generate_async timeout (90s). Falling back to local.")
            return await self._local_fallback(
                prompt, kwargs.get("system_instruction"), "Zaman asimi yerel yedegi."
            )
        except (httpx.ConnectError, httpx.RemoteProtocolError, ConnectionRefusedError) as conn_err:
            self.trigger_circuit_breaker(30)
            logger.error(f"Architrave: Gateway baglanti hatasi -> CB tetiklendi (30s): {conn_err}")
            return await self._local_fallback(
                prompt, kwargs.get("system_instruction"), f"Proxy kapali: {conn_err}"
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "channel is full" in err_msg or "500" in err_msg or "503" in err_msg:
                self.trigger_circuit_breaker(30)  # 30s dinlendir

            logger.error(f"Architrave: generate_async API call failed ({type(e).__name__}: {e})")
            if "ValidationError" in type(e).__name__:
                raise
            return await self._local_fallback(
                prompt, kwargs.get("system_instruction"), f"API Hata yedegi: {e}"
            )
