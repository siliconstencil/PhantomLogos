import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import record_step

logger = setup_logger(__name__)


async def refine_node(state: Any) -> dict[str, Any]:
    from cognition.sophia import run_refine
    from src.lachesis import get_output_guard

    try:
        task = state["task"]
        draft = state["draft"]
        critique = state["critique"]
        correction = state.get("partial_correction")

        if correction:
            logger.info(
                f"ergon: refine_node applying partial correction: {correction.get('error_type')}"
            )
            if isinstance(critique, dict):
                critique["partial_correction"] = correction
            else:
                critique = {"original_critique": critique, "partial_correction": correction}

        final_output = await run_refine(task, draft, critique)

        {
            "final_output": final_output,
            "memory_sync": bool(final_output),
            "partial_correction": None,
        }

        guard = get_output_guard()
        res = guard.check(final_output, agent_id="refine_node")
        if res.get("action") == "reject":
            logger.warning("ergon: refine_node REJECTED final output via OutputGuard")
            final_output = state.get("draft", "Refine failed behavioral check. Draft retained.")

        await asyncio.to_thread(record_step, state, "refine")

        # [Step 3] Centralized Knowledge Extraction (Final Scavenger)
        try:
            from src.architrave.entity_extractor import EntityExtractor

            session_id = state.get("session_id", "default")
            await asyncio.to_thread(EntityExtractor.harvest_knowledge, final_output, session_id)
        except Exception as e_ext:
            logger.warning(f"ergon: Knowledge extraction failed in refine_node ({e_ext})")

        return {
            "final_output": final_output,
            "memory_sync": bool(final_output),
            "step_index": state.get("step_index", 0) + 1,
        }
    except Exception as e:
        logger.error(f"ergon: refine_node failed ({e})", exc_info=True)
        return {"final_output": "", "memory_sync": False}
