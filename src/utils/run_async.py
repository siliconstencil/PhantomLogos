import asyncio
import contextlib
import threading
from collections.abc import Coroutine
from concurrent.futures import TimeoutError
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class _DedicatedLoop:
    _thread: threading.Thread | None = None
    _loop: asyncio.AbstractEventLoop | None = None
    _lock = threading.Lock()
    _started = False

    @classmethod
    def ensure(cls) -> asyncio.AbstractEventLoop:
        with cls._lock:
            if cls._started:
                return cls._loop
            cls._loop = asyncio.new_event_loop()
            cls._loop.set_exception_handler(cls._handle_loop_exception)
            cls._thread = threading.Thread(
                target=cls._run_forever,
                name="dedicated-asyncio-loop",
                daemon=True,
            )
            cls._thread.start()
            cls._started = True
            logger.debug("DedicatedLoop: Background asyncio thread started.")
            return cls._loop

    @classmethod
    def _run_forever(cls) -> None:
        loop = cls._loop
        if loop is None:
            return
        asyncio.set_event_loop(loop)
        loop.run_forever()

    @classmethod
    def _handle_loop_exception(cls, _loop: Any, context: dict[str, Any]) -> None:
        exc = context.get("exception")
        msg = context.get("message", "Unknown")
        logger.error(f"DedicatedLoop: Unhandled exception in loop ({msg})", exc_info=exc)

    @classmethod
    def shutdown(cls, timeout: float = 3.0) -> None:
        with cls._lock:
            if not cls._started:
                return
            loop = cls._loop
            cls._started = False
            if loop and loop.is_running():
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.call_soon_threadsafe(loop.stop)
            if cls._thread and cls._thread.is_alive():
                cls._thread.join(timeout=timeout)
            if loop:
                with contextlib.suppress(Exception):
                    loop.run_until_complete(loop.shutdown_asyncgens())
                with contextlib.suppress(Exception):
                    loop.close()
            cls._loop = None
            cls._thread = None
            logger.debug("DedicatedLoop: Shutdown complete.")


def run_async(coro: Coroutine[Any, Any, Any], timeout: float | None = None) -> Any:
    loop = _DedicatedLoop.ensure()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return future.result(timeout=timeout)
    except TimeoutError:
        logger.warning(
            f"run_async: Timeout ({timeout}s) for coroutine {coro.__name__ if hasattr(coro, '__name__') else type(coro).__name__}"
        )
        raise
