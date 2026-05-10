import os
import time
import asyncio
from typing import Optional, Any
from collections import OrderedDict
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client
from ..hephaestus import _get_sweeper, _get_loader, _get_pruner

logger = setup_logger(__name__)

_context_cache_local = OrderedDict()
_MAX_CACHE_ENTRIES = 20

async def get_dynamic_context(agent_id: str, task_hint: str = "", session_id: str = "default") -> tuple[str, str, dict]:
    """
    [SRC:axis_12] Returns a split context: (stable_context, dynamic_context, block_signal).
    Stable context is suitable for System Instruction (Implicit Caching).
    Dynamic context contains task-specific and rapidly changing axes.
    """
    cache_key = f"{agent_id}:{task_hint[:40]}:{session_id}"
    if cache_key in _context_cache_local:
        _context_cache_local.move_to_end(cache_key)
        return _context_cache_local[cache_key]
    
    anchor_path = "data/ankyra_anchor.md"
    anchor = ""
    if os.path.exists(anchor_path):
        with open(anchor_path, "r", encoding="utf-8") as f:
            anchor = f.read()
    
    stable_context = [f"### PROJECT ANCHOR (ANKYRA)\n{anchor}"]
    dynamic_context = []
    block_signal = {"block": False, "reason": None}
    embedding_vec = None

    if task_hint:
        try:
            _get_sweeper().check_and_sweep(_get_loader())
            from src.clotho.activity import ActivityMonitor
            import numpy as np
            ActivityMonitor().increment()
            from src.architrave.model_registry import resolve_local_model
            client = get_ollama_client()
            try:
                embedding_model = resolve_local_model("embedding")
                resp = await asyncio.wait_for(
                    client.embeddings(model=embedding_model, prompt=task_hint),
                    timeout=5.0
                )
                # Phase 11.21.x: Ollama returns Pydantic EmbeddingsResponse, not dict
                embedding_vec = np.array(resp.embedding)[:256]
            except Exception as e:
                logger.warning(f"Gnosis: Embedding extraction failed ({e})")
            finally:
                ActivityMonitor().decrement()
        except Exception: pass

    # --- 14-Axis Context Building ---
    from .axis_1_episodic import _build_axis_1
    from .axis_2_procedural import _build_axis_2
    from .axis_3_goals import _build_axis_3
    from .axis_4_temporal import _build_axis_4
    from .axis_5_spatial import _build_axis_5
    from .axis_6_semantic import _build_axis_6
    from .axis_7_operational import _build_axis_7
    from .axis_8_meta import _build_axis_8_meta, _build_axis_8_failures
    from .axis_9_tone import _build_axis_9
    from .axis_10_rational import _build_axis_10
    from .axis_11_verify import _build_axis_11
    from .axis_12_cache import _build_axis_12
    from .axis_13_patterns import _build_axis_13
    from .axis_14_visual import _build_axis_14

    try:
        # Dynamic Axes (Session/Task specific)
        dynamic_context.extend(_build_axis_1(session_id))
        dynamic_context.extend(_build_axis_2())
        dynamic_context.extend(_build_axis_3())
        dynamic_context.extend(_build_axis_4(session_id))
        dynamic_context.extend(_build_axis_5(task_hint))
        dynamic_context.extend(await _build_axis_6(task_hint, session_id, embedding_vec))
        dynamic_context.extend(_build_axis_7())
        
        fail_lines, block_signal = await _build_axis_8_failures(task_hint, embedding_vec)
        dynamic_context.extend(_build_axis_8_meta())
        dynamic_context.extend(fail_lines)
        dynamic_context.extend(_build_axis_14(session_id))

        # Stable Axes (Governance/Patterns)
        stable_context.extend(_build_axis_9(session_id, task_hint))
        stable_context.extend(_build_axis_10(agent_id))
        stable_context.extend(_build_axis_11())
        stable_context.extend(_build_axis_12())
        stable_context.extend(_build_axis_13())
    except Exception as e:
        logger.warning(f"Gnosis: Memory Axis retrieval partially failed ({e})")
    
    stable_str = "\n\n".join(stable_context)
    dynamic_str = "\n\n".join(dynamic_context)

    # Pruning (Optional, but apply to combined if needed. Here we keep them separate)
    pruner = _get_pruner()
    sliced_stable = pruner.slice_context_window(stable_str, "task") # Static part should be small
    sliced_dynamic = pruner.slice_context_window(dynamic_str, "reasoning")
    
    result = (sliced_stable, sliced_dynamic, block_signal)
    _context_cache_local[cache_key] = result
    if len(_context_cache_local) > _MAX_CACHE_ENTRIES:
        _context_cache_local.popitem(last=False)
    return result
