import contextlib
import json
import os
import threading
import time

from src.utils.logging_config import setup_logger

from .mcp_models import MCPRuntimeConfig, MCPServerConfig
from .mcp_session import MCPSession

logger = setup_logger(__name__)


class MCPRegistry:
    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self._sessions: dict[str, MCPSession] = {}
        self._config = self._load_config()
        self._initialize_sessions()
        self._start_retry_timer()

    def _start_retry_timer(self) -> None:
        timer = threading.Thread(target=self._retry_loop, daemon=True, name="MCPRetryTimer")
        timer.start()

    def _retry_loop(self) -> None:
        while True:
            time.sleep(60)
            with contextlib.suppress(Exception):
                self.retry_disabled_sessions()

    def _load_config(self) -> MCPRuntimeConfig:
        paths_to_try = [
            os.path.join("D:\\Hank", "mcp_config.json"),
            os.path.join("C:\\Users\\Hakan\\.gemini\\antigravity", "mcp_config.json"),
            os.path.join(os.path.dirname(__file__), "mcp_config.json"),
        ]

        if self._config_path:
            paths_to_try.insert(0, self._config_path)

        for config_path in paths_to_try:
            if os.path.exists(config_path):
                try:
                    with open(config_path, encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:
                            logger.warning(
                                f"MCPRegistry: Config file at {config_path} is empty, trying next fallback."
                            )
                            continue
                        data = json.loads(content)
                    config = MCPRuntimeConfig.model_validate(data)
                    logger.info(f"MCPRegistry: Loaded config file successfully from: {config_path}")
                    slm_entry = config.mcpServers.get("slm")
                    if slm_entry is not None:
                        slm_cmd_override = os.getenv("SLM_MCP_CMD")
                        if slm_cmd_override:
                            cmd_parts = slm_cmd_override.split()
                            slm_entry.command = cmd_parts[0]
                            slm_entry.args = cmd_parts[1:]
                        if os.getenv("SLM_MCP_TIMEOUT"):
                            slm_entry.timeout = int(os.getenv("SLM_MCP_TIMEOUT"))
                        slm_enabled_override = os.getenv("SLM_ENABLED")
                        if slm_enabled_override:
                            slm_entry.enabled = slm_enabled_override.lower() == "true"
                    return config
                except Exception as e:
                    logger.warning(
                        f"MCPRegistry: Failed to parse config from {config_path} ({e}), trying next fallback."
                    )
                    continue

        config_path = os.path.join(os.path.dirname(__file__), "mcp_config.json")
        slm_cmd = os.getenv("SLM_MCP_CMD", "slm mcp")
        cmd_parts = slm_cmd.split() if slm_cmd else ["slm", "mcp"]
        slm_enabled_env = os.getenv("SLM_ENABLED", "true")
        slm_enabled = slm_enabled_env.lower() == "true" if slm_enabled_env else True

        default_config = MCPRuntimeConfig(
            mcpServers={
                "slm": MCPServerConfig(
                    command=cmd_parts[0],
                    args=cmd_parts[1:],
                    env={},
                    timeout=int(os.getenv("SLM_MCP_TIMEOUT", "30")),
                    enabled=slm_enabled,
                )
            }
        )
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(default_config.model_dump_json(indent=2))
            logger.info(f"MCPRegistry: Created default config file at: {config_path}")
        except Exception as e:
            logger.error(f"MCPRegistry: Failed to write default config: {e}")
        return default_config

    def _kill_orphaned_slm(self) -> None:
        """Kill orphaned slm.exe processes before spawning a new one.

        An slm.exe is an orphan if and only if its parent PID no longer exists,
        or the process at that PID was born after the SLM (Windows PID reuse).

        Deliberately does NOT filter by parent process name: multiple IDEs, CLIs,
        and agents (Python, Node, Electron, etc.) may each own a healthy slm.exe
        simultaneously. Any live parent - regardless of type - means the SLM is
        not an orphan and must be left alone.
        """
        import sys

        if sys.platform != "win32":
            return
        try:
            import psutil  # type: ignore
        except ImportError:
            logger.debug("MCPRegistry: psutil unavailable, orphan SLM cleanup skipped")
            return

        killed = 0
        try:
            for proc in psutil.process_iter(["pid", "name", "ppid", "create_time"]):
                try:
                    if (proc.info["name"] or "").lower() != "slm.exe":
                        continue
                    ppid = proc.info["ppid"]
                    slm_create_time = proc.info["create_time"] or 0.0

                    is_orphan = False
                    if ppid is None or not psutil.pid_exists(ppid):
                        # Parent PID is gone - true orphan
                        is_orphan = True
                    else:
                        try:
                            parent_create_time = psutil.Process(ppid).create_time()
                            if parent_create_time > slm_create_time:
                                # A new process reused the parent PID after the real
                                # parent died - treat as orphan
                                is_orphan = True
                        except psutil.NoSuchProcess:
                            is_orphan = True

                    if is_orphan:
                        try:
                            proc.kill()
                            killed += 1
                            logger.info(
                                f"MCPRegistry: Killed orphaned SLM pid={proc.pid} "
                                f"(parent pid={ppid} is dead)"
                            )
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as _e:
                            logger.debug(
                                f"MCPRegistry: Could not kill orphaned SLM pid={proc.pid} ({_e})"
                            )
                except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
                    continue

            if killed:
                time.sleep(0.5)
                logger.info(
                    f"MCPRegistry: Cleaned up {killed} orphaned SLM process(es) before init."
                )
        except Exception as e:
            logger.debug(f"MCPRegistry: Orphan SLM cleanup skipped ({e})")

    def _initialize_sessions(self) -> None:
        self._kill_orphaned_slm()
        for srv_name, server in self._config.mcpServers.items():
            session = MCPSession(
                name=srv_name,
                command=server.command,
                args=server.args,
                env=server.env or None,
                timeout=server.timeout,
                enabled=server.enabled,
            )
            self._sessions[srv_name] = session
            logger.info(
                f"MCPRegistry: Initialized session for server '{srv_name}' (enabled={server.enabled})."
            )

    def retry_disabled_sessions(self) -> None:
        import os
        import shutil
        import threading

        for srv_name, session in self._sessions.items():
            if not session.enabled:
                exec_exists = shutil.which(session.command) is not None or os.path.exists(
                    session.command
                )
                if exec_exists:
                    logger.info(
                        f"MCPRegistry: Found executable for disabled session '{srv_name}'. Attempting non-blocking re-enable..."
                    )
                    session.enabled = True
                    threading.Thread(target=session._ensure_connected, daemon=True).start()

    def get_session(self, name: str) -> MCPSession | None:
        return self._sessions.get(name)

    def get_all_sessions(self) -> dict[str, MCPSession]:
        return self._sessions

    def shutdown(self) -> None:
        for name, session in self._sessions.items():
            try:
                session.shutdown()
            except Exception as e:
                logger.error(f"MCPRegistry: Failed to shutdown session '{name}': {e}")


_registry_instance = None


def get_mcp_registry() -> MCPRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = MCPRegistry()
    return _registry_instance
