import contextlib
import time
from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field

from cognition.mnemosyne.episodic_store import EpisodicStore
from src.architrave.gateway_client import GatewayArchitrave, MockResponse
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class MiddlewareRequest(BaseModel):
    prompt: str
    system_instruction: str | None = None
    model: str | None = None
    session_id: str = "default"
    thinking: bool = False
    thinking_budget: int | None = None
    temperature: float | None = 0.1
    max_output_tokens: int | None = None
    stream: bool = False


class MiddlewareResponse(BaseModel):
    text: str
    thoughts: str | None = None
    model: str | None = None
    session_id: str = "default"
    latency_ms: float = 0.0
    token_usage: dict[str, Any] = Field(default_factory=dict)
    middleware_log: list[dict[str, Any]] = Field(default_factory=list)


class NextHandler:
    def __init__(self, handler: Callable[[MiddlewareRequest], Any]) -> None:
        self._handler = handler

    async def __call__(self, req: MiddlewareRequest) -> Any:
        return await self._handler(req)


class MiddlewareHook:
    async def before(self, req: MiddlewareRequest, _log: list[dict]) -> MiddlewareRequest | None:
        return req

    async def around(self, req: MiddlewareRequest, next: NextHandler, _log: list[dict]) -> Any:
        return await next(req)

    async def after(self, _req: MiddlewareRequest, resp: Any, _log: list[dict]) -> Any:
        return resp


