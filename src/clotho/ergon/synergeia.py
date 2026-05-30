import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import record_step

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

    _MCP_PREFIXES = (  # noqa: N806
        "mcp_slm_",
        "kg-mem_",
        "fetch_",
        "playwright_",
        "filesystem_",
        "sequentialthinking_",
    )
    _BASE_TOOLS = {  # noqa: N806
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
    }

    def _is_allowed(t: str) -> bool:
        return t in _BASE_TOOLS or any(t.startswith(p) for p in _MCP_PREFIXES)

    try:
        from src.clotho.agent_loader import AgentRegistry

        reg = AgentRegistry.get_instance()
        agent = reg.get(agent_id)
        whitelist = set(agent.tools if agent else [])
    except Exception as e:
        logger.error(f"ergon: tool_exec_node agent load failed ({e})")
        whitelist = set()

    READ_ONLY_TOOLS = {  # noqa: N806
        "ls",
        "semantic",
        "report",
        "vram",
        "vision",
        "verify",
        "prune",
        "mcp_slm_recall",
        "mcp_slm_search",
        "mcp_slm_get_status",
        "kg-mem_search_nodes",
        "kg-mem_read_graph",
        "kg-mem_open_nodes",
        "fetch_fetch",
        "filesystem_read_file",
        "filesystem_list_directory",
        "filesystem_read_multiple_files",
        "filesystem_search_files",
        "filesystem_get_file_info",
    }
    bridge = ToolBridge(session_id, agent_id=agent_id)
    new_results = []

    # Separate calls into Parallel (Read-Only) and Sequential (Side-Effect)
    parallel_calls = []
    sequential_calls = []

    priority_tools = set()
    if needs.get("needs_search"):
        priority_tools.update({"semantic", "report"})
    if needs.get("needs_vision"):
        priority_tools.add("vision")
    if needs.get("needs_file_ops"):
        priority_tools.update({"write_file", "replace_content", "run_code"})

    for call in tool_calls:
        tool = call.get("tool")
        if tool not in whitelist and not _is_allowed(tool):
            new_results.append(
                {"tool": tool, "input": call.get("input"), "output": "Error: Unauthorized."}
            )
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
                    logger.warning(
                        f"ergon: Tool '{tool_name}' failed (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
        return f"Error after {max_retries} retries: {last_err}"

    # 1) Parallel Execution (Axis 6: Parallel Muscle)
    if parallel_calls:
        logger.info(f"ergon: Parallel execution for {len(parallel_calls)} tools.")
        tasks = [execute_with_retry(c.get("tool"), c.get("input")) for c in parallel_calls]
        results = await asyncio.gather(*tasks)
        for call, output in zip(parallel_calls, results, strict=False):
            new_results.append(
                {"tool": call.get("tool"), "input": call.get("input"), "output": output}
            )

    # 2) Sequential Execution (Side-Effect preservation)
    for call in sequential_calls:
        tool, arg = call.get("tool"), call.get("input")
        output = await execute_with_retry(tool, arg)
        new_results.append({"tool": tool, "input": arg, "output": output})

        # Pillar 3: Debounce Pattern
        if tool in ("write_file", "replace_content") and output and "Error" not in str(output):
            target_file = (
                (arg.get("TargetFile") or arg.get("target_file")) if isinstance(arg, dict) else None
            )
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
        from cognition.sophia.hephaestus import get_episodic

        get_episodic().log(
            session_id=session_id,
            agent_id=agent_id,
            action="tool_execution",
            detail=f"Executed {len(new_results)} tools (Parallel: {len(parallel_calls)}).",
            outcome="success",
        )
    except Exception as le:
        logger.warning(f"ergon: Failed to log tool episode ({le})")

    # Centralized Mnemosyne Hypergraph edge addition
    try:
        import os

        from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
        from cognition.mnemosyne.hypergraph_store import HypergraphStore

        tools_used = ",".join(
            list(set([res.get("tool") for res in new_results if res.get("tool")]))
        )

        nodes = [
            HypernodeRef(
                axis_id=1,
                entity_type="episodic",
                entity_key=session_id,
                label=f"Exec: {tools_used[:30]}",
            ),
            HypernodeRef(
                axis_id=2, entity_type="procedural", entity_key=agent_id, label=f"Tools: {agent_id}"
            ),
        ]

        for res in new_results:
            tool = res.get("tool")
            arg = res.get("input")
            if tool in ("write_file", "replace_content") and isinstance(arg, dict):
                target_file = arg.get("TargetFile") or arg.get("target_file")
                if target_file:
                    nodes.append(
                        HypernodeRef(
                            axis_id=5,
                            entity_type="module",
                            entity_key=os.path.basename(target_file),
                            label=os.path.basename(target_file),
                        )
                    )
                    break

        edge = Hyperedge(nodes=nodes, relation_type="tool_execution_flow", weight=1.0)
        HypergraphStore().add_edge(edge)
        logger.info(
            f"HypergraphStore: Added tool execution hyperedge {edge.edge_id} connecting Axes 1, 2, 5."
        )
    except Exception as e_hg:
        logger.warning(f"ergon: Hypergraph update failed in tool_exec_node ({e_hg})")

    await asyncio.to_thread(record_step, state, "tool_exec")
    return {
        "tool_results": tool_results + new_results,
        "tool_iteration": iteration + 1,
        "memory_sync": True,
    }
