import json
import os
import threading
import time
import urllib.request

import ollama

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def _is_embedding_model(model_name: str) -> bool:
    name_lower = model_name.lower()
    return "embed" in name_lower or "bge" in name_lower or "mxbai" in name_lower


class KeepAlivePool:
    """LRU Keep-Alive Pool to maintain a list of active models in VRAM."""

    def __init__(self, max_size: int = 2):
        self._pool = {}  # model_name -> logical sequence counter
        self._max_size = max_size
        self._counter = 0
        self._lock = threading.Lock()

    def add(self, model: str):
        with self._lock:
            self._counter += 1
            self._pool[model] = self._counter

    def get_least_recently_used(self) -> str | None:
        with self._lock:
            if not self._pool:
                return None
            try:
                from .vram_config import CORE_MODELS
            except ImportError:
                CORE_MODELS = ["tinyllama:latest"]

            candidates = {m: t for m, t in self._pool.items() if m not in CORE_MODELS}
            if not candidates:
                return None
            return min(candidates, key=lambda x: candidates[x])

    def remove(self, model: str):
        with self._lock:
            if model in self._pool:
                del self._pool[model]

    def contains(self, model: str) -> bool:
        with self._lock:
            return model in self._pool

    def size(self) -> int:
        with self._lock:
            return len(self._pool)

    def get_all(self) -> list[str]:
        with self._lock:
            return list(self._pool.keys())


class VRAMBudgetGuard:
    """Guards VRAM safety budget by dynamically evicting non-hot, non-core models."""

    def __init__(self, min_free_gb: float = 1.0):
        self.min_free_gb = min_free_gb

    def guard_vram(self, required_gb: float, loader) -> bool:
        from .monitor import get_gpu_memory_info

        info = get_gpu_memory_info()
        free_gb = info.get("free_gb", 0.0)
        after_load = free_gb - required_gb

        if after_load >= self.min_free_gb:
            logger.debug(
                f"VRAMBudgetGuard: Sufficient VRAM. Free: {free_gb}GB, Required: {required_gb}GB, Margin: {after_load}GB >= {self.min_free_gb}GB"
            )
            return True

        logger.warning(
            f"VRAMBudgetGuard: Eviction triggered! Free: {free_gb}GB, Required: {required_gb}GB, Margin: {after_load}GB < {self.min_free_gb}GB"
        )

        try:
            from .vram_config import CORE_MODELS, EVICTION_ORDER
        except ImportError:
            EVICTION_ORDER = []
            CORE_MODELS = ["tinyllama:latest"]

        from src.architrave.base_models import VRAM_CATALOG_GB

        # Try evicting from EVICTION_ORDER
        for model in EVICTION_ORDER:
            # Rules:
            # 1. Skip if model is in CORE_MODELS
            if model in CORE_MODELS:
                continue
            # 2. Skip if model is currently loaded
            if model == loader._loaded_model:
                continue

            # Evict!
            logger.info(f"VRAMBudgetGuard: Evicting model '{model}' to free VRAM")
            try:
                # Call Ollama unload directly:
                client = ollama.Client(host=loader.base_url)
                if _is_embedding_model(model):
                    client.embeddings(model=model, prompt=".", keep_alive=0)
                else:
                    client.chat(
                        model=model,
                        messages=[{"role": "user", "content": "."}],
                        options={"num_predict": 1, "num_keep": 0},
                        keep_alive=0,
                    )
                model_vram = VRAM_CATALOG_GB.get(model, 2.0)
                free_gb += model_vram
                # Remove from pool if it was there
                loader._pool.remove(model)
                logger.debug(
                    f"VRAMBudgetGuard: Model '{model}' evicted. Simulated Free: {free_gb}GB"
                )

                if (free_gb - required_gb) >= self.min_free_gb:
                    logger.info(
                        f"VRAMBudgetGuard: Eviction successful! Budget restored. Simulated Free: {free_gb}GB"
                    )
                    return True
            except Exception as e:
                logger.error(f"VRAMBudgetGuard: Failed to evict model '{model}' ({e})")

        return False