class MiddlewarePipeline:
    def __init__(self) -> None:
        self._before_hooks: list[MiddlewareHook] = []
        self._around_hooks: list[MiddlewareHook] = []
        self._after_hooks: list[MiddlewareHook] = []
        self._gateway: GatewayArchitrave | None = None

    def add_before(self, hook: MiddlewareHook) -> None:
        self._before_hooks.append(hook)

    def add_around(self, hook: MiddlewareHook) -> None:
        self._around_hooks.append(hook)

    def add_after(self, hook: MiddlewareHook) -> None:
        self._after_hooks.append(hook)

    def set_gateway(self, gateway: GatewayArchitrave) -> None:
        self._gateway = gateway

    async def _gateway_handler(self, req: MiddlewareRequest) -> MiddlewareResponse:
        gw = self._gateway or GatewayArchitrave()
        t0 = time.time()
        kwargs = {}
        if req.system_instruction:
            kwargs["system_instruction"] = req.system_instruction
        if req.thinking:
            kwargs["thinking"] = True
        if req.thinking_budget:
            kwargs["thinking_budget"] = req.thinking_budget
        if req.temperature is not None:
            kwargs["temperature"] = req.temperature
        if req.max_output_tokens:
            kwargs["max_output_tokens"] = req.max_output_tokens
        kwargs["session_id"] = req.session_id
        kwargs["model"] = req.model

        if req.stream:
            return await self._stream_handler(gw, req, kwargs)

        resp = await gw.generate_async(req.prompt, **kwargs)
        latency_ms = (time.time() - t0) * 1000.0

        if isinstance(resp, MockResponse):
            return MiddlewareResponse(
                text=resp.text,
                thoughts=resp.thoughts,
                model=resp.model or req.model,
                session_id=req.session_id,
                latency_ms=latency_ms,
                token_usage=self._extract_usage(resp),
            )

        text = getattr(resp, "text", str(resp))
        thoughts = None
        with contextlib.suppress(Exception):
            thoughts = getattr(resp, "thoughts", None)
        model = getattr(resp, "model", req.model)
        usage = self._extract_usage(resp)

        return MiddlewareResponse(
            text=text,
            thoughts=thoughts,
            model=model,
            session_id=req.session_id,
            latency_ms=latency_ms,
            token_usage=usage,
        )

    async def _stream_handler(
        self, gw: GatewayArchitrave, req: MiddlewareRequest, kwargs: dict
    ) -> MiddlewareResponse:
        chunks = [chunk async for chunk in gw.generate_async_stream(req.prompt, **kwargs)]
        return MiddlewareResponse(
            text="".join(chunks),
            session_id=req.session_id,
            latency_ms=0.0,
            token_usage={"streamed_chunks": len(chunks)},
        )

    def _extract_usage(self, resp: Any) -> dict[str, Any]:
        try:
            usage = getattr(resp, "usage_metadata", None) or getattr(resp, "usage", None)
            if usage:
                return {
                    "prompt_tokens": getattr(usage, "prompt_token_count", 0)
                    or getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "candidates_token_count", 0)
                    or getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_token_count", 0)
                    or getattr(usage, "total_tokens", 0),
                    "cached_tokens": getattr(usage, "cached_content_token_count", 0),
                }
        except Exception as e:
            logger.debug(f"SovereignMiddleware: usage extraction skipped ({e})")
        return {}

    async def execute(self, req: MiddlewareRequest) -> MiddlewareResponse:
        log: list[dict[str, Any]] = []
        t_start = time.time()

        log.append({"hook": "pipeline_start", "ts": t_start})

        modified_req = req
        for hook in self._before_hooks:
            t_hook = time.time()
            try:
                result = await hook.before(modified_req, log)
                if result is None:
                    log.append(
                        {
                            "hook": type(hook).__name__,
                            "action": "blocked",
                            "ts": time.time() - t_hook,
                        }
                    )
                    return MiddlewareResponse(
                        text="[MIDDLEWARE GUARD] Request blocked by before-hook.",
                        session_id=req.session_id,
                        latency_ms=(time.time() - t_start) * 1000.0,
                        middleware_log=log,
                    )
                modified_req = result
                log.append(
                    {"hook": type(hook).__name__, "action": "passed", "ts": time.time() - t_hook}
                )
            except Exception as e:
                log.append({"hook": type(hook).__name__, "action": "error", "error": str(e)})
                return MiddlewareResponse(
                    text=f"[MIDDLEWARE ERROR] Before-hook failed: {e}",
                    session_id=req.session_id,
                    latency_ms=(time.time() - t_start) * 1000.0,
                    middleware_log=log,
                )

        next_handler = NextHandler(self._gateway_handler)
        final_resp: MiddlewareResponse | None = None

        for hook in self._around_hooks:
            t_hook = time.time()
            current_handler = next_handler

            async def _wrap_around(
                h: MiddlewareHook = hook,
                nh: NextHandler = current_handler,
                mr: MiddlewareRequest = modified_req,
            ) -> Any:
                return await h.around(mr, nh, log)

            result = await _wrap_around(hook, next_handler)
            if isinstance(result, MiddlewareResponse):
                final_resp = result
                log.append(
                    {
                        "hook": type(hook).__name__,
                        "action": "short_circuit" if result.middleware_log else "proxied",
                        "ts": time.time() - t_hook,
                    }
                )
                break
            elif result is not None:
                modified_req = result if isinstance(result, MiddlewareRequest) else modified_req
                log.append(
                    {"hook": type(hook).__name__, "action": "modified", "ts": time.time() - t_hook}
                )

        if final_resp is None:
            final_resp = await next_handler(modified_req)
            log.append({"hook": "gateway_direct", "ts": time.time() - t_start})

        if final_resp is None:
            raise RuntimeError("SovereignMiddleware: pipeline produced no response")

        for hook in self._after_hooks:
            t_hook = time.time()
            try:
                result = await hook.after(modified_req, final_resp, log)
                if isinstance(result, MiddlewareResponse):
                    final_resp = result
                log.append(
                    {"hook": type(hook).__name__, "action": "completed", "ts": time.time() - t_hook}
                )
            except Exception as e:
                log.append({"hook": type(hook).__name__, "action": "error", "error": str(e)})

        total_ms = (time.time() - t_start) * 1000.0
        final_resp.latency_ms = total_ms
        final_resp.middleware_log = log

        try:
            store = EpisodicStore()
            store.log(
                session_id=req.session_id,
                action="middleware_pipeline",
                agent_id="sovereign_middleware",
                detail=f"Pipeline completed: {len(self._before_hooks)} before, {len(self._around_hooks)} around, {len(self._after_hooks)} after hooks",
                outcome="completed",
                latency_ms=total_ms,
                tokens_used=final_resp.token_usage.get("total_tokens", 0),
            )
        except Exception as e:
            logger.warning(f"SovereignMiddleware: Episodic log failed ({e})")

        return final_resp


