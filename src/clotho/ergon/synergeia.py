from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def tool_exec_node(state: Any):
    """Executes tool calls requested by Sophia with True Debounce Remapping."""

    from src.clotho.bridge import ToolBridge
    from src.clotho.mapper_bridge import schedule_remap

    tool_calls = state.get("tool_calls", [])
    tool_results = state.get("tool_results", []) or []
    iteration = state.get("tool_iteration", 0)

    active_agent = state.get("active_agent", {})
    agent_id = active_agent.get("id", "sophia")

    try:
        from src.clotho.agent_loader import AgentRegistry

        agent_def = AgentRegistry.get_instance().get(agent_id)
        whitelist = (
            agent_def.tools
            if agent_def
            else [
                "ls",
                "semantic",
                "vram",
                "report",
                "write_file",
                "replace_content",
                "run_code",
                "vision",
                "verify",
                "prune",
                "skill",
            ]
        )
    except Exception as e:
        logger.error(f"ergon: tool_exec_node agent definition load failed ({e})")
        whitelist = [
            "ls",
            "semantic",
            "vram",
            "report",
            "write_file",
            "replace_content",
            "run_code",
            "vision",
            "verify",
            "prune",
            "skill",
        ]

    bridge = ToolBridge(state.get("session_id", "default"), agent_id=agent_id)
    new_results = []
    for call in tool_calls:
        tool, arg = call.get("tool"), call.get("input")
        if tool not in whitelist:
            new_results.append({"tool": tool, "input": arg, "output": "Error: Unauthorized."})
            continue
        try:
            res = await bridge.execute(tool, arg)
            output = res.get("output") if isinstance(res, dict) else str(res)
            new_results.append({"tool": tool, "input": arg, "output": output})

            # Pillar 3: Debounce Pattern (Duzeltme 4)
            if tool in ("write_file", "replace_content"):
                target_file = None

                if isinstance(arg, dict):
                    target_file = arg.get("TargetFile") or arg.get("target_file")

                if target_file:
                    await schedule_remap(target_file)

        except Exception as e:
            new_results.append({"tool": tool, "input": arg, "output": f"Error: {e!s}"})

    # Phase 2.3: Log tool execution to episodic store
    try:
        from cognition.sophia.hephaestus import _get_episodic

        _get_episodic().log(
            session_id=state.get("session_id", "default"),
            agent_id=agent_id,
            action="tool_execution",
            detail=f"Executed {len(new_results)} tools. Iteration: {iteration}",
            outcome="success",
        )
    except Exception as le:
        logger.warning(f"ergon: Failed to log tool episode ({le})")

    return {
        "tool_results": tool_results + new_results,
        "tool_iteration": iteration + 1,
        "tool_calls": [],
    }
