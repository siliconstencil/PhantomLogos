import contextlib
import json
import os
import threading
import time

from src.utils.logging_config import setup_logger

from .mcp_models import MCPRuntimeConfig
from .mcp_session import MCPSession

logger = setup_logger(__name__)

# SuperLocalMemory is reached over its own HTTP daemon, never as an MCP stdio
# server. Any legacy "slm" entry in a config file is therefore ignored.
RETIRED_SERVERS = frozenset({"slm"})


class MCPRegistry:
    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self._sessions: dict[str, MCPSession] = {}
        self._config = self._load_config()
        self._initialize_sessions()
        self._start_retry_timer()

    @property
    def config(self) -> MCPRuntimeConfig:
        """The runtime configuration the sessions were built from."""
        return self._config

    def _start_retry_timer(self) -> None:
        timer = threading.Thread(target=self._retry_loop, daemon=True, name="MCPRetryTimer")
        timer.start()

    def _retry_loop(self) -> None:
        while True:
            time.sleep(60)
            with contextlib.suppress(Exception):
                self.retry_disabled_sessions()

    def _load_config(self) -> MCPRuntimeConfig:
        from src.utils.config import get_config

        _project_root = str(get_config().project_root)
        paths_to_try = [
            os.path.join(_project_root, "mcp_config.json"),
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
                    retired = RETIRED_SERVERS.intersection(config.mcpServers)
                    if retired:
                        logger.warning(
                            f"MCPRegistry: Ignoring retired MCP servers {sorted(retired)}; "
                            "SuperLocalMemory is reached over HTTP."
                        )
                        for name in retired:
                            del config.mcpServers[name]
                    logger.info(f"MCPRegistry: Loaded config file successfully from: {config_path}")
                    return config
                except Exception as e:
                    logger.warning(
                        f"MCPRegistry: Failed to parse config from {config_path} ({e}), trying next fallback."
                    )
                    continue

        config_path = os.path.join(os.path.dirname(__file__), "mcp_config.json")
        default_config = MCPRuntimeConfig(mcpServers={})
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(default_config.model_dump_json(indent=2))
            logger.info(f"MCPRegistry: Created default config file at: {config_path}")
        except Exception as e:
            logger.error(f"MCPRegistry: Failed to write default config: {e}")
        return default_config

    def _initialize_sessions(self) -> None:
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
