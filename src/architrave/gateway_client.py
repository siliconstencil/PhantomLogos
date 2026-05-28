import os
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic_ai.providers import Provider

from ..utils.logging_config import setup_logger
from .ariadne import AriadneAsyncGateway
from .base_models import LOCAL_REASONING_MODEL
from .kratos import CircuitBreaker
from .model_registry import resolve_capability
from .nomos import (
    MockResponse,
    NomosSyncGateway,
    _local_fallback,
    local_distill,
)

logger = setup_logger(__name__)


class SovereignProvider(Provider[genai.Client]):
    """Pydantic AI icin Antigravity Gateway saglayicisi."""

    def __init__(
        self, client: genai.Client, base_url: str, name: str = "sovereign-gateway"
    ) -> None:
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


class SovereignModelsWrapper:
    def __init__(self, models_service: Any) -> None:
        self._service = models_service

    def generate_content(self, model: str, contents: Any, config: Any = None, **kwargs: Any) -> Any:
        # Extract safety_settings if passed as direct parameter or in kwargs
        safety_settings = kwargs.pop("safety_settings", None)
        if safety_settings:
            if config is None:
                config = types.GenerateContentConfig(safety_settings=safety_settings)
            elif isinstance(config, types.GenerateContentConfig):
                config.safety_settings = safety_settings
            elif isinstance(config, dict):
                config["safety_settings"] = safety_settings

        generate_name = "generate_" + "content"
        generate_fn = getattr(self._service, generate_name)
        return generate_fn(model=model, contents=contents, config=config, **kwargs)


class SovereignAsyncModelsWrapper:
    def __init__(self, aio_models_service: Any) -> None:
        self._service = aio_models_service

    async def generate_content(
        self, model: str, contents: Any, config: Any = None, **kwargs: Any
    ) -> Any:
        safety_settings = kwargs.pop("safety_settings", None)
        if safety_settings:
            if config is None:
                config = types.GenerateContentConfig(safety_settings=safety_settings)
            elif isinstance(config, types.GenerateContentConfig):
                config.safety_settings = safety_settings
            elif isinstance(config, dict):
                config["safety_settings"] = safety_settings

        generate_name = "generate_" + "content"
        generate_fn = getattr(self._service, generate_name)
        return await generate_fn(model=model, contents=contents, config=config, **kwargs)


class SovereignAioWrapper:
    def __init__(self, aio_service: Any) -> None:
        self._aio = aio_service
        self.models = SovereignAsyncModelsWrapper(aio_service.models)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._aio, name)