class ModelLoader:
    """
    Manages Ollama model load/unload lifecycle.
    Uses the Ollama API to warm models into GPU memory.
    """

    def __init__(
        self,
        base_url: str | None = None,
        swap_threshold_gb: float | None = None,
        frag_threshold: float | None = None,
    ):
        self.swap_threshold = swap_threshold_gb or float(os.getenv("VRAM_SWAP_THRESHOLD_GB", "5.5"))
        self.frag_threshold = frag_threshold or float(os.getenv("VRAM_FRAG_THRESHOLD", "0.3"))
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").replace(
            "/v1", ""
        )
        self._loaded_model: str | None = None
        self._load_count: dict = {}

        # KeepAlivePool + Lock Thread Safety [SRC:axis_1]
        self._pool = KeepAlivePool(max_size=2)
        self._lock = threading.Lock()

    def sync_from_ollama(self):
        """Sync _loaded_model from ollama ps output. Catches models loaded by IDE directly."""
        with self._lock:
            self._sync_from_ollama_unlocked()

    def _sync_from_ollama_unlocked(self):
        try:
            req = urllib.request.Request(f"{self.base_url}/api/ps")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            ps_models = data.get("models", [])
            loaded_names = [m.get("name", m.get("model", "")) for m in ps_models]
            logger.debug(f"ModelLoader: ollama ps found: {loaded_names}")

            try:
                from .vram_config import CORE_MODELS
            except ImportError:
                CORE_MODELS = ["tinyllama:latest"]

            # Finding 4: sync pool with actual loaded models in Ollama
            for name in loaded_names:
                if not self._pool.contains(name):
                    self._pool.add(name)
            for pool_model in self._pool.get_all():
                if pool_model not in loaded_names:
                    self._pool.remove(pool_model)

            if not ps_models:
                if self._loaded_model is not None:
                    logger.info("ModelLoader: ollama ps empty, clearing stale _loaded_model")
                    self._loaded_model = None
                return

            for name in loaded_names:
                if name in CORE_MODELS:
                    if self._loaded_model != name:
                        logger.info(
                            f"ModelLoader: Synced _loaded_model -> '{name}' (from ollama ps)"
                        )
                        self._loaded_model = name
                    return
            for name in loaded_names:
                if self._loaded_model != name:
                    logger.debug(f"ModelLoader: Synced _loaded_model -> '{name}' (non-core)")
                    self._loaded_model = name
                return
        except Exception as e:
            logger.debug(f"ModelLoader: sync_from_ollama failed ({e})")

    def load(self, model_name: str, timeout_s: int = 30) -> bool:
        with self._lock:
            if model_name == self._loaded_model:
                self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                self._pool.add(model_name)
                return True
            try:
                self._sync_from_ollama_unlocked()
                if model_name == self._loaded_model:
                    self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                    self._pool.add(model_name)
                    return True

                # Check VRAMBudgetGuard
                from src.architrave.base_models import VRAM_CATALOG_GB

                req_gb = VRAM_CATALOG_GB.get(model_name, 2.0)
                guard = VRAMBudgetGuard()
                if not guard.guard_vram(req_gb, self):
                    logger.critical(f"VRAMBudgetGuard: Cannot fit {model_name}")
                    return False

                # KeepAlivePool LRU eviction if size exceeds limit
                try:
                    from .vram_config import CORE_MODELS
                except ImportError:
                    CORE_MODELS = ["tinyllama:latest"]

                active_pool_size = len([m for m in self._pool.get_all() if m not in CORE_MODELS])
                if active_pool_size >= self._pool._max_size and not self._pool.contains(model_name):
                    evict = self._pool.get_least_recently_used()
                    if evict:
                        logger.info(f"KeepAlivePool: Evicting LRU model '{evict}' from pool")
                        try:
                            client = ollama.Client(host=self.base_url)
                            if _is_embedding_model(evict):
                                client.embeddings(model=evict, prompt=".", keep_alive=0)
                            else:
                                client.chat(
                                    model=evict,
                                    messages=[{"role": "user", "content": "."}],
                                    options={"num_predict": 1, "num_keep": 0},
                                    keep_alive=0,
                                )
                        except Exception as e:
                            logger.error(
                                f"KeepAlivePool: Failed to unload LRU model '{evict}' ({e})"
                            )
                        self._pool.remove(evict)
                        if self._loaded_model == evict:
                            self._loaded_model = None

                self._unload_current_unlocked()
                client = ollama.Client(host=self.base_url)
                if _is_embedding_model(model_name):
                    resp = client.embeddings(
                        model=model_name,
                        prompt="ping",
                        keep_alive=-1,
                    )
                else:
                    resp = client.chat(
                        model=model_name,
                        messages=[{"role": "user", "content": "ping"}],
                        options={"num_predict": 1},
                        keep_alive=-1,
                    )
                if resp and ("message" in resp or "embedding" in resp or "embeddings" in resp):
                    self._loaded_model = model_name
                    self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                    self._pool.add(model_name)
                    logger.info(f"Morpheus: Successfully loaded {model_name} (keep_alive=-1)")
                    return True
            except Exception as e:
                err_str = str(e).lower()
                if "cuda" in err_str and ("out of memory" in err_str or "oom" in err_str):
                    logger.critical(
                        f"Morpheus: CUDA OOM detected loading {model_name}. Forcing emergency flush..."
                    )
                    self._flush_unlocked()
                    time.sleep(2)
                    import gc

                    gc.collect()
                    return False  # Notifies upper layer of OOM
                logger.error(f"Morpheus: Failed to load {model_name} ({e})", exc_info=True)
                return False
            return False

    def unload_current(self):
        """Unloads current Ollama model and stops any active LocalRuntime (llama.cpp) processes."""
        with self._lock:
            self._unload_current_unlocked()

    def _unload_current_unlocked(self):
        # GPU Constants
        float(os.getenv("GPU_TOTAL_VRAM_GB", 7.0))

        try:
            req = urllib.request.Request(f"{self.base_url}/api/ps")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            ps_models = data.get("models", [])
            [m.get("name", m.get("model", "")) for m in ps_models]
        except Exception:
            pass

        if self._loaded_model:
            try:
                from .vram_config import CORE_MODELS
            except ImportError:
                CORE_MODELS = ["tinyllama:latest"]

            # If loaded model is in core models or in keep-alive pool, we skip unloading from Ollama!
            if self._loaded_model in CORE_MODELS or self._pool.contains(self._loaded_model):
                logger.info(f"Morpheus: Skipping unload of hot/core model '{self._loaded_model}'")
                return

            try:
                # 1. Unload from Ollama
                client = ollama.Client(host=self.base_url)
                if _is_embedding_model(self._loaded_model):
                    client.embeddings(model=self._loaded_model, prompt=".", keep_alive=0)
                else:
                    client.chat(
                        model=self._loaded_model,
                        messages=[{"role": "user", "content": "."}],
                        options={"num_predict": 1, "num_keep": 0},
                        keep_alive=0,
                    )
                logger.info(f"Morpheus: Unloaded Ollama model '{self._loaded_model}'")
            except Exception as e:
                logger.error(f"Morpheus: Failed to unload Ollama model ({e})")
            self._loaded_model = None

        # 2. Kill any active LocalRuntime (llama.cpp) processes (Sequential Loading Protocol)
        try:
            from src.muscle.local_runtime import LocalRuntime

            LocalRuntime.stop_active()
        except Exception as e:
            logger.debug(f"Morpheus: No active LocalRuntime to stop or stop failed ({e})")

    def flush(self):
        """Forceful VRAM cleanup: Unloads everything and triggers system-level flush."""
        with self._lock:
            self._flush_unlocked()

    def _flush_unlocked(self):
        logger.warning("Morpheus: Triggering global VRAM flush...")

        # Clear pool as well on global flush!
        for model in self._pool.get_all():
            try:
                client = ollama.Client(host=self.base_url)
                if _is_embedding_model(model):
                    client.embeddings(model=model, prompt=".", keep_alive=0)
                else:
                    client.chat(
                        model=model,
                        messages=[{"role": "user", "content": "."}],
                        options={"num_predict": 1, "num_keep": 0},
                        keep_alive=0,
                    )
            except Exception:
                pass
            self._pool.remove(model)

        self._unload_current_unlocked()
        import gc

        gc.collect()

    def should_pin(self, model_name: str) -> bool:
        try:
            from .vram_config import CORE_MODELS
        except ImportError:
            CORE_MODELS = ["tinyllama:latest"]

        return (
            model_name in self._pool.get_all()
            or model_name in CORE_MODELS
            or self._load_count.get(model_name, 0) >= 3
        )

    @property
    def loaded(self) -> str | None:
        return self._loaded_model
