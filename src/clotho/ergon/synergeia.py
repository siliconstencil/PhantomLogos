import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def tool_exec_node(state: Any):
    """Executes tool calls requested by Sophia with Parallel Muscle and Error Recovery."""

    from src.clotho.bridge import ToolBridge
    from src.clotho.mapper_bridge import schedule_remap

    tool_calls = state.get("tool_calls", [])
    tool_results = state.get("tool_results", []) or []
    iteration = state.get("tool_iteration", 0)

    active_agent = state.get("active_agent", {})
    agent_id = active_agent.get("id", "sophia")
    session_id = state.get("session_id", "default")
    task = state.get("task", "")

    # Phase 1.0.29: Local Tool Needs Classification (FunctionGemma)
    try:
        from src.clotho.krisis import classify_tool_needs
        needs = await classify_tool_needs(task)
        logger.info(f"ergon: Task classification: {needs}")
    except Exception as e:
        logger.warning(f"ergon: Classification failed ({e})")
        needs = {"needs_file_ops": True, "needs_search": True, "needs_vision": True}

    try:
        from src.clotho.agent_loader import AgentRegistry

        reg = AgentRegistry.get_instance()
        agent = reg.get(agent_id)
        whitelist = set(agent.tools if agent else [])
    except Exception as e:
        logger.error(f"ergon: tool_exec_node agent load failed ({e})")
        whitelist = {"ls", "semantic", "vram", "report", "write_file", "replace_content", "run_code", "vision", "verify", "prune", "skill"}

    READ_ONLY_TOOLS = {"ls", "semantic", "report", "vram", "vision", "verify", "prune"}
    bridge = ToolBridge(session_id, agent_id=agent_id)
    new_results = []

    # Separate calls into Parallel (Read-Only) and Sequential (Side-Effect)
    parallel_calls = []
    sequential_calls = []
    
    priority_tools = set()
    if needs.get("needs_search"): priority_tools.update({"semantic", "report"})
    if needs.get("needs_vision"): priority_tools.add("vision")
    if needs.get("needs_file_ops"): priority_tools.update({"write_file", "replace_content", "run_code"})

    for call in tool_calls:
        tool = call.get("tool")
        if tool not in whitelist:
            new_results.append({"tool": tool, "input": call.get("input"), "output": "Error: Unauthorized."})
            continue
        
        if tool in READ_ONLY_TOOLS:
            # Sort prioritized read-only tools to the front
            if tool in priority_tools:
                parallel_calls.insert(0, call)
            else:
                parallel_calls.append(call)
        else:
            # Sort prioritized side-effect tools to the front
            if tool in priority_tools:
                sequential_calls.insert(0, call)
            else:
                sequential_calls.append(call)

    async def execute_with_retry(tool_name, tool_input, max_retries=2):
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                res = await bridge.execute(tool_name, tool_input)
                return res.get("output") if isinstance(res, dict) else str(res)
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    wait = 0.5 * (attempt + 1)
                    logger.warning(f"ergon: Tool '{tool_name}' failed (attempt {attempt+1}/{max_retries+1}). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
        return f"Error after {max_retries} retries: {last_err}"

    # 1) Parallel Execution (Axis 6: Parallel Muscle)
    if parallel_calls:
        logger.info(f"ergon: Parallel execution for {len(parallel_calls)} tools.")
        tasks = [execute_with_retry(c.get("tool"), c.get("input")) for c in parallel_calls]
        results = await asyncio.gather(*tasks)
        for call, output in zip(parallel_calls, results):
            new_results.append({"tool": call.get("tool"), "input": call.get("input"), "output": output})

    # 2) Sequential Execution (Side-Effect preservation)
    for call in sequential_calls:
        tool, arg = call.get("tool"), call.get("input")
        output = await execute_with_retry(tool, arg)
        new_results.append({"tool": tool, "input": arg, "output": output})

        # Pillar 3: Debounce Pattern
        if tool in ("write_file", "replace_content") and output and "Error" not in str(output):
            target_file = (arg.get("TargetFile") or arg.get("target_file")) if isinstance(arg, dict) else None
            if target_file:
                await schedule_remap(target_file)

    # Layer 3: Scavenger Mode (Axis 6)
    try:
        from src.architrave.entity_extractor import EntityExtractor
        for res in new_results:
            text = res.get("output", "")
            if len(text) > 10:
                await asyncio.to_thread(EntityExtractor.harvest_knowledge, text, session_id)
    except Exception as e_scav:
        logger.warning(f"ergon: Scavenger failed ({e_scav})")

    # Phase 2.3: Log tool execution to episodic store
    try:
        from cognition.sophia.hephaestus import _get_episodic
        _get_episodic().log(
            session_id=session_id,
            agent_id=agent_id,
            action="tool_execution",
            detail=f"Executed {len(new_results)} tools (Parallel: {len(parallel_calls)}).",
            outcome="success",
        )
    except Exception as le:
        logger.warning(f"ergon: Failed to log tool episode ({le})")

    return {
        "tool_results": tool_results + new_results,
        "tool_iteration": iteration + 1,
        "memory_sync": True,
    }
