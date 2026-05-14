import json
import re
import subprocess
import time

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

_cached_gpu_info = {}
_cached_gpu_time = 0.0


def set_cached_gpu_info(info: dict):
    global _cached_gpu_info, _cached_gpu_time
    _cached_gpu_info = info
    _cached_gpu_time = time.time()


def get_cached_gpu_info(max_age: float = 35.0) -> dict | None:
    if _cached_gpu_info and (time.time() - _cached_gpu_time) < max_age:
        return _cached_gpu_info
    return None


def get_gpu_memory_info() -> dict:
    """
    Query GPU memory via nvidia-smi.
    Returns {total_gb, used_gb, free_gb, utilization_pct}.
    Falls back to JSON parse of a subprocess call.
    """
    try:
        creationflags = (
            0x08000000  # Phase 11.21.6: 30s timeout for high VRAM load/thermal throttling
        )
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            return _fallback()
        parts = re.split(r",\s*", result.stdout.strip())
        if len(parts) >= 3:
            total_mb = float(parts[0])
            used_mb = float(parts[1])
            free_mb = float(parts[2])
            util = float(parts[3]) if len(parts) >= 4 else 0.0
            return {
                "total_gb": round(total_mb / 1024, 2),
                "used_gb": round(used_mb / 1024, 2),
                "free_gb": round(free_mb / 1024, 2),
                "utilization_pct": util,
            }
    except subprocess.TimeoutExpired:
        logger.warning(
            "Morpheus: nvidia-smi timed out (30s). GPU may be under heavy load or throttling."
        )
        return _fallback()
    except Exception as e:
        logger.error(f"Morpheus: GPU monitoring failed ({e})", exc_info=True)
        return _fallback()

    return _fallback()


def _fallback() -> dict:
    return {
        "total_gb": 8.0,
        "used_gb": 1.0,
        "free_gb": 7.0,
        "utilization_pct": 0.0,
        "source": "fallback",
    }


def get_fragmentation_estimate() -> float:
    """
    Rough fragmentation estimate based on free memory ratio.
    Returns 0.0-1.0 where 1.0 = highly fragmented.
    """
    info = get_gpu_memory_info()
    free = info["free_gb"]
    total = info["total_gb"]
    if total <= 0:
        return 0.0
    # If lots of free memory but small contiguous blocks, flag it
    ratio = free / total
    # Crude heuristic: >60% free but nvidia-smi suggests high use = fragmented
    return max(0.0, 1.0 - ratio) if info.get("utilization_pct", 0) < 50 else 0.3


if __name__ == "__main__":
    import json

    info = get_gpu_memory_info()
    print(json.dumps(info, indent=2))
