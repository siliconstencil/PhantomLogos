"""
Clotho Bootstrap (System Startup).
Initializes Morpheus VRAM daemon and system health monitoring.
Run once at application start to activate background VRAM management.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

load_dotenv()

logger = setup_logger(__name__)

_scheduler = None
_sweeper = None
_loader_instance = None
_telemetry_running = False
_telemetry_thread = None
_init_lock = threading.Lock()
_morpheus_lock = threading.Lock()
_shield_lock = threading.Lock()
_pool_lock = threading.Lock()
_cpu_pool = None
_shield_running = False


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        from cognition.morpheus.scheduler import MorpheusScheduler

        _scheduler = MorpheusScheduler(idle_cooldown_s=120.0)
        logger.info("Bootstrap: MorpheusScheduler initialized.")
    return _scheduler


def get_sweeper():
    global _sweeper
    if _sweeper is None:
        from cognition.morpheus.sweeper import VRAMSweeper

        # Phase 11.18.3: 7GB total limit -> 6.0GB swap threshold for safety
        _sweeper = VRAMSweeper(swap_threshold_gb=6.0, frag_threshold=0.3)
    return _sweeper


def init_system():
    """Initializes system security, environment (S1.2), and configuration (K1.5.4)."""
    with _init_lock:
        from src.utils.security_utils import load_secrets_to_env

        load_secrets_to_env()

        # Phase 1.0.18: Professional Diagnostic Injection
        try:
            from src.utils.system_check import SystemCheck

            project_root = str(get_project_root())
            diagnostic = SystemCheck(project_root)
            result = diagnostic.run()

            if result.warnings:
                logger.warning("Bootstrap: SystemCheck detected environment issues:")
                for warning in result.warnings:
                    logger.warning(f"  [CHECK] {warning}")

            if result.passed:
                logger.info("Bootstrap: All system integrity checks passed.")
            else:
                logger.info(
                    f"Bootstrap: SystemCheck completed with {len(result.warnings)} warnings."
                )

        except Exception as e:
            logger.warning(f"Bootstrap: SystemCheck diagnostic suite failed to execute: {e}")

        logger.info("Bootstrap: System environment initialized (Secrets loaded).")


def get_loader():
    global _loader_instance
    if _loader_instance is None:
        from cognition.morpheus.loader import ModelLoader

        _loader_instance = ModelLoader()
    return _loader_instance


def get_cpu_executor():
    """
    Returns a singleton ThreadPoolExecutor for CPU-heavy tasks.
    Phase 11.18.5: max_workers=4 to prevent CPU saturation on i7-13620H.
    """
    global _cpu_pool
    if _cpu_pool is None:
        with _pool_lock:
            if _cpu_pool is None:
                _cpu_pool = ThreadPoolExecutor(max_workers=4)
                logger.info("Bootstrap: CPU_HEAVY_EXECUTOR initialized (max_workers=4).")
    return _cpu_pool


def start_morpheus():
    """Start Morpheus daemon: scheduler background thread."""
    with _morpheus_lock:
        scheduler = get_scheduler()
        if not getattr(scheduler, "_running", False):
            scheduler.start()
            logger.info("Bootstrap: MorpheusScheduler daemon started (30s interval).")
            return True
        else:
            logger.info("Bootstrap: MorpheusScheduler already running.")
            return False


def stop_morpheus():
    """Stop Morpheus daemon cleanly."""
    global _scheduler, _sweeper, _loader_instance, _telemetry_thread, _telemetry_running
    with _morpheus_lock:
        if _scheduler and getattr(_scheduler, "_running", False):
            _scheduler.stop()
            logger.info("Bootstrap: MorpheusScheduler stopped.")
        _telemetry_running = False
        _scheduler = None
        _sweeper = None
        _loader_instance = None
        _telemetry_thread = None


def pre_model_load(model_name: str) -> bool:
    """
    Pre-load VRAM check: sweep before loading a new model.
    Phase 11.18.3: Manages auxiliary tools (Nomic/Jina) and enforces Sequential Loading.
    """
    sweeper = get_sweeper()
    loader = get_loader()

    state = sweeper.state
    free_gb = state["free_gb"]
    used_gb = state["used_gb"]
    frag = state["fragmentation"]

    logger.info(
        f"Bootstrap: Pre-load check for '{model_name}' - free={free_gb}GB used={used_gb}GB frag={frag:.2f}"
    )

    # 1. Flush for Heavy Models (Sequential Loading Protocol - Pro Restoration)
    try:
        from src.architrave.model_registry import get_vram_requirement

        vram_req = get_vram_requirement(model_name)
        if vram_req >= 3.0:
            logger.warning(
                f"Bootstrap: Heavy model detected '{model_name}' ({vram_req}GB). Enforcing Sequential Loading Flush."
            )
            loader.flush()
    except Exception as e:
        logger.warning(
            f"Bootstrap: Dynamic heavy model check failed ({e}). Falling back to safety sweep."
        )

    # 2. Auxiliary Tool Management (Nomic/Jina)
    # If used_gb is high, we might need to unload auxiliary tools unless strictly required
    if used_gb >= sweeper.swap_threshold:
        logger.warning(
            f"Bootstrap: VRAM pressure detected ({used_gb}GB). Checking auxiliary tools."
        )
        # Currently, Jina and Nomic are managed via Ollama or Muscle.
        # loader.flush() already unloads these if they are in Ollama.
        sweeper.check_and_sweep(loader)

    return True


def start_telemetry(interval_s: float = 30.0):
    """Start nvidia-smi telemetry in background thread."""
    global _telemetry_running, _telemetry_thread
    if _telemetry_running:
        return

    _telemetry_running = True

    def telemetry_loop():
        from cognition.mnemosyne.temporal_store import TemporalStore
        from cognition.morpheus.monitor import get_gpu_memory_info

        ts = TemporalStore()
        while _telemetry_running:
            try:
                info = get_gpu_memory_info()
                ts.record(
                    session_id="bootstrap",
                    event_type="telemetry.tick",
                    model_name="morpheus",
                    vram_gb=info.get("used_gb", 0),
                    extra={
                        "free_gb": info.get("free_gb", 0),
                        "util_pct": info.get("utilization_pct", 0),
                    },
                )
            except Exception as e:
                logger.error(f"Bootstrap: Telemetry tick failed ({e})", exc_info=True)
            try:
                time.sleep(interval_s)
            except KeyboardInterrupt:
                break

    _telemetry_thread = threading.Thread(target=telemetry_loop, daemon=True)
    _telemetry_thread.start()
    logger.info(f"Bootstrap: VRAM telemetry started ({interval_s}s interval).")


def quick_vram_check() -> dict:
    """One-shot VRAM health check. Uses Morpheus cache if available, else live nvidia-smi."""
    try:
        from cognition.morpheus.monitor import (
            get_cached_gpu_info,
            get_fragmentation_estimate,
            get_gpu_memory_info,
        )

        cached = get_cached_gpu_info(max_age=35.0)
        if cached:
            info = dict(cached)
        else:
            info = get_gpu_memory_info()
        info["fragmentation"] = get_fragmentation_estimate()
        info["morpheus_status"] = (
            "active" if (_scheduler and getattr(_scheduler, "_running", False)) else "idle"
        )
        return info
    except Exception as e:
        return {"error": str(e)}


def start_shield(project_root: str):
    """
    Starts the Sovereign Shield (Integrity Guardian).
    Phase 11.19.10: Single Guardian thread + Initial baseline scan.
    """
    global _shield_running
    with _shield_lock:
        if _shield_running:
            logger.info("Bootstrap: Sovereign Shield already running.")
            return False

        from src.lachesis.file_watchdog import PollingGuardian
        from src.lachesis.snapshot_manager import SnapshotManager

        logger.info("Bootstrap: Initializing Sovereign Shield...")

        # 1. Baseline Scan (Synchronous)
        try:
            manager = SnapshotManager(project_root)
            logger.info("Bootstrap: Performing initial baseline snapshot scan...")
            manager.scan_all()
            logger.info("Bootstrap: Baseline snapshot complete.")
        except Exception as e:
            logger.error(f"Bootstrap: Baseline scan failed ({e})", exc_info=True)
            # We still proceed to start the watchdog

        # 2. Start Guardian (Single Thread)
        def guardian_loop():
            global _shield_running
            try:
                guardian = PollingGuardian(project_root)
                guardian.run()
            except Exception as e:
                logger.critical(f"Bootstrap: Sovereign Shield crashed ({e})", exc_info=True)
                _shield_running = False

        _shield_running = True
        t = threading.Thread(target=guardian_loop, name="SovereignGuardian", daemon=True)
        t.start()
        logger.info("Bootstrap: Polling Integrity Guardian started.")
        return True


def _handle_oom(model_name: str):
    """[Phase 11.18.15] Emergency OOM recovery: flush and load ultra-light model."""
    logger.critical(f"Bootstrap: Emergency OOM Recovery triggered for {model_name}")
    loader = get_loader()
    loader.flush()
    time.sleep(2)

    # Try to load ultra-light model as a fallback to keep the system responsive
    recovery_model = "deepscaler-1-5b-preview-q4_k_m:latest"
    logger.info(f"Bootstrap: Attempting to load recovery model {recovery_model}")
    if loader.load(recovery_model):
        logger.info("Bootstrap: Recovery model loaded successfully.")
    else:
        logger.error("Bootstrap: Recovery model load failed. System in degraded state.")


if __name__ == "__main__":
    import sys

    project_root = str(get_project_root())

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        logger.info("=== Clotho Bootstrap: Starting Morpheus Daemon ===")
        start_morpheus()
        start_telemetry(interval_s=30.0)
        start_shield(project_root)
        logger.info("Daemon started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            stop_morpheus()
            logger.info("Daemon stopped cleanly.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--shield":
        logger.info("=== Clotho Bootstrap: Starting Sovereign Shield ===")
        start_shield(project_root)
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Shield stopped.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        info = quick_vram_check()
        logger.info(f"VRAM check: {info}")
    else:
        logger.info("Usage: python bootstrap.py --daemon | --shield | --check")
