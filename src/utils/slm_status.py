"""Status probe for the optional SuperLocalMemory daemon.

SuperLocalMemory (SLM) is an optional full-memory mode. When the daemon is
absent the system falls back to LanceDB + Ollama, so an absent daemon is
reported as INFO and never as a broken axis.
"""

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def check_slm() -> tuple[str, str]:
    """Report the optional SuperLocalMemory daemon.

    Returns a (status, detail) pair where status is one of OK, INFO, BROKEN.
    A missing or disabled daemon is INFO: the core keeps working without it.
    """
    try:
        from src.architrave.mcp import is_slm_enabled
        from src.architrave.mcp.slm_client import SLMClient, SLMConfig, reset_heartbeat

        if not is_slm_enabled():
            return "INFO", "SLM disabled (LanceDB + Ollama fallback in use)"

        config = SLMConfig.from_env()
        reset_heartbeat()
        if SLMClient(config).health():
            return "OK", f"SLM daemon reachable on port {config.http_port}"
        return "INFO", f"SLM enabled but the daemon does not answer on port {config.http_port}"
    except Exception as exc:
        return "INFO", f"SLM not available ({exc})"