class AntiLoopCircuitBreaker(MiddlewareHook):
    def __init__(self, max_loop_count: int = 3, cooldown_seconds: float = 30.0) -> None:
        self.max_loop_count = max_loop_count
        self.cooldown_seconds = cooldown_seconds
        self._loop_count: dict[str, int] = {}
        self._blocked_until: dict[str, float] = {}

    async def before(self, req: MiddlewareRequest, _log: list[dict]) -> MiddlewareRequest | None:
        import hashlib

        sid = req.session_id
        now = time.time()

        # Component 4: Hash of first 512 chars of the prompt to avoid cosmetic manipulation loop escapes
        prompt_hash = hashlib.sha256(req.prompt[:512].encode("utf-8")).hexdigest()[:16]
        key = f"{sid}:{prompt_hash}"

        if key in self._blocked_until and now < self._blocked_until[key]:
            _log.append(
                {
                    "hook": "AntiLoopCB",
                    "action": "blocked",
                    "reason": "circuit_open",
                    "until": self._blocked_until[key],
                }
            )
            return None

        if key not in self._loop_count:
            self._loop_count[key] = 0
        self._loop_count[key] += 1

        if self._loop_count[key] > self.max_loop_count:
            self._blocked_until[key] = now + self.cooldown_seconds
            _log.append(
                {
                    "hook": "AntiLoopCB",
                    "action": "tripped",
                    "count": self._loop_count[key],
                    "cooldown": self.cooldown_seconds,
                }
            )
            return None

        return req

    def reset(self, session_id: str) -> None:
        prefix = f"{session_id}:"
        for k in list(self._loop_count.keys()):
            if k.startswith(prefix) or k == session_id:
                self._loop_count.pop(k, None)
        for k in list(self._blocked_until.keys()):
            if k.startswith(prefix) or k == session_id:
                self._blocked_until.pop(k, None)


class SovereignMiddlewareServer:
    def __init__(
        self,
        pipeline: MiddlewarePipeline | None = None,
        host: str = "0.0.0.0",
        port: int = 32556,  # noqa: S104
    ) -> None:
        self.pipeline = pipeline or MiddlewarePipeline()
        self.host = host
        self.port = port
        self.app = FastAPI(title="Sovereign Middleware Proxy", version="1.0.0")
        self._setup_routes()

    def _setup_routes(self) -> None:
        app = self.app

        @app.get("/health")
        async def health() -> dict[str, Any]:
            return {"status": "ok", "service": "sovereign-middleware", "port": self.port}

        @app.post("/v1/generate", response_model=MiddlewareResponse)
        async def generate(request: Request) -> MiddlewareResponse:
            body = await request.json()
            mw_req = MiddlewareRequest(**body)
            return await self.pipeline.execute(mw_req)

        @app.post("/v1/stream")
        async def generate_stream(request: Request) -> Response:
            body = await request.json()
            mw_req = MiddlewareRequest(**{**body, "stream": True})
            result = await self.pipeline.execute(mw_req)
            return Response(
                content=result.model_dump_json(),
                media_type="application/json",
            )

        @app.post("/v1/reset_loop/{session_id}")
        async def reset_loop(session_id: str) -> dict[str, Any]:
            for hook in self.pipeline._before_hooks:
                if isinstance(hook, AntiLoopCircuitBreaker):
                    hook.reset(session_id)
            return {"status": "reset", "session_id": session_id}

    async def start(self) -> None:
        logger.info(f"SovereignMiddleware: Starting server on {self.host}:{self.port}")
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def start_sync(self) -> None:
        logger.info(f"SovereignMiddleware: Starting server (sync) on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


def create_default_pipeline() -> MiddlewarePipeline:
    from src.atropos.context_cache_middleware import ContextCacheMiddleware
    from src.atropos.token_budget_middleware import TokenBudgetMiddleware
    from src.lachesis.verifiers.local_repair import LocalRepairMiddleware

    pipeline = MiddlewarePipeline()
    pipeline.add_before(AntiLoopCircuitBreaker(max_loop_count=3, cooldown_seconds=30.0))
    pipeline.add_before(TokenBudgetMiddleware())
    pipeline.add_around(ContextCacheMiddleware())
    pipeline.add_after(LocalRepairMiddleware())
    pipeline.set_gateway(GatewayArchitrave())
    return pipeline


if __name__ == "__main__":
    pipeline = create_default_pipeline()
    server = SovereignMiddlewareServer(pipeline, host="0.0.0.0", port=32556)  # noqa: S104
    server.start_sync()
