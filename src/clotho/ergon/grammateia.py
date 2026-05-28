import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import _verify_draft_sync, record_step

logger = setup_logger(__name__)


async def draft_node(state: Any):
    from cognition.sophia import ReasoningState, run_draft

    raw_task = state["task"]
    vision = state.get("vision_analysis", "")
    anchors = state.get("anchors", "")

    # AXIS 3: XML Structured Prompting (Madde 8)
    formatted_task = "<TASK>\n" + raw_task + "\n</TASK>\n"

    if anchors:
        formatted_task += f"\n<CONTEXT>\n{anchors}\n</CONTEXT>\n"

    if vision:
        formatted_task += f"\n<VISION_ANALYSIS>\n{vision[:2000]}\n</VISION_ANALYSIS>\n"

    tool_results = state.get("tool_results", [])
    if tool_results:
        tool_ctx = "\n<TOOL_RESULTS>\n"
        for tr in tool_results:
            tool_ctx += f"- Tool: {tr.get('tool')}\n  Output: {str(tr.get('output'))[:1000]}\n---\n"
        tool_ctx += "</TOOL_RESULTS>\n"
        formatted_task += tool_ctx

    # AXIS 3: Few-Shot Examples for Rule Adherence (Madde 9)
    few_shot = """
<EXAMPLES>
[BAD EXAMPLE - REJECTED]
Response: "I apologize for the confusion. Here is the script [EMOJI_REDACTED]"
Reason: Violates NO APOLOGY and EMOJI_BAN rules.

[GOOD EXAMPLE - APPROVED]
Response: "The script has been updated to include the requested changes."
Reason: Deterministic, concise, no social filler.
</EXAMPLES>
"""
    formatted_task += few_shot

    sophia_state = ReasoningState(
        task=formatted_task,
        session_id=state.get("session_id", "default"),
        flags={"tier": state.get("ru_flow_tier", 2)},
    )
    try:
        res = await run_draft(sophia_state)
        draft, tool_calls = res if isinstance(res, tuple) else (res, [])

        error_msg = None
        if draft.startswith("[SYSTEM GUARD]"):
            error_msg = draft
            draft = ""
            tool_calls = []

        sync_ok = await _verify_draft_sync()
        await asyncio.to_thread(record_step, state, "draft")
        return {
            "draft": draft,
            "tool_calls": tool_calls,
            "error_message": error_msg,
            "iteration": state.get("iteration", 0) + 1,
            "memory_sync": sync_ok,
        }
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: draft_node failed ({e})", exc_info=True)
        return {"draft": "", "iteration": state.get("iteration", 0) + 1, "memory_sync": False}


async def expert_draft_node(state: Any):
    from cognition.sophia import run_draft

    try:
        res = await run_draft(state, thinking=True)
        draft, tool_calls = res if isinstance(res, tuple) else (res, [])

        error_msg = None
        if draft.startswith("[SYSTEM GUARD]"):
            error_msg = draft
            draft = ""
            tool_calls = []

        await asyncio.to_thread(record_step, state, "expert_draft")
        return {
            "draft": draft,
            "tool_calls": tool_calls,
            "error_message": error_msg,
            "memory_sync": True,
            "iteration": state.get("iteration", 0) + 1,
        }

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: expert_draft_node failed ({e})", exc_info=True)
        await asyncio.to_thread(record_step, state, "expert_draft")
        return {
            "draft": f"[Expert Error: {e}]",
            "memory_sync": False,
            "iteration": state.get("iteration", 0) + 1,
        }
