import asyncio
import atexit
import concurrent.futures
import contextlib
import os
import subprocess
import sys
import threading
import time
from enum import Enum
from typing import Any

from mcp import StdioServerParameters

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class _ConnState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class MCPSession:
    def __init__(
        self,
        name: str,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        timeout: int = 5,
        enabled: bool = True,
    ) -> None:
        self.name = name
        self.command = command
        self.args = args
        self.env = env
        self.timeout = timeout
        self.enabled = enabled

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: Any = None
        self._running = False
        self._healthy = False
        self._conn_state = _ConnState.DISCONNECTED
        self._runner_task: asyncio.Task[object] | None = None
        self._lock = threading.Lock()
        self._reconnect_lock = threading.Lock()

        self._patch_create_windows_process()

        self._tools_cache: list[Any] = []
        self._tools_cache_time = 0.0
        self._tools_cache_ttl = 300.0

        atexit.register(self.shutdown)

    def _patch_create_windows_process(self) -> None:
        if sys.platform != "win32":
            return
        try:
            from pathlib import Path
            from typing import TextIO

            from mcp.os.win32 import utilities as win32_utils

            async def _patched(
                command: str,
                args: list[str],
                env: dict[str, str] | None = None,
                errlog: TextIO | None = None,
                cwd: Path | str | None = None,
            ) -> Any:
                # Force CREATE_NO_WINDOW and FallbackProcess to prevent any visible console windows
                from mcp.os.win32.utilities import (
                    _create_job_object,
                    _create_windows_fallback_process,
                    _maybe_assign_process_to_job,
                )

                job = _create_job_object()
                process = await _create_windows_fallback_process(
                    command, args, env, errlog or subprocess.DEVNULL, cwd
                )
                _maybe_assign_process_to_job(process, job)
                job_attached = hasattr(process, "_job_object")
                logger.info(
                    f"MCPSession: spawned slm pid={process.pid} job_attached={job_attached}"
                )
                return process

            win32_utils.create_windows_process = _patched
        except Exception as e:
            logger.debug(f"MCPSession: win32 process patch skipped ({e})")

    def _ensure_thread_running(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            if os.name == "nt":
                self._loop = asyncio.ProactorEventLoop()
            else:
                self._loop = asyncio.new_event_loop()

            def exception_handler(
                _loop: asyncio.AbstractEventLoop, context: dict[str, Any]
            ) -> None:
                msg = context.get("message")
                logger.error(f"MCPSession ({self.name}): Loop exception: {msg}")
                self._healthy = False

            if self._loop is None:
                raise RuntimeError("Failed to create new event loop")
            self._loop.set_exception_handler(exception_handler)
            self._running = True
            self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._thread.start()
            logger.info(f"MCPSession ({self.name}): Lazy-started background thread event loop.")

    def _run_event_loop(self) -> None:
        if self._loop is not None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

    def _cancel_runner(self) -> None:
        task = self._runner_task
        self._runner_task = None
        if task is not None and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._cancel_runner_async(task), self._loop)

    async def _cancel_runner_async(self, task: asyncio.Task[object]) -> None:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, TimeoutError):
                await asyncio.wait_for(task, timeout=5.0)

    def _wait_for_connect(self) -> bool:
        start = time.time()
        while time.time() - start < float(self.timeout):
            if not self._running:
                return False
            with self._lock:
                if self._conn_state == _ConnState.CONNECTED and self._session is not None:
                    return True
                if self._conn_state != _ConnState.CONNECTING:
                    return False
            time.sleep(0.05)
        return False

    def shutdown(self) -> None:
        self._running = False
        acquired = self._lock.acquire(timeout=3.0)
        try:
            if acquired:
                self._healthy = False
                self._conn_state = _ConnState.DISCONNECTED
            self._cancel_runner()
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._shutdown_async(), self._loop)
        finally:
            if acquired:
                self._lock.release()

        if self._thread:
            self._thread.join(timeout=5.0)

    async def _shutdown_async(self) -> None:
        if self._loop is None:
            return
        current_task = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks(self._loop) if t is not current_task]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=5.0, return_when=asyncio.ALL_COMPLETED)
        self._loop.stop()

    def _wait_for_future(self, future: concurrent.futures.Future[object], timeout: float) -> object:
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as err:
            raise TimeoutError(f"MCPSession ({self.name}): Future timed out ({timeout}s)") from err

    def _ensure_connected(self) -> bool:
        if not self.enabled:
            return False
        self._ensure_thread_running()
        if not self._running:
            return False
        with self._reconnect_lock:
            with self._lock:
                if self._conn_state == _ConnState.CONNECTED and self._session is not None:
                    return True
                if self._conn_state == _ConnState.CONNECTING:
                    logger.debug(f"MCPSession ({self.name}): Already connecting, waiting...")
                    return self._wait_for_connect()
            if self._loop is None:
                return False
            future = asyncio.run_coroutine_threadsafe(self._connect_async(), self._loop)
            try:
                return self._wait_for_future(future, float(self.timeout))
            except Exception as e:
                logger.error(f"MCPSession ({self.name}): Failed to connect: {e}")
                with self._lock:
                    self._healthy = False
                    self._conn_state = _ConnState.DISCONNECTED
                return False

    async def _connect_async(self) -> bool:
        with self._lock:
            if self._conn_state == _ConnState.CONNECTED and self._session is not None:
                return True
            if self._conn_state == _ConnState.CONNECTING:
                return False
            self._conn_state = _ConnState.CONNECTING

        self._cancel_runner()

        try:
            merged_env = os.environ.copy()
            merged_env["PYTHONUNBUFFERED"] = "1"
            merged_env["PYTHONIOENCODING"] = "UTF-8"
            if self.env:
                merged_env.update(self.env)

            server_params = StdioServerParameters(
                command=self.command, args=self.args, env=merged_env
            )

            if self._loop is not None:
                self._runner_task = self._loop.create_task(self._session_runner(server_params))

            start_time = time.time()
            while time.time() - start_time < float(self.timeout):
                if not self._running:
                    return False
                with self._lock:
                    if self._conn_state == _ConnState.CONNECTED and self._session is not None:
                        return True
                    if self._conn_state != _ConnState.CONNECTING:
                        return False
                await asyncio.sleep(0.1)

            return False
        except Exception as e:
            logger.error(f"MCPSession ({self.name}): Error inside connect_async: {e}")
            with self._lock:
                self._healthy = False
                self._conn_state = _ConnState.DISCONNECTED
            return False

    async def _session_runner(self, server_params: StdioServerParameters) -> None:
        try:
            from mcp import ClientSession
            from mcp.client.stdio import stdio_client
        except Exception as e:
            logger.error(f"MCPSession ({self.name}): Failed to import MCP modules: {e}")
            with self._lock:
                self._session = None
                self._healthy = False
                self._conn_state = _ConnState.DISCONNECTED
            raise

        retries = 0
        while self._running and self.enabled:
            try:
                async with (
                    stdio_client(server_params) as (read, write),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    with self._lock:
                        self._session = session
                        self._healthy = True
                        self._conn_state = _ConnState.CONNECTED
                        self._tools_cache = []
                        self._tools_cache_time = 0.0
                    logger.info(
                        f"MCPSession ({self.name}): MCP Stdio Session initialized successfully."
                    )
                    retries = 0

                    while self._running and self._healthy and self.enabled:  # noqa: ASYNC110
                        await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info(f"MCPSession ({self.name}): Session runner task cancelled.")
                with self._lock:
                    self._session = None
                    self._healthy = False
                    self._conn_state = _ConnState.DISCONNECTED
                raise
            except OSError as e:
                logger.error(f"MCPSession ({self.name}): OSError in session runner: {e}")
                with self._lock:
                    self._session = None
                    self._healthy = False
                    self._conn_state = _ConnState.DISCONNECTED
                    self.enabled = False
                break
            except Exception as e:
                logger.warning(
                    f"MCPSession ({self.name}): Stdio session crash or connection failure: {e}"
                )
                with self._lock:
                    self._session = None
                    self._healthy = False
                    self._conn_state = _ConnState.DISCONNECTED

                if not self._running or not self.enabled:
                    break

                retries += 1
                if retries >= 3:
                    logger.warning(
                        f"MCPSession ({self.name}): Reached 3 connection failures. Cooldown for 15s..."
                    )
                    try:
                        await asyncio.sleep(15)
                    except asyncio.CancelledError:
                        raise
                    retries = 0
                else:
                    try:
                        await asyncio.sleep(2)
                    except asyncio.CancelledError:
                        raise

    def call_tool_sync(self, name: str, args: dict[str, object]) -> object:
        if not self.enabled or not self._running:
            raise RuntimeError(f"MCPSession ({self.name}) is disabled or shutting down")
        if not self._ensure_connected():
            raise RuntimeError(f"MCPSession ({self.name}) is not connected")

        if self._session is None:
            raise RuntimeError(f"MCPSession ({self.name}) session is None")
        if self._loop is None:
            raise RuntimeError(f"MCPSession ({self.name}) event loop is None")
        coro = self._session.call_tool(name, arguments=args)
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            result = self._wait_for_future(future, float(self.timeout))
            return self._parse_mcp_result(result)
        except Exception as e:
            logger.error(f"MCPSession ({self.name}): Sync tool call '{name}' failed: {e}")
            raise

    async def call_tool_async(self, name: str, args: dict[str, object]) -> object:
        if not self.enabled or not self._running:
            raise RuntimeError(f"MCPSession ({self.name}) is disabled or shutting down")
        if not self._ensure_connected():
            raise RuntimeError(f"MCPSession ({self.name}) is not connected")

        if self._session is None:
            raise RuntimeError(f"MCPSession ({self.name}) session is None")
        if self._loop is None:
            raise RuntimeError(f"MCPSession ({self.name}) event loop is None")
        coro = self._session.call_tool(name, arguments=args)
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            result = await asyncio.wrap_future(future)
            return self._parse_mcp_result(result)
        except Exception as e:
            logger.error(f"MCPSession ({self.name}): Async tool call '{name}' failed: {e}")
            raise

    def list_tools_sync(self) -> list[object]:
        if not self.enabled:
            return []
        with self._lock:
            if self._tools_cache and (time.time() - self._tools_cache_time) < self._tools_cache_ttl:
                return self._tools_cache

        if not self._ensure_connected():
            return []
        if self._session is None or self._loop is None:
            return []
        coro = self._session.list_tools()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            result = self._wait_for_future(future, float(self.timeout))
            tools = []
            if hasattr(result, "tools"):
                tools = result.tools
            elif isinstance(result, list):
                tools = result

            with self._lock:
                self._tools_cache = tools
                self._tools_cache_time = time.time()
            return tools
        except Exception as e:
            logger.error(f"MCPSession ({self.name}): Sync list_tools failed: {e}")
            return []

    def _parse_mcp_result(self, result: object) -> object:
        if hasattr(result, "content") and result.content:
            text_val = result.content[0].text
            try:
                import json

                return json.loads(text_val)
            except Exception:
                return text_val
        return result

    @property
    def healthy(self) -> bool:
        if not self.enabled:
            return False
        with self._lock:
            return self._healthy