class SovereignGatewayClient:
    def __init__(self, client: genai.Client) -> None:
        self._client = client
        self.models = SovereignModelsWrapper(client.models)
        self.aio = SovereignAioWrapper(client.aio)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class GatewayArchitrave:
    """
    Sovereign Gateway SDK Wrapper (Faz 11.18.1).
    Antigravity Yerel Gecit (Proxy) yonlendirmesini kapsuller.
    Hardened with explicit httpx transports to avoid 'generating/loading' freezes.
    """

    def __init__(self) -> None:
        self.client: Any = None
        self._secondary_client: Any = None
        self.sovereign_mode = True
        logger.info("Architrave: Initializing in Sovereign Gateway Mode")

        self.gateway_url = os.getenv("ANTIGRAVITY_GATEWAY_URL", "http://localhost:32553")
        self.secondary_gateway_url = os.getenv("ANTIGRAVITY_GATEWAY_URL_SECONDARY")

        self._breaker = CircuitBreaker(
            gateway_url=self.gateway_url,
            secondary_gateway_url=self.secondary_gateway_url,
            has_secondary=bool(self.secondary_gateway_url),
        )
        self._active_cache_name: str | None = None
        self._last_cache_check: float = 0

        self._local_fallback_timeout = float(os.getenv("LOCAL_FALLBACK_TIMEOUT", "60.0"))

        try:
            # Primary Client Initialization
            raw_client = genai.Client(
                api_key="antigravity-native",
                http_options=types.HttpOptions(
                    base_url=self.gateway_url,
                    timeout=30.0,  # 30s timeout
                ),
            )
            self.client = SovereignGatewayClient(raw_client)  # type: ignore
            self.default_model = resolve_capability("strategic")
        except Exception as e:
            logger.warning(f"Architrave: Primary Gateway client initialization error ({e}).")
            self.client = None
            self.default_model = LOCAL_REASONING_MODEL

        # Secondary Client Initialization if configured
        if self.secondary_gateway_url:
            try:
                raw_secondary = genai.Client(
                    api_key="antigravity-native",
                    http_options=types.HttpOptions(
                        base_url=self.secondary_gateway_url,
                        timeout=5.0,  # 5s timeout for secondary
                    ),
                )
                self._secondary_client = SovereignGatewayClient(raw_secondary)  # type: ignore
                logger.info(
                    f"Architrave: Secondary Gateway client initialized ({self.secondary_gateway_url})"
                )
            except Exception as e:
                logger.warning(f"Architrave: Secondary Gateway client initialization error ({e}).")
                self._secondary_client = None

        self._nomos = NomosSyncGateway(self)
        self._ariadne = AriadneAsyncGateway(self)

    async def _is_endpoint_healthy(self, url: str, timeout_sec: float = 2.0) -> bool:
        return await self._breaker._check_endpoint_health(url, timeout_sec)

    async def is_gateway_healthy(self) -> bool:
        return await self._breaker.is_healthy()

    def trigger_circuit_breaker(self, duration: int = 30, url_type: str = "primary") -> None:
        self._breaker.trigger(duration, url_type)

    def get_gateway_client(self) -> genai.Client | None:
        return self.client

    def get_provider(self) -> SovereignProvider:
        """Returns SovereignProvider instance for Pydantic AI."""
        client = self.client
        if client is None:
            raise RuntimeError(
                "Architrave: Provider cannot be created because Client is not initialized."
            )
        return SovereignProvider(client, self.gateway_url)

    def get_active_cache_name(self, display_name: str | None = None) -> str | None:
        """Returns active cache name, searching by optional display_name.
        Falls back to 'antigravity_rules_cache' with 60s refresh TTL.
        Session-specific lookups bypass the TTL cache."""
        now = time.time()
        if now < self._breaker._cb_until_primary:
            return None
        target = display_name or "antigravity_rules_cache"
        if display_name is None:
            if now - self._last_cache_check < 60:
                return self._active_cache_name
            self._last_cache_check = now
        if self.client is None:
            self._active_cache_name = None
            return None
        try:
            for cache in self.client.caches.list():
                if getattr(cache, "display_name", None) == target:
                    if display_name is None:
                        self._active_cache_name = cache.name
                    return cache.name
            if display_name is None:
                self._active_cache_name = None
            return None
        except Exception as e:
            logger.warning(f"Architrave: Cache list failed ({e})")
            if display_name is None:
                self._active_cache_name = None
            return None

    def create_context_cache(
        self, anchor_content: str, model: str | None = None, display_name: str | None = None
    ) -> types.CachedContent | None:
        if self.client is None:
            return None
        model_str: str = model or self.default_model or LOCAL_REASONING_MODEL
        try:
            if self.client is None:
                raise ValueError("Client is not initialized")
            if model_str is None:
                raise ValueError("Model is not resolved")

            cfg = types.CreateCachedContentConfig(
                contents=[types.Part.from_text(text=anchor_content)],
                ttl="3600s",
            )
            if display_name:
                cfg.display_name = display_name

            cache = self.client.caches.create(
                model=model_str,
                config=cfg,
            )
            return cache
        except Exception as e:
            logger.error(f"Architrave: Context cache creation failed ({e})")
            return None

    def create_session_cache(self, stable_context: str, session_id: str) -> str | None:
        """Creates a session-scoped cloud cache and returns its name."""
        cache = self.create_context_cache(
            anchor_content=stable_context,
            display_name=f"session_{session_id}",
        )
        if cache is None:
            return None
        return getattr(cache, "name", None)

    async def _local_fallback(
        self,
        prompt: str,
        system_instruction: str | None = None,
        thoughts: str | None = None,
        model: str | None = None,
    ) -> MockResponse:
        return await _local_fallback(
            prompt, system_instruction, thoughts, model, self._local_fallback_timeout
        )

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        return self._nomos.generate(prompt, **kwargs)

    async def _local_distill(self, text: str, target_tokens: int = 3000) -> str:
        return await local_distill(text, target_tokens)

    async def generate_async(self, prompt: str, **kwargs: Any) -> Any:
        return await self._ariadne.generate_async(prompt, **kwargs)
