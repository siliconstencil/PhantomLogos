import asyncio
import functools
import inspect
import os
import time
from collections.abc import Callable
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from .token_budget import get_token_guard
except ImportError:
    from src.atropos.token_budget import get_token_guard

# --- K4.4: OpenTelemetry Integration ---
_otel_tracer = None
_otel_initialized = False


def init_opentelemetry(service_name: str = "phantom-logos") -> Any:
    global _otel_tracer, _otel_initialized
    if _otel_initialized:
        return _otel_tracer
    _otel_initialized = True
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _otel_tracer = trace.get_tracer(service_name)
        logger.info(f"OpenTelemetry: Initialized with OTLP endpoint {otlp_endpoint}")
    except ImportError:
        logger.info("OpenTelemetry: Packages not installed, skipping OTLP export.")
    except Exception as e:
        logger.warning(f"OpenTelemetry: Init failed ({e})")
    return _otel_tracer


def get_otel_tracer() -> Any:
    return _otel_tracer


class AtroposMonitor:
    """
    Local Observability and Monitoring Layer.
    Logs traces, timing, and status to local JSONL files and TemporalStore.
    """

    def __init__(self) -> None:
        self.budget_guard = get_token_guard()
        self._temporal = None
        self._tracer = None
        self._otel_ready = False
        self._init_otel()

    def _init_otel(self) -> None:
        try:
            tracer = init_opentelemetry()
            self._tracer = tracer
            self._otel_ready = tracer is not None
        except Exception as e:
            logger.debug(f"AtroposMonitor: OTel init skipped ({e})")
            self._tracer = None
            self._otel_ready = False

    def get_temporal(self) -> Any:
        if self._temporal is None:
            try:
                from cognition.mnemosyne.temporal_store import TemporalStore

                self._temporal = TemporalStore()
            except Exception as e:
                logger.warning(f"AtroposMonitor: TemporalStore init failed ({e})")
        return self._temporal

    def trace(self, component: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    start_time = time.perf_counter()
                    trace_id = f"tr_{int(time.time() * 1000)}"
                    otel = get_otel_tracer()
                    if otel:
                        with otel.start_as_current_span(f"{component}.{func.__name__}") as span:
                            span.set_attribute("trace_id", trace_id)
                            span.set_attribute("component", component)
                            self._log_event(trace_id, component, func.__name__, "START")
                            try:
                                result = await func(*args, **kwargs)
                                duration = time.perf_counter() - start_time
                                span.set_attribute("duration_ms", duration * 1000)
                                span.set_status(status="OK")
                                self._log_event(
                                    trace_id,
                                    component,
                                    func.__name__,
                                    "SUCCESS",
                                    duration=duration,
                                    result=result,
                                )
                                return result
                            except asyncio.CancelledError:
                                duration = time.perf_counter() - start_time
                                span.set_status(status="UNSET")
                                self._log_event(
                                    trace_id,
                                    component,
                                    func.__name__,
                                    "CANCELLED",
                                    duration=duration,
                                )
                                raise
                            except Exception as e:
                                duration = time.perf_counter() - start_time
                                span.record_exception(e)
                                span.set_status(status="ERROR", description=str(e))
                                self._log_event(
                                    trace_id,
                                    component,
                                    func.__name__,
                                    "FAILURE",
                                    duration=duration,
                                    error=str(e),
                                )
                                raise
                    else:
                        self._log_event(trace_id, component, func.__name__, "START")
                        try:
                            result = await func(*args, **kwargs)
                            duration = time.perf_counter() - start_time
                            self._log_event(
                                trace_id,
                                component,
                                func.__name__,
                                "SUCCESS",
                                duration=duration,
                                result=result,
                            )
                            return result
                        except asyncio.CancelledError:
                            duration = time.perf_counter() - start_time
                            self._log_event(
                                trace_id, component, func.__name__, "CANCELLED", duration=duration
                            )
                            raise
                        except Exception as e:
                            duration = time.perf_counter() - start_time
                            self._log_event(
                                trace_id,
                                component,
                                func.__name__,
                                "FAILURE",
                                duration=duration,
                                error=str(e),
                            )
                            raise

                return async_wrapper
            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    start_time = time.perf_counter()
                    trace_id = f"tr_{int(time.time() * 1000)}"
                    otel = get_otel_tracer()
                    if otel:
                        with otel.start_as_current_span(f"{component}.{func.__name__}") as span:
                            span.set_attribute("trace_id", trace_id)
                            span.set_attribute("component", component)
                            self._log_event(trace_id, component, func.__name__, "START")
                            try:
                                result = func(*args, **kwargs)
                                duration = time.perf_counter() - start_time
                                span.set_attribute("duration_ms", duration * 1000)
                                span.set_status(status="OK")
                                self._log_event(
                                    trace_id,
                                    component,
                                    func.__name__,
                                    "SUCCESS",
                                    duration=duration,
                                    result=result,
                                )
                                return result
                            except Exception as e:
                                duration = time.perf_counter() - start_time
                                span.record_exception(e)
                                span.set_status(status="ERROR", description=str(e))
                                self._log_event(
                                    trace_id,
                                    component,
                                    func.__name__,
                                    "FAILURE",
                                    duration=duration,
                                    error=str(e),
                                )
                                raise
                    else:
                        self._log_event(trace_id, component, func.__name__, "START")
                        try:
                            result = func(*args, **kwargs)
                            duration = time.perf_counter() - start_time
                            self._log_event(
                                trace_id,
                                component,
                                func.__name__,
                                "SUCCESS",
                                duration=duration,
                                result=result,
                            )
                            return result
                        except Exception as e:
                            duration = time.perf_counter() - start_time
                            self._log_event(
                                trace_id,
                                component,
                                func.__name__,
                                "FAILURE",
                                duration=duration,
                                error=str(e),
                            )
                            raise

                return sync_wrapper

        return decorator

    def _log_event(
        self, trace_id: str, component: str, action: str, status: str, **kwargs: Any
    ) -> None:
        # Database-First: No file I/O for traces.
        from src.utils.logging_config import setup_logger

        logger = setup_logger(component)

        event_msg = f"Trace[{trace_id}] {action} -> {status}"
        if "error" in kwargs:
            event_msg += f" (Error: {kwargs['error']})"
        if "duration" in kwargs:
            event_msg += f" [{kwargs['duration']:.4f}s]"

        logger.info(event_msg)

        # Axis 4: Temporal - Record trace as time-series metric
        temporal = self.get_temporal()
        if temporal:
            duration = kwargs.get("duration", 0.0)
            temporal.record(
                session_id="system",
                event_type=f"{component}.{action}",
                model_name=component,
                tokens_used=kwargs.get("tokens", 0),
                latency_ms=duration * 1000 if duration else 0.0,
                extra={"trace_id": trace_id, "status": status},
            )

        if status == "SUCCESS":
            tokens = kwargs.get("tokens")
            if tokens is None:
                # Attempt to count tokens from result if it's a string
                result = kwargs.get("result")
                if isinstance(result, str):
                    try:
                        import tiktoken

                        enc = tiktoken.get_encoding(os.getenv("TOKEN_ENCODING", "cl100k_base"))
                        tokens = len(enc.encode(result))
                    except Exception as e:
                        logger.warning(f"AtroposMonitor: tiktoken failed ({e}), fallback 500")
                        tokens = 500
                else:
                    tokens = 500  # Fallback

            allowed = self.budget_guard.consume(tokens)
            if not allowed:
                remaining = self.budget_guard.remaining_daily()
                logger.warning(f"TokenBudget: Exceeded limit. Daily remaining: {remaining}")


if __name__ == "__main__":
    import asyncio

    monitor = AtroposMonitor()

    @monitor.trace("test_component")
    async def sample_async_task() -> str:
        await asyncio.sleep(0.1)
        return "Async Done"

    @monitor.trace("test_component")
    def sample_sync_task() -> str:
        time.sleep(0.05)
        return "Sync Done"

    print("Testing sync trace...")
    sample_sync_task()
    print("Testing async trace...")
    asyncio.run(sample_async_task())
    print("Trace logged to TemporalStore (Axis 4) via Database-First.")
