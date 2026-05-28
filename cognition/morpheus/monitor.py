import json
import re
import subprocess
import time

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

_cached_gpu_info = {}
_cached_gpu_time = 0.0
_last_failure_time = 0.0


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
    global _last_failure_time
    import os

    # 1. Environment variable override check (DISABLE_NVIDIA_SMI / MOCK_GPU)
    if os.getenv("DISABLE_NVIDIA_SMI") or os.getenv("MOCK_GPU"):
        cached = get_cached_gpu_info(max_age=999999999.0)
        if cached:
            return cached
        return _fallback()

    # 2. Cooldown check after a failure / timeout (60 seconds)
    if (time.time() - _last_failure_time) < 60.0:
        cached = get_cached_gpu_info(max_age=999999999.0)
        if cached:
            return cached
        return _fallback()

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
            _last_failure_time = time.time()
            cached = get_cached_gpu_info(max_age=999999999.0)
            if cached:
                return cached
            return _fallback()

        parts = re.split(r",\s*", result.stdout.strip())
        if len(parts) >= 3:
            total_mb = float(parts[0])
            used_mb = float(parts[1])
            free_mb = float(parts[2])
            util = float(parts[3]) if len(parts) >= 4 else 0.0
            info = {
                "total_gb": round(total_mb / 1024, 2),
                "used_gb": round(used_mb / 1024, 2),
                "free_gb": round(free_mb / 1024, 2),
                "utilization_pct": util,
            }
            set_cached_gpu_info(info)
            return info
    except subprocess.TimeoutExpired:
        logger.warning(
            "Morpheus: nvidia-smi timed out (30s). GPU may be under heavy load or throttling."
        )
        _last_failure_time = time.time()
        cached = get_cached_gpu_info(max_age=999999999.0)
        if cached:
            return cached
        return _fallback()
    except Exception as e:
        logger.error(f"Morpheus: GPU monitoring failed ({e})", exc_info=True)
        _last_failure_time = time.time()
        cached = get_cached_gpu_info(max_age=999999999.0)
        if cached:
            return cached
        return _fallback()

    _last_failure_time = time.time()
    cached = get_cached_gpu_info(max_age=999999999.0)
    if cached:
        return cached
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


class MemoryLeakMonitor:
    def __init__(self, top_n: int = 10, interval_s: int = 300):
        self._top_n = top_n
        self._interval_s = interval_s
        self._snapshot = None
        self._enabled = False

    def start(self):
        try:
            import tracemalloc

            tracemalloc.start(25)
            self._snapshot = tracemalloc.take_snapshot()
            self._enabled = True
            logger.info("MemoryLeakMonitor: tracemalloc started (nframe=25).")
        except Exception as e:
            logger.warning(f"MemoryLeakMonitor: tracemalloc not available ({e})")
            self._enabled = False

    def check(self) -> list[dict]:
        if not self._enabled:
            return []
        try:
            import tracemalloc

            new_snap = tracemalloc.take_snapshot()
            if self._snapshot is None:
                self._snapshot = new_snap
                return []
            stats = new_snap.compare_to(self._snapshot, "lineno")
            top = stats[: self._top_n]
            result = []
            for stat in top:
                frame = stat.traceback[0]
                result.append(
                    {
                        "file": frame.filename,
                        "line": frame.lineno,
                        "size_diff_b": stat.size_diff,
                        "count_diff": stat.count_diff,
                    }
                )
            self._snapshot = new_snap
            return result
        except Exception as e:
            logger.debug(f"MemoryLeakMonitor: check failed ({e})")
            return []

    def should_warn(self, leaks: list[dict], threshold_b: int = 1_048_576) -> bool:
        return any(l["size_diff_b"] > threshold_b for l in leaks)


if __name__ == "__main__":
    import json

    info = get_gpu_memory_info()
    print(json.dumps(info, indent=2))
