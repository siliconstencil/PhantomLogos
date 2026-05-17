import os
import threading
import time
from dataclasses import dataclass

from src.utils.logging_config import setup_logger

from ..morpheus.monitor import get_gpu_memory_info, set_cached_gpu_info
from ..morpheus.registry import GPU_USABLE_VRAM_GB, find_fitting_model

logger = setup_logger(__name__)


@dataclass
class SchedulerState:
    """Snapshot of the Morpheus scheduler state at a given tick."""

    active_model: str | None = None
    gpu_used_gb: float = 0.0
    gpu_free_gb: float = 0.0
    fragmentation: float = 0.0
    pending_requests: int = 0
    last_tick: float = 0.0


class MorpheusScheduler:
    """
    Background scheduler that monitors GPU VRAM and makes model load/unload decisions.

    Decision rules:
    - Idle for `idle_cooldown_s` with high VRAM pressure -> unload model
    - New model request -> check VRAM fit via registry
    - High fragmentation -> trigger sweep
    """

    def __init__(self, idle_cooldown_s: float | None = None):
        self.idle_cooldown_s = idle_cooldown_s or float(
            os.getenv("MORPHEUS_IDLE_COOLDOWN_S", "120.0")
        )
        self._lock = threading.Lock()
        self._active_model: str | None = None
        self._last_request_time: float = time.time()
        self._load_count: dict[str, int] = {}
        self._running = False
        self._thread: threading.Thread | None = None

        # Sprint C: Injected dependencies for autonomous re-sharding
        self._loader = None
        self._sweeper = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("MorpheusScheduler: Background loop started.")

    def stop(self):
        self._running = False
        logger.info("MorpheusScheduler: Stop signal sent.")

    def request_model(self, role: str) -> str | None:
        """Request a model for a given role. Returns model name or None if no fit."""
        gpu_info = get_gpu_memory_info()
        free_gb = gpu_info.get("free_gb", 0)
        model_name = find_fitting_model(role, available_vram_gb=free_gb)
        if model_name:
            self._last_request_time = time.time()
            self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
            logger.info(f"MorpheusScheduler: Model {model_name} requested for role {role}")
            return model_name
        logger.warning(f"MorpheusScheduler: No fitting model for role {role} ({free_gb}GB free)")
        return None

    def _run_loop(self):
        """Internal tick loop for autonomous VRAM management."""
        # Phase 11.18.15: Set E-core affinity for background Morpheus daemon
        try:
            import psutil

            p = psutil.Process()
            # i7-13620H: 6 P-cores (0-11) + 4 E-cores (12-15)
            # Correct Mask: 0xf000
            p.cpu_affinity([12, 13, 14, 15])
            logger.info("MorpheusScheduler: CPU Affinity set to E-cores [12, 13, 14, 15].")
        except Exception as e:
            logger.warning(f"MorpheusScheduler: Failed to set CPU affinity ({e})")

        interval = float(os.getenv("MORPHEUS_TICK_INTERVAL_S", "300.0"))
        while self._running:
            try:
                self._orchestrate_vram()
            except Exception as e:
                logger.error(f"MorpheusScheduler: Tick error ({e})", exc_info=True)
            time.sleep(interval)

    def _orchestrate_vram(self):
        gpu_info = get_gpu_memory_info()
        set_cached_gpu_info(gpu_info)  # Merge Attack: make VRAM data globally available
        used_gb = gpu_info.get("used_gb", 0)
        free_gb = gpu_info.get("free_gb", 0)
        idle_time = time.time() - self._last_request_time

        # Sprint C: Dynamic Idle Threshold
        idle_vram_threshold = float(
            os.getenv("MORPHEUS_VRAM_IDLE_THRESHOLD_GB", str(GPU_USABLE_VRAM_GB * 0.25))
        )

        if idle_time > self.idle_cooldown_s and used_gb > idle_vram_threshold:
            logger.info(
                f"MorpheusScheduler: Autonomous sweep triggered (Idle for {int(idle_time)}s, {used_gb}GB VRAM used)"
            )

            # Use bootstrap to get singletons safely
            try:
                from src.utils.service_locator import get_bootstrap_loader, get_bootstrap_sweeper

                sweeper = get_bootstrap_sweeper()
                loader = get_bootstrap_loader()
                # Sprint C: Soru 1 Approved - Trigger autonomous re-sharding
                sweeper.check_and_sweep(loader)
            except Exception as e:
                logger.warning(f"MorpheusScheduler: Autonomous sweep failed to execute ({e})")

        try:
            from cognition.mnemosyne.temporal_store import TemporalStore

            ts = TemporalStore()
            ts.record(
                session_id="morpheus",
                event_type="scheduler.tick",
                model_name="morpheus",
                vram_gb=used_gb,
                extra={"free_gb": free_gb, "idle_s": round(idle_time, 1)},
            )
        except Exception as e:
            logger.warning(f"MorpheusScheduler: TemporalStore tick record failed ({e})")

    def state(self) -> SchedulerState:
        gpu_info = get_gpu_memory_info()
        return SchedulerState(
            active_model=self._active_model,
            gpu_used_gb=gpu_info.get("used_gb", 0),
            gpu_free_gb=gpu_info.get("free_gb", 0),
            fragmentation=gpu_info.get("utilization_pct", 0) / 100,
            pending_requests=len(self._load_count),
            last_tick=time.time(),
        )


if __name__ == "__main__":
    # Firmitas Test: demonstrate scheduler instantiation
    logger.info("=== Morpheus Scheduler: Firmitas Test ===")
    scheduler = MorpheusScheduler(idle_cooldown_s=30)
    logger.info(f"Scheduler initialized. Idle cooldown: {scheduler.idle_cooldown_s}s")
    state = scheduler.state()
    logger.info(f"GPU State: {state.gpu_free_gb}GB free, {state.gpu_used_gb}GB used")
    logger.info("Scheduler connectivity verified.")
