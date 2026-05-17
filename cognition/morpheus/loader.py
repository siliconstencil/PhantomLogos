import json
import os
import subprocess
import time
import urllib.request

import ollama

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


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

    def sync_from_ollama(self):
        """Sync _loaded_model from ollama ps output. Catches models loaded by IDE directly."""
        # Phase 11.21.6: 15s timeout for high VRAM load
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total,memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            req = urllib.request.Request(f"{self.base_url}/api/ps")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            ps_models = data.get("models", [])
            if not ps_models:
                if self._loaded_model is not None:
                    logger.info("ModelLoader: ollama ps empty, clearing stale _loaded_model")
                    self._loaded_model = None
                return
            loaded_names = [m.get("name", m.get("model", "")) for m in ps_models]
            logger.debug(f"ModelLoader: ollama ps found: {loaded_names}")
            CORE_MODELS = [
                "tinyllama:latest",
            ]
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
        if model_name == self._loaded_model:
            self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
            return True
        try:
            self.sync_from_ollama()
            if model_name == self._loaded_model:
                self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                return True

            self.unload_current()
            client = ollama.Client(host=self.base_url)
            resp = client.chat(
                model=model_name,
                messages=[{"role": "user", "content": "ping"}],
                options={"num_predict": 1},
                keep_alive=-1,
            )
            if resp and "message" in resp:
                self._loaded_model = model_name
                self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                logger.info(f"Morpheus: Successfully loaded {model_name} (keep_alive=-1)")
                return True
        except Exception as e:
            err_str = str(e).lower()
            if "cuda" in err_str and ("out of memory" in err_str or "oom" in err_str):
                logger.critical(
                    f"Morpheus: CUDA OOM detected loading {model_name}. Forcing emergency flush..."
                )
                self.flush()
                time.sleep(2)
                import gc

                gc.collect()
                return False  # Notifies upper layer of OOM
            logger.error(f"Morpheus: Failed to load {model_name} ({e})", exc_info=True)
            return False
        return False

    def unload_current(self):
        """Unloads current Ollama model and stops any active LocalRuntime (llama.cpp) processes."""
        # GPU Constants
        GPU_TOTAL_VRAM_GB = float(os.getenv("GPU_TOTAL_VRAM_GB", 7.0))
        GPU_SAFETY_MARGIN_GB = 1.0
        self.sync_from_ollama()
        if self._loaded_model:
            # Phase 11.21.x: Never unload core models (keeps IDE responsive)
            try:
                from .vram_config import CORE_MODELS

                if self._loaded_model in CORE_MODELS:
                    logger.info(f"Morpheus: Skipping unload of core model '{self._loaded_model}'")
                    return
            except ImportError:
                pass
            try:
                # 1. Unload from Ollama
                client = ollama.Client(host=self.base_url)
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
        logger.warning("Morpheus: Triggering global VRAM flush...")
        self.unload_current()
        # Additional system-level hygiene if needed (e.g., garbage collection)
        import gc

        gc.collect()

    def should_pin(self, model_name: str) -> bool:
        # Phase 11.21.x: Core models are always pinned (never evicted)
        try:
            from .vram_config import CORE_MODELS

            if model_name in CORE_MODELS:
                return True
        except ImportError:
            pass
        return self._load_count.get(model_name, 0) >= 3

    @property
    def loaded(self) -> str | None:
        return self._loaded_model
