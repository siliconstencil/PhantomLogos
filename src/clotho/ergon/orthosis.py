from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def refine_node(state: Any):
    from cognition.sophia import run_refine

    try:
        task = state["task"]
        draft = state["draft"]
        critique = state["critique"]
        correction = state.get("partial_correction")

        if correction:
            logger.info(
                f"ergon: refine_node applying partial correction: {correction.get('error_type')}"
            )
            # Guide refinement with the correction hint
            if isinstance(critique, dict):
                critique["partial_correction"] = correction
            else:
                critique = {"original_critique": critique, "partial_correction": correction}

        final_output = await run_refine(task, draft, critique)

        # Clear partial correction after use to prevent loops
        result = {
            "final_output": final_output,
            "memory_sync": bool(final_output),
            "partial_correction": None,
        }
        from src.lachesis import get_output_guard

        guard = get_output_guard()
        res = guard.check(final_output, agent_id="refine_node")
        if res.get("action") == "reject":
            logger.warning("ergon: refine_node REJECTED final output via OutputGuard")
            final_output = state.get("draft", "Refine failed behavioral check. Draft retained.")

        return {"final_output": final_output, "memory_sync": bool(final_output)}
    except Exception as e:
        logger.error(f"ergon: refine_node failed ({e})", exc_info=True)
        return {"final_output": "", "memory_sync": False}
