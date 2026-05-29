import asyncio
import json
import os
from collections import OrderedDict

from cognition.sophia.hephaestus import _get_loader, _get_pruner, _get_sweeper
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)

_context_cache_local = OrderedDict()
_MAX_CACHE_ENTRIES = 20


def _check_system_status() -> str | None:
    """Reads data/system_status.json and returns a formatted ERROR block if critical. [SRC:axis_11]"""
    status_path = "data/system_status.json"
    if not os.path.exists(status_path):
        return None

    try:
        with open(status_path, encoding="utf-8") as f:
            data = json.load(f)

        if data.get("status") == "ERROR":
            filename = data.get("file", "unknown")
            msg = data.get("message", "Violation detected")
            ts = data.get("time", "unknown")

            return (
                "### SYSTEM CRITICAL UYARI (Watchdog)\n"
                f"**DURUM**: KRITIK IHLAL\n"
                f"**DOSYA**: {filename}\n"
                f"**OLAY**: {msg}\n"
                f"**ZAMAN**: {ts}\n"
                "**TALIMAT**: Sovereign Shield yetkisiz bir degisiklik algiladi ve geri aldi. "
                "Isleme devam etmeden once degisikliklerin dogrulugunu ve L0 yetkisini (create_l0_token.py) kontrol edin. [SRC:axis_11]"
            )
    except Exception as e:
        logger.warning(f"Gnosis: Failed to parse system_status.json ({e})")

    return None


