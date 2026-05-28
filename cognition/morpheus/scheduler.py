import os
import threading
import time
from dataclasses import dataclass

from src.architrave.base_models import GPU_USABLE_VRAM_GB
from src.architrave.model_registry import find_fitting_model
from src.utils.logging_config import setup_logger

from ..morpheus.monitor import get_gpu_memory_info, set_cached_gpu_info

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
        self._last_request_time = time.time()
        self._load_count: dict[str, int] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_traj_mining: float = 0.0

        # Sprint C: Injected dependencies for autonomous re-sharding
        self._loader = None
        self._sweeper = None

        # Predictive Pre-load attributes [SRC:axis_1]
        self._usage_history: dict[str, list[float]] = {}
        self._session_patterns: dict[str, int] = {}
        self._last_role: str | None = None

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

    def _predict_next_models(self) -> list[str]:
        """
        Predicts the next most likely roles (up to 2) based on transitions and usage frequencies.
        Returns a list of role names.
        """
        predictions = []

        # 1. Transition pattern: most common role1 -> role2 transition in the last 3 transitions
        if self._last_role:
            prefix = f"{self._last_role}->"
            transitions = {k: v for k, v in self._session_patterns.items() if k.startswith(prefix)}
            if transitions:
                sorted_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
                for pattern, _count in sorted_transitions:
                    next_role = pattern.split("->")[1]
                    if next_role not in predictions:
                        predictions.append(next_role)
                    if len(predictions) >= 2:
                        break

        # 2. Role frequency: fill based on usage frequency in the last 24 hours
        if len(predictions) < 2:
            now = time.time()
            twenty_four_hours_ago = now - 86400
            frequencies = {}
            for r, ts_list in self._usage_history.items():
                recent = [t for t in ts_list if t >= twenty_four_hours_ago]
                frequencies[r] = len(recent)

            sorted_freqs = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
            for r, _freq in sorted_freqs:
                if r not in predictions:
                    predictions.append(r)
                if len(predictions) >= 2:
                    break

        return predictions

    def _preload_model_in_background(self, model_name: str):
        """Asynchronously pre-loads a predicted next model into VRAM if enough budget exists."""
        try:
            from src.utils.service_locator import get_bootstrap_loader

            loader = get_bootstrap_loader()
            if not loader:
                return

            if model_name == loader.loaded:
                return

            gpu_info = get_gpu_memory_info()
            free_gb = gpu_info.get("free_gb", 0.0)

            from src.architrave.base_models import VRAM_CATALOG_GB

            req_gb = VRAM_CATALOG_GB.get(model_name, 2.0)

            # Predictive preload VRAM safety check: free_gb - req_gb >= 1.0 (safety budget)
            if (free_gb - req_gb) >= 1.0:
                logger.info(
                    f"MorpheusScheduler: Pre-loading predicted model '{model_name}' (free: {free_gb}GB, req: {req_gb}GB)"
                )
                loader.load(model_name)
            else:
                logger.info(
                    f"MorpheusScheduler: Skipping preload for '{model_name}' due to VRAM safety budget (free: {free_gb}GB, req: {req_gb}GB)"
                )
        except Exception as e:
            logger.warning(f"MorpheusScheduler: Failed to preload model '{model_name}' ({e})")

    def request_model(self, role: str) -> str | None:
        """Request a model for a given role. Returns model name or None if no fit."""
        with self._lock:
            now = time.time()
            if role not in self._usage_history:
                self._usage_history[role] = []
            self._usage_history[role].append(now)

            # Record role transition
            if self._last_role:
                pattern = f"{self._last_role}->{role}"
                self._session_patterns[pattern] = self._session_patterns.get(pattern, 0) + 1
            self._last_role = role

            gpu_info = get_gpu_memory_info()
            free_gb = gpu_info.get("free_gb", 0)
            model_name = find_fitting_model(role, available_vram_gb=free_gb)
            if model_name:
                self._last_request_time = now
                self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                logger.info(f"MorpheusScheduler: Model {model_name} requested for role {role}")

                # Predict next models and trigger asynchronous background preloading
                predicted_roles = self._predict_next_models()
                for pred_role in predicted_roles:
                    if pred_role == role:
                        continue
                    pred_model = find_fitting_model(pred_role, available_vram_gb=free_gb)
                    if pred_model and pred_model != model_name:
                        threading.Thread(
                            target=self._preload_model_in_background,
                            args=(pred_model,),
                            daemon=True,
                        ).start()

                return model_name
            logger.warning(
                f"MorpheusScheduler: No fitting model for role {role} ({free_gb}GB free)"
            )
            return None

    def _run_loop(self):
        """Internal tick loop for autonomous VRAM management + weekly OTL mining."""
        try:
            import psutil  # type: ignore

            p = psutil.Process()
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

            # Weekly trajectory mining cron hook
            now = time.time()
            if now - self._last_traj_mining >= 604800:
                self._last_traj_mining = now
                logger.info("MorpheusScheduler: Running weekly OTL trajectory mining...")
                try:
                    import subprocess

                    root = os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                    subprocess.Popen(
                        [
                            os.path.join(root, ".venv", "Scripts", "python.exe"),
                            os.path.join(root, "scripts", "run_trajectory_mining.py"),
                        ],
                        cwd=root,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                except Exception as me:
                    logger.error(f"MorpheusScheduler: Weekly trajectory mining failed ({me})")

            time.sleep(interval)

    def _orchestrate_vram(self):
        gpu_info = get_gpu_memory_info()
        set_cached_gpu_info(gpu_info)
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

            try:
                from src.utils.service_locator import get_bootstrap_loader, get_bootstrap_sweeper

                sweeper = get_bootstrap_sweeper()
                loader = get_bootstrap_loader()
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
    logger.info("=== Morpheus Scheduler: Firmitas Test ===")
    scheduler = MorpheusScheduler(idle_cooldown_s=30)
    logger.info(f"Scheduler initialized. Idle cooldown: {scheduler.idle_cooldown_s}s")
    state = scheduler.state()
    logger.info(f"GPU State: {state.gpu_free_gb}GB free, {state.gpu_used_gb}GB used")
    logger.info("Scheduler connectivity verified.")
