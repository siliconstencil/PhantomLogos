import os
import threading
import time as time_module

from src.architrave.mcp import get_slm_client
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def discover_slm_port(host: str = "127.0.0.1", port: int = 8765) -> str:
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(2.0)
        if sock.connect_ex((host, port)) != 0:
            return "none"
        import http.client

        conn = http.client.HTTPConnection(host, port, timeout=2.0)
        try:
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status == 200:
                data = resp.read().decode()
                if '"agent":"phantom-logos"' in data or "phantom-logos" in data:
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
    try:
        slm_status = discover_slm_port()
        if slm_status == "ours":
            logger.info("Bootstrap: SLM daemon already running (our process). Reusing.")
            return
        if slm_status == "foreign":
            logger.warning("Bootstrap: Port 8765 occupied by foreign process. Skipping SLM start.")
            return

        import logging
        from logging.handlers import RotatingFileHandler

        log_dir = "logs/system/slm"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "slm_daemon.log")

        slm_logger = logging.getLogger("superlocalmemory")
        f_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        f_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        f_handler.setFormatter(f_formatter)
        f_handler.setLevel(logging.INFO)

        slm_logger.addHandler(f_handler)
        slm_logger.setLevel(logging.INFO)

        logger.info(
            "Bootstrap: Starting SLM Unified Daemon Server programmatically in background thread..."
        )

        def run_slm() -> None:
            try:
                from superlocalmemory.server.unified_daemon import start_server

                start_server(port=8765)
            except Exception as e:
                logger.error(f"Bootstrap: SLM Daemon server thread crashed: {e}")

        slm_thread = threading.Thread(target=run_slm, name="SLMServerThread", daemon=True)
        slm_thread.start()
        logger.info(
            "Bootstrap: SLM Unified Daemon Server thread launched successfully (logs routed to logs/system/slm/slm_daemon.log)."
        )

        time_module.sleep(2.0)
    except Exception as e:
        logger.warning(f"Bootstrap: Failed to start SLM Daemon Server ({e})")


def start_slm() -> None:
    try:
        if os.getenv("SLM_ENABLED", "true").lower() == "true":
            from src.architrave.mcp.mcp_registry import get_mcp_registry

            registry = get_mcp_registry()
            session = registry.get_session("slm")
            if session and session.enabled:
                logger.info("Bootstrap: SLM MCP session initialized (enabled=True). Connecting...")
                for attempt in range(3):
                    connected = session._ensure_connected()
                    if connected:
                        logger.info("Bootstrap: SLM MCP session connected successfully.")
                        try:
                            slm = get_slm_client()
                            _proj = str(__import__("pathlib").Path(__file__).resolve().parents[2])
                            slm.session_init(project_path=_proj)
                            logger.info("Bootstrap: SLM MCP session_init completed.")
                        except Exception as e:
                            logger.warning(f"Bootstrap: SLM session_init failed ({e})")
                        break
                    logger.warning(f"Bootstrap: SLM MCP connection attempt {attempt + 1}/3 failed.")
                    time_module.sleep(2.0)
                else:
                    logger.warning(
                        "Bootstrap: SLM MCP session failed to connect after 3 attempts. "
                        "MCP tools (fetch, playwright, github, kg-mem, sequential-thinking) will be unavailable "
                        "until the first task triggers retry."
                    )
            else:
                logger.info(
                    "Bootstrap: SLM MCP session disabled (SLM_ENABLED=false or config disabled)."
                )
        else:
            logger.info("Bootstrap: SLM disabled via SLM_ENABLED env var.")
    except Exception as e:
        logger.warning(f"Bootstrap: SLM MCP initialization skipped ({e})")