async def get_dynamic_context(
    agent_id: str, task_hint: str = "", session_id: str = "default"
) -> tuple[str, str, dict]:
    """
    [SRC:axis_12] Returns a split context: (stable_context, dynamic_context, block_signal).
    Stable context is suitable for System Instruction (Implicit Caching).
    Dynamic context contains task-specific and rapidly changing axes.
    """
    cache_key = f"{agent_id}:{task_hint[:40]}:{session_id}"

    # [SRC:axis_12] Query disk-based cache first
    try:
        import hashlib

        from src.architrave.context_cache import ContextCacheStore

        hashed_key = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        disk_cache = ContextCacheStore(start_sweep=False)
        cached_val = disk_cache.get_by_key(hashed_key)
        if cached_val:
            data = json.loads(cached_val)
            res = (data["stable_context"], data["dynamic_context"], data["block_signal"])
            _context_cache_local[cache_key] = res
            return res
    except Exception as e:
        logger.warning(f"Gnosis: ContextCacheStore lookup failed ({e})")

    if cache_key in _context_cache_local:
        _context_cache_local.move_to_end(cache_key)
        return _context_cache_local[cache_key]

    anchor_path = "data/ankyra_anchor.md"
    anchor = ""
    if os.path.exists(anchor_path):
        with open(anchor_path, encoding="utf-8") as f:
            anchor = f.read()

    stable_context = [f"### PROJECT ANCHOR (ANKYRA)\n{anchor}"]

    # [Phase 1.0.12] System Health Check (Watchdog Integration)
    status_block = _check_system_status()
    if status_block:
        stable_context.append(status_block)

    dynamic_context = []
    block_signal = {"block": False, "reason": None}
    embedding_vec = None

    if task_hint:
        try:
            _get_sweeper().check_and_sweep(_get_loader())
            import numpy as np

            from src.clotho.activity import ActivityMonitor

            ActivityMonitor().increment()
            from src.architrave.model_registry import resolve_local_model

            client = get_ollama_client()
            try:
                embedding_model = resolve_local_model("embedding")
                resp = await asyncio.wait_for(
                    client.embeddings(model=embedding_model, prompt=task_hint), timeout=5.0
                )
                # Phase 11.21.x: Ollama returns Pydantic EmbeddingsResponse, not dict
                embedding_vec = np.array(resp.embedding)[:256]
            except Exception as e:
                logger.warning(f"Gnosis: Embedding extraction failed ({e})")
            finally:
                ActivityMonitor().decrement()
        except Exception:
            pass

    # --- 14-Axis Context Building ---
    from .axis_1_episodic import _build_axis_1
    from .axis_2_procedural import _build_axis_2
    from .axis_3_goals import _build_axis_3
    from .axis_4_temporal import _build_axis_4
    from .axis_5_spatial import _build_axis_5
    from .axis_6_semantic import _build_axis_6
    from .axis_7_operational import _build_axis_7
    from .axis_8_meta import _build_axis_8_failures, _build_axis_8_meta
    from .axis_9_tone import _build_axis_9
    from .axis_10_rational import _build_axis_10
    from .axis_11_verify import _build_axis_11
    from .axis_12_cache import _build_axis_12
    from .axis_13_patterns import _build_axis_13
    from .axis_14_visual import _build_axis_14

    try:
        # [K2.6] Schedule all async axes in parallel
        a1_task = asyncio.create_task(_build_axis_1(session_id))
        a6_task = asyncio.create_task(_build_axis_6(task_hint, session_id, embedding_vec))
        a8f_task = asyncio.create_task(_build_axis_8_failures(task_hint, embedding_vec))
        a8m_task = asyncio.create_task(_build_axis_8_meta(session_id))

        # Dynamic Axes (async tasks already running in background)
        dynamic_context.append(await a1_task)
        dynamic_context.append(_build_axis_2())
        dynamic_context.append(_build_axis_3())
        dynamic_context.append(_build_axis_4(session_id))
        dynamic_context.append(_build_axis_5(task_hint))
        dynamic_context.append(await a6_task)
        dynamic_context.append(_build_axis_7())

        # [SRC:axis_8] Failure Memory & Meta-Cognition Recall (P3)
        fail_str, block_signal = await a8f_task
        dynamic_context.append(await a8m_task)
        dynamic_context.append(fail_str)
        dynamic_context.append(_build_axis_14(session_id))

        # Stable Axes (Governance/Patterns)
        stable_context.append(_build_axis_9(session_id, task_hint))
        stable_context.append(_build_axis_10(agent_id))
        stable_context.append(_build_axis_11())
        stable_context.append(_build_axis_12(session_id))
        stable_context.append(_build_axis_13())
    except Exception as e:
        logger.warning(f"Gnosis: Memory Axis retrieval partially failed ({e})")

    stable_str = "\n\n".join(stable_context)
    dynamic_str = "\n\n".join(dynamic_context)

    # Pruning (Optional, but apply to combined if needed. Here we keep them separate)
    pruner = _get_pruner()
    sliced_stable = pruner.slice_context_window(stable_str, "task")  # Static part should be small
    sliced_dynamic = pruner.slice_context_window(dynamic_str, "reasoning")

    # Budget-Gate (Yeni)
    if pruner.budget_exceeded and not block_signal.get("block"):
        block_signal["block"] = True
        block_signal["reason"] = "Daily token budget exceeded"
        block_signal["fallback_model"] = "qwen3.5-4b-ud:latest"

    result = (sliced_stable, sliced_dynamic, block_signal)

    # [SRC:axis_12] Store in disk-based cache
    try:
        import hashlib

        from src.architrave.context_cache import ContextCacheStore

        hashed_key = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        disk_cache = ContextCacheStore(start_sweep=False)
        serialized_val = json.dumps(
            {
                "stable_context": sliced_stable,
                "dynamic_context": sliced_dynamic,
                "block_signal": block_signal,
            }
        )
        disk_cache.set_by_key(hashed_key, serialized_val, ttl_seconds=3600)
    except Exception as e:
        logger.warning(f"Gnosis: ContextCacheStore population failed ({e})")

    _context_cache_local[cache_key] = result
    if len(_context_cache_local) > _MAX_CACHE_ENTRIES:
        _context_cache_local.popitem(last=False)
    return result
