import time
import json
import os
import asyncio
import functools
import inspect
import datetime
from typing import Any, Callable
try:
    from .token_budget import TokenBudgetGuard, get_token_guard
except ImportError:
    from token_budget import TokenBudgetGuard, get_token_guard


class AtroposMonitor:
    """
    Local Observability and Monitoring Layer.
    Logs traces, timing, and status to local JSONL files and TemporalStore.
    """
    def __init__(self):
        self.budget_guard = get_token_guard()
        self._temporal = None

    def _get_temporal(self):
        if self._temporal is None:
            try:
                from cognition.mnemosyne.temporal_store import TemporalStore
                self._temporal = TemporalStore()
            except Exception as e:
                logger.warning(f"AtroposMonitor: TemporalStore init failed ({e})")
        return self._temporal

    def trace(self, component: str):
        def decorator(func: Callable):
            if inspect.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()
                    trace_id = f"tr_{int(time.time() * 1000)}"
                    self._log_event(trace_id, component, func.__name__, "START")
                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time
                        self._log_event(trace_id, component, func.__name__, "SUCCESS", duration=duration, result=result)
                        return result
                    except asyncio.CancelledError:
                        duration = time.perf_counter() - start_time
                        self._log_event(trace_id, component, func.__name__, "CANCELLED", duration=duration)
                        raise
                    except Exception as e:
                        duration = time.perf_counter() - start_time
                        self._log_event(trace_id, component, func.__name__, "FAILURE", duration=duration, error=str(e))
                        raise
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()
                    trace_id = f"tr_{int(time.time() * 1000)}"
                    self._log_event(trace_id, component, func.__name__, "START")
                    try:
                        result = func(*args, **kwargs)
                        duration = time.perf_counter() - start_time
                        self._log_event(trace_id, component, func.__name__, "SUCCESS", duration=duration, result=result)
                        return result
                    except Exception as e:
                        duration = time.perf_counter() - start_time
                        self._log_event(trace_id, component, func.__name__, "FAILURE", duration=duration, error=str(e))
                        raise
                return sync_wrapper
        return decorator

    def _log_event(self, trace_id: str, component: str, action: str, status: str, **kwargs):
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
        temporal = self._get_temporal()
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
                    tokens = 500 # Fallback
            
            allowed = self.budget_guard.consume(tokens)
            if not allowed:
                remaining = self.budget_guard.remaining_daily()
                logger.warning(f"TokenBudget: Exceeded limit. Daily remaining: {remaining}")


if __name__ == "__main__":
    import asyncio
    monitor = AtroposMonitor()

    @monitor.trace("test_component")
    async def sample_async_task():
        time.sleep(0.1)
        return "Async Done"

    @monitor.trace("test_component")
    def sample_sync_task():
        time.sleep(0.05)
        return "Sync Done"

    print("Testing sync trace...")
    sample_sync_task()
    print("Testing async trace...")
    asyncio.run(sample_async_task())
    print("Trace logged to TemporalStore (Axis 4) via Database-First.")
