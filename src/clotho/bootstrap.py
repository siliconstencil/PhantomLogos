"""
Clotho Bootstrap (System Startup) - Thin CLI Entry Point.
All logic lives in ananke.py (Morpheus daemon) and hermes_mcp.py (SLM daemon).
"""

import sys
import time

from src.clotho.ananke import (
    _STARTUP_REGISTRY,
    _handle_oom,
    _register_for_shutdown,
    _shutdown_all,
    get_cpu_executor,
    get_loader,
    get_scheduler,
    get_sweeper,
    init_system,
    pre_model_load,
    quick_vram_check,
    register_a2a_bridge,
    start_a2a_server,
    start_morpheus,
    start_shield,
    start_telemetry,
    stop_a2a_server,
    stop_morpheus,
)
from src.clotho.hermes_mcp import (
    discover_slm_port,
    start_slm,
    start_slm_server,
)

_is_our_slm = discover_slm_port  # lazy, callable: result = _is_our_slm(host, port)

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

logger = setup_logger(__name__)

__all__ = [
    "_STARTUP_REGISTRY",
    "_handle_oom",
    "_is_our_slm",
    "_register_for_shutdown",
    "_shutdown_all",
    "get_cpu_executor",
    "get_loader",
    "get_scheduler",
    "get_sweeper",
    "init_system",
    "pre_model_load",
    "quick_vram_check",
    "register_a2a_bridge",
    "start_a2a_server",
    "start_morpheus",
    "start_shield",
    "start_slm",
    "start_slm_server",
    "start_telemetry",
    "stop_a2a_server",
    "stop_morpheus",
]

if __name__ == "__main__":
    project_root = str(get_project_root())

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        logger.info("=== Clotho Bootstrap: Starting Morpheus Daemon ===")
        from cognition.mnemosyne.temporal_store import initialize_temporal_schema

        initialize_temporal_schema()

        start_slm_server()
        start_morpheus()
        start_telemetry(interval_s=30.0)
        start_shield(project_root)
        start_slm()
        logger.info("Daemon started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            stop_morpheus()
            logger.info("Daemon stopped cleanly.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--shield":
        logger.warning(
            "=== --shield is DEPRECATED. Use --daemon (includes Shield). Delegating... ==="
        )
        from cognition.mnemosyne.temporal_store import initialize_temporal_schema

        initialize_temporal_schema()

        start_slm_server()
        start_morpheus()
        start_telemetry(interval_s=30.0)
        start_shield(project_root)
        start_slm()
        logger.info("Fully consolidated daemon running (via --shield compat).")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            stop_morpheus()
            logger.info("Daemon stopped.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        info = quick_vram_check()
        logger.info(f"VRAM check: {info}")
    else:
        logger.info("Usage: python bootstrap.py --daemon | --shield | --check")
