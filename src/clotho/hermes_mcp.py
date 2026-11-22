"""Bootstrap helpers for the optional SuperLocalMemory daemon.

SuperLocalMemory (SLM) is reached over its own HTTP daemon on port 8765.
The daemon must run as a separate OS process: starting it inside the host
process fails on Linux with "cannot schedule new futures after shutdown".
"""

import http.client
import json
import os
import socket
import subprocess
import time
from pathlib import Path

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

SLM_HOST = "127.0.0.1"
SLM_PORT = 8765
# The daemon needs a moment to bind the port after the launch.
SLM_START_ATTEMPTS = 10
SLM_START_POLL_SECONDS = 1.0


def discover_slm_port(host: str = SLM_HOST, port: int = SLM_PORT) -> str:
    """Classify what listens on the SLM port.

    Returns "ours" for a healthy SuperLocalMemory daemon, "foreign" for any
    other listener and "none" when the port is free.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(2.0)
        if sock.connect_ex((host, port)) != 0:
            return "none"

        conn = http.client.HTTPConnection(host, port, timeout=2.0)
        try:
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status != 200:
                return "foreign"
            data = json.loads(resp.read().decode() or "{}")
            if data.get("status") == "ok":
                return "ours"
            return "foreign"
        except Exception:
            return "foreign"
        finally:
            conn.close()
    except Exception:
        return "none"
    finally:
        sock.close()


def start_slm_server() -> None:
    """Start the SuperLocalMemory daemon as a separate process.

    The daemon is only started when SLM_BIN points at its executable. Without
    it the system keeps running on the LanceDB + Ollama fallback.
    """
    slm_status = discover_slm_port()
    if slm_status == "ours":
        logger.info("Bootstrap: SLM daemon already running on port 8765. Reusing.")
        return
    if slm_status == "foreign":
        logger.warning("Bootstrap: Port 8765 is occupied by another service. Skipping SLM start.")
        return

    slm_bin = os.getenv("SLM_BIN")
    if not slm_bin:
        logger.info(
            "Bootstrap: SLM daemon not running and SLM_BIN is not set. "
            "Start it manually (for example: .venv-slm/bin/slm serve start) or continue "
            "with the LanceDB + Ollama fallback."
        )
        return

    log_dir = Path("logs") / "system" / "slm"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "slm_daemon.log"

    logger.info(f"Bootstrap: Starting the SLM daemon from {slm_bin} ...")
    with open(log_file, "a", encoding="utf-8") as handle:
        subprocess.Popen(  # noqa: S603
            [slm_bin, "serve", "start"],
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    logger.info(f"Bootstrap: SLM daemon process launched (logs: {log_file}).")

    # The daemon needs a moment to bind the port. Without this wait the health
    # probe that follows races the launch and reports a false negative.
    for _attempt in range(SLM_START_ATTEMPTS):
        if discover_slm_port() == "ours":
            logger.info("Bootstrap: SLM daemon is answering on port 8765.")
            return
        time.sleep(SLM_START_POLL_SECONDS)
    logger.warning(
        "Bootstrap: SLM daemon did not answer on port 8765 within the start window. "
        "The system continues with the LanceDB + Ollama fallback."
    )


def start_slm() -> None:
    """Initialise the HTTP SLM client when SLM is enabled and the daemon answers."""
    try:
        from src.architrave.mcp import get_slm_client, is_slm_enabled

        if not is_slm_enabled():
            logger.info("Bootstrap: SLM disabled via SLM_ENABLED env var.")
            return

        slm = get_slm_client()
        if not slm.health():
            logger.warning(
                "Bootstrap: SLM is enabled but the daemon does not answer on port 8765. "
                "The system continues with the LanceDB + Ollama fallback."
            )
            return

        project_path = str(Path(__file__).resolve().parents[2])
        slm.session_init(project_path=project_path)
        logger.info("Bootstrap: SLM HTTP session initialised.")
    except Exception as e:
        logger.warning(f"Bootstrap: SLM initialisation skipped ({e})")
