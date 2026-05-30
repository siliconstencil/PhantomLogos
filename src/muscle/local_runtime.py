import asyncio
import os
import subprocess
import sys

from src.utils.project_path import get_project_root

from ..utils.logging_config import setup_logger

logger = setup_logger(__name__)


class LocalRuntime:
    """
    llama.cpp based local runtime manager.
    [SRC:axis_12] Manages local process execution and hardware resource monitoring.
    Handles architecture-specific binary selection (e.g., llama-mtmd-cli for MiMo-VL).
    """

    def __init__(self, binary_dir: str | None = None, base_model_dir: str | None = None) -> None:
        root = get_project_root()
        self.binary_dir = (
            binary_dir or os.getenv("LLM_BINARY_DIR") or os.path.join(root, "bin", "llama_bin")
        )
        # Hardened path resolution: LLM_MODEL_DIR is mandatory for deterministic execution
        self.base_model_dir = base_model_dir or os.getenv("LLM_MODEL_DIR")
        if not self.base_model_dir:
            logger.warning(
                "LocalRuntime: LLM_MODEL_DIR not set, falling back to workspace relative path."
            )
            # Safe fallback using root if env vars are missing
            alt_root = os.getenv("ANTIGRAVITY_ROOT") or str(root)
            self.base_model_dir = os.path.join(alt_root, "models")
            logger.warning(
                "LocalRuntime: LLM_MODEL_DIR not set. Set LLM_MODEL_DIR env var to your GGUF model directory."
            )

        self._validate_path(self.binary_dir, "Binary Dir")
        self._validate_path(self.base_model_dir, "Model Dir")
        self.active_process = None

    def _validate_path(self, path: str, label: str) -> None:
        """Ensures the path is absolute, exists and lies in safe directories (P3.11)."""
        if not path:
            raise ValueError(f"{label} path is empty")
        # Normalize and check existence
        norm_path = os.path.abspath(path)

        # Hardened Whitelist check for safe directories (Axis 13)
        project_root = str(get_project_root())
        if not norm_path.startswith(project_root):
            raise ValueError(f"LocalRuntime: Unsafe path detected for {label}: {norm_path}")

        if not os.path.exists(norm_path):
            logger.error(f"LocalRuntime: {label} does not exist: {norm_path}")
            # We don't raise here in __init__ to avoid early crashes,
            # but we will check again in run_vision

    def _get_binary(self, architecture: str) -> str:
        """Returns the correct binary path based on the architecture."""
        ext = ".exe" if sys.platform == "win32" else ""
        binaries = {
            "qwen2vl": f"llama-mtmd-cli{ext}",
            "gemma4": f"llama-mtmd-cli{ext}",
            "qwen3vl": f"llama-mtmd-cli{ext}",
            "llava": f"llama-llava-cli{ext}",
            "generic": f"llama-cli{ext}",
        }
        bin_name = binaries.get(architecture, f"llama-cli{ext}")
        return os.path.join(self.binary_dir, bin_name)

    def _calculate_ngl(self, registry_name: str, num_ctx: int, actual_layers: int) -> int:
        """
        Calculates optimal -ngl (GPU layers) based on VRAM budget and actual model layers.
        [SRC:axis_12] VRAM-aware layer offloading logic.
        """
        try:
            from src.architrave.base_models import GPU_USABLE_VRAM_GB, VRAM_CATALOG_GB

            model_size = VRAM_CATALOG_GB.get(registry_name, 4.0)

            # Estimate KV-Cache (rough 0.5-1.5 GB depending on ctx)
            kv_cache_est = (num_ctx / 32768) * 1.5
            total_req = model_size + kv_cache_est

            if total_req <= GPU_USABLE_VRAM_GB:
                return 99  # Full offload

            # Partial offload: Using actual layers from registry (Pro Restoration)
            safe_vram = GPU_USABLE_VRAM_GB - kv_cache_est - 0.5  # 0.5 margin
            if safe_vram <= 0:
                return 0

            ratio = safe_vram / model_size
            ngl = int(actual_layers * ratio)
            logger.info(
                f"LocalRuntime: Partial offload calculated: {ngl}/{actual_layers} layers (ratio: {ratio:.2f})"
            )
            return ngl
        except Exception as e:
            logger.warning(f"LocalRuntime: ngl calculation failed ({e}), defaulting to 20")
            return 20

    def run_vision(
        self,
        architecture: str,
        model_rel_path: str,
        mmproj_rel_path: str,
        prompt: str,
        image_path: str,
        num_ctx: int = 2048,
        registry_name: str = "generic",
        layers: int = 32,
    ) -> str:
        """
        Executes Vision models using architecture-specific binaries.
        """
        binary_path = self._get_binary(architecture)
        base_dir = self.base_model_dir or ""
        model_path = os.path.join(base_dir, model_rel_path)
        mmproj_path = os.path.join(base_dir, mmproj_rel_path)

        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"Binary not found at {binary_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        if mmproj_path and not os.path.exists(mmproj_path):
            raise FileNotFoundError(f"MMProj not found at {mmproj_path}")

        # Phase 11.18.3: Dynamic ngl (Pro Restoration - Fixed VRAM Key & Layers)
        ngl = self._calculate_ngl(registry_name, num_ctx, layers)

        cmd = [
            binary_path,
            "-m",
            model_path,
            "--mmproj",
            mmproj_path,
            "--image",
            image_path,
            "-p",
            prompt,
            "--temp",
            "0.7",
            "-n",
            "512",
            "-ngl",
            str(ngl),
            "-c",
            str(num_ctx),
        ]

        logger.info(f"--- Executing {architecture} Vision ---")
        logger.debug(f"Command: {' '.join(cmd)}")

        creationflags = 0x08000000 if sys.platform == "win32" else 0
        try:
            self.active_process = subprocess.Popen(  # noqa: S603
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=creationflags,
            )
            stdout, stderr = self.active_process.communicate()
            if self.active_process.returncode == 0:
                return stdout
            else:
                err_msg = f"LocalRuntime Error ({self.active_process.returncode}): {stderr}"
                logger.error(err_msg)
                raise RuntimeError(err_msg)
        except Exception as e:
            logger.error(f"LocalRuntime Exception: {e}", exc_info=True)
            raise
        finally:
            self.active_process = None

    @staticmethod
    def stop_active() -> None:
        """Statically terminates all active llama processes (Sequential Loading Protocol)."""
        try:
            import subprocess

            creationflags = 0x08000000 if sys.platform == "win32" else 0
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "llama*", "/T"],  # noqa: S607
                    capture_output=True,
                    creationflags=creationflags,
                )
            else:
                subprocess.run(["pkill", "-f", "llama"], capture_output=True)  # noqa: S607
            logger.info("LocalRuntime: All active llama processes terminated.")
        except Exception as e:
            logger.warning(f"LocalRuntime: Failed to terminate processes ({e})")

    async def run_vision_async(
        self,
        architecture: str,
        model_rel_path: str,
        mmproj_rel_path: str,
        prompt: str,
        image_path: str,
        num_ctx: int = 2048,
        registry_name: str = "generic",
        layers: int = 32,
    ) -> str:
        """Async wrapper for run_vision to avoid blocking the event loop."""
        return await asyncio.to_thread(
            self.run_vision,
            architecture,
            model_rel_path,
            mmproj_rel_path,
            prompt,
            image_path,
            num_ctx,
            registry_name,
            layers,
        )
