import atexit
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
_a2a_server = None
_a2a_lock = threading.Lock()

_STARTUP_REGISTRY = []


def _register_for_shutdown(name: str, cleanup_func) -> None:
    _STARTUP_REGISTRY.append((name, cleanup_func))
    logger.debug(f"Bootstrap: Registered '{name}' for LIFO shutdown.")


def _shutdown_all() -> None:
    logger.info("Bootstrap: Executing LIFO shutdown for all registered services...")
    for name, cleanup_func in reversed(_STARTUP_REGISTRY):
        try:
            cleanup_func()
            logger.info(f"Bootstrap: '{name}' shutdown completed.")
        except Exception as e:
            logger.warning(f"Bootstrap: '{name}' shutdown error ({e})")
    _STARTUP_REGISTRY.clear()
    logger.info("Bootstrap: LIFO shutdown complete.")


atexit.register(_shutdown_all)


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

        _sweeper = VRAMSweeper(swap_threshold_gb=6.0, frag_threshold=0.3)
    return _sweeper


def get_loader():
    global _loader_instance
    if _loader_instance is None:
        import asyncio

        from cognition.morpheus.loader import ModelLoader
        from src.utils.ollama_utils import register_vram_guard_callback

        loader = ModelLoader()
        _loader_instance = loader

        async def guard_callback(model: str) -> bool:
            return await asyncio.to_thread(loader.load, model)

        register_vram_guard_callback(guard_callback)

    return _loader_instance


def get_cpu_executor():
    global _cpu_pool
    if _cpu_pool is None:
        with _pool_lock:
            if _cpu_pool is None:
                _cpu_pool = ThreadPoolExecutor(max_workers=4)
                logger.info("Bootstrap: CPU_HEAVY_EXECUTOR initialized (max_workers=4).")
    return _cpu_pool


def init_system() -> None:
    with _init_lock:
        from src.utils.security_utils import load_secrets_to_env

        load_secrets_to_env()

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


def register_a2a_bridge() -> None:
    try:
        from src.architrave.a2a.discovery import A2ADiscovery
        from src.clotho.agent_loader import AgentDefinition, AgentRegistry

        def bridge_callback(info) -> None:
            registry = AgentRegistry.get_instance()
            agent_data = {
                "id": info.agent_id,
                "name": info.name,
                "version": "1.0.0",
                "description": f"Remote federated agent endpoint: {info.endpoint}",
                "capability": info.capabilities[0] if info.capabilities else None,
                "tools": [],
                "skills": info.skills,
                "memory_axes": [1, 8],
                "model": {"primary": f"remote:{info.endpoint}"},
            }
            agent_def = AgentDefinition(agent_data)
            registry._agents[info.agent_id] = agent_def
            logger.info(
                f"Bootstrap Bridge: Dynamically bound remote '{info.agent_id}' to AgentRegistry."
            )

        A2ADiscovery.register_on_register_callback(bridge_callback)
        logger.info(
            "Bootstrap Bridge: A2A to AgentRegistry callback bridge successfully registered."
        )
    except Exception as e:
        logger.error(f"Bootstrap Bridge: Failed to register A2A to AgentRegistry bridge ({e})")


def start_a2a_server() -> bool:
    global _a2a_server
    with _a2a_lock:
        if _a2a_server is None:
            register_a2a_bridge()

            import os

            from src.architrave.a2a.server import A2AServer

            agent_id = os.getenv("A2A_AGENT_ID", "sophia")
            port = int(os.getenv("A2A_PORT", "32554"))
            _a2a_server = A2AServer(agent_id=agent_id, default_port=port)
            _a2a_server.start()
            logger.info("Bootstrap: A2A Federation Server daemon started.")
            return True
        else:
            logger.info("Bootstrap: A2A Federation Server already running.")
            return False


def stop_a2a_server() -> None:
    global _a2a_server
    with _a2a_lock:
        if _a2a_server is not None:
            try:
                from src.utils.run_async import run_async

                run_async(_a2a_server.stop(), timeout=5.0)
            except Exception as e:
                logger.warning(f"Bootstrap: Failed to cleanly await A2A Server stop ({e})")
            _a2a_server = None
            logger.info("Bootstrap: A2A Federation Server stopped.")


def start_morpheus() -> bool:
    with _morpheus_lock:
        scheduler = get_scheduler()
        if not getattr(scheduler, "_running", False):
            from cognition.mnemosyne.temporal_store import initialize_temporal_schema

            initialize_temporal_schema()

            scheduler.start()
            logger.info("Bootstrap: MorpheusScheduler daemon started (30s interval).")

            _register_for_shutdown("morpheus", stop_morpheus)

            start_a2a_server()
            return True
        else:
            logger.info("Bootstrap: MorpheusScheduler already running.")
            return False


def stop_morpheus() -> None:
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

        stop_a2a_server()


def pre_model_load(model_name: str) -> bool:
    sweeper = get_sweeper()
    loader = get_loader()

    state = sweeper.state
    free_gb = state["free_gb"]
    used_gb = state["used_gb"]
    frag = state["fragmentation"]

    logger.info(
        f"Bootstrap: Pre-load check for '{model_name}' - free={free_gb}GB used={used_gb}GB frag={frag:.2f}"
    )

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

    if used_gb >= sweeper.swap_threshold:
        logger.warning(
            f"Bootstrap: VRAM pressure detected ({used_gb}GB). Checking auxiliary tools."
        )
        sweeper.check_and_sweep(loader)

    return True


def start_telemetry(interval_s: float = 30.0) -> None:
    global _telemetry_running, _telemetry_thread
    if _telemetry_running:
        return

    _telemetry_running = True

    def telemetry_loop() -> None:
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


def start_shield(project_root: str) -> bool:
    global _shield_running
    with _shield_lock:
        if _shield_running:
            logger.info("Bootstrap: Sovereign Shield already running.")
            return False

        from src.lachesis.file_watchdog import PollingGuardian
        from src.lachesis.snapshot_manager import SnapshotManager

        logger.info("Bootstrap: Initializing Sovereign Shield...")

        try:
            manager = SnapshotManager(project_root)
            logger.info("Bootstrap: Performing initial baseline snapshot scan...")
            manager.scan_all()
            logger.info("Bootstrap: Baseline snapshot complete.")
        except Exception as e:
            logger.error(f"Bootstrap: Baseline scan failed ({e})", exc_info=True)

        def guardian_loop() -> None:
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


def quick_vram_check() -> dict:
    try:
        from cognition.morpheus.monitor import (
            get_cached_gpu_info,
            get_fragmentation_estimate,
            get_gpu_memory_info,
        )

        cached = get_cached_gpu_info(max_age=35.0)
        info = dict(cached) if cached else get_gpu_memory_info()
        info["fragmentation"] = get_fragmentation_estimate()
        info["morpheus_status"] = (
            "active" if (_scheduler and getattr(_scheduler, "_running", False)) else "idle"
        )
        return info
    except Exception as e:
        return {"error": str(e)}


def _handle_oom(model_name: str) -> None:
    logger.critical(f"Bootstrap: Emergency OOM Recovery triggered for {model_name}")
    loader = get_loader()
    loader.flush()
    time.sleep(2)

    recovery_model = "deepscaler-1.5b:latest"
    logger.info(f"Bootstrap: Attempting to load recovery model {recovery_model}")
    if loader.load(recovery_model):
        logger.info("Bootstrap: Recovery model loaded successfully.")
    else:
        logger.error("Bootstrap: Recovery model load failed. System in degraded state.")
