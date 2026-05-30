# [SRC:axis_2] Clotho Orchestration Graph
import asyncio
import os

# from langgraph.checkpoint.sqlite import SqliteSaver (Removed)
import sqlite3
from collections.abc import AsyncGenerator
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.utils.logging_config import setup_logger

from .ergon import (
    anchor_inject_node,
    critique_node,
    deadlock_resolver_node,
    draft_node,
    expert_draft_node,
    negotiate_node,
    refine_node,
    reflection_node,
    tool_exec_node,
    verify_node,
    vision_node,
)
from .krisis import (
    clear_session_blacklist,
    should_after_reflection,
    should_call_tools,
    should_continue,
    should_use_tier,
)

logger = setup_logger(__name__)
NODE_TIMEOUT = float(os.getenv("ORCHESTRATOR_NODE_TIMEOUT", "60.0"))

# --- Phase 1.0.10: Resilient Shutdown Helpers ---
_checkpointer_ref = None  # SqliteSaver reference
_checkpointer_conn = None  # sqlite3.Connection reference


async def flush_checkpointer() -> None:
    """Flush the checkpoint WAL and commit transactions to Axis 13."""
    global _checkpointer_ref, _checkpointer_conn
    if _checkpointer_conn:
        try:
            # Axis 13 persistence: Commit current transaction
            _checkpointer_conn.commit()
            logger.info("orchestrator: Checkpoint WAL flushed.")
        except Exception as e:
            logger.warning(f"orchestrator: Flush failed ({e})")


async def close_checkpointer() -> None:
    """Safely flush and close the checkpointer connection."""
    global _checkpointer_ref, _checkpointer_conn
    await flush_checkpointer()
    if _checkpointer_conn:
        try:
            _checkpointer_conn.close()
            _checkpointer_ref = None
            _checkpointer_conn = None
            logger.info("orchestrator: Checkpointer closed.")
        except Exception as e:
            logger.warning(f"orchestrator: Failed to close checkpointer ({e})")


def _validate_checkpoint(state: Any) -> bool:
    """Verify structural integrity of a recovered checkpoint (Axis 13)."""
    required = {"task", "session_id", "iteration"}
    # Handle both dict and StateSnapshot (namedtuple) from LangGraph 0.2+
    if isinstance(state, dict):
        values = state.get("channel_values", state)
    else:
        values = getattr(state, "channel_values", state)

    return all(k in values for k in required) if isinstance(values, dict) else False


async def checkpoint_exists(session_id: str) -> dict | None:
    """Check if a valid checkpoint exists for the given session_id."""
    global _checkpointer_ref
    if not _checkpointer_ref:
        return None
    try:
        config = {"configurable": {"thread_id": session_id}}
        # SqliteSaver.get is sync, wrap in thread
        state = await asyncio.to_thread(_checkpointer_ref.get, config)
        if state and _validate_checkpoint(state):
            return state
    except Exception as e:
        logger.debug(f"orchestrator: Checkpoint check failed for {session_id} ({e})")
    return None


def with_timeout(node_func: Any, seconds: float = NODE_TIMEOUT) -> Any:
    """Wraps a node function with a mandatory timeout."""

    async def wrapper(state: Any) -> Any:
        try:
            return await asyncio.wait_for(node_func(state), timeout=seconds)
        except TimeoutError:
            logger.error(f"orchestrator: Node '{node_func.__name__}' timed out after {seconds}s.")
            return {"reflection_insight": f"Node timeout: {node_func.__name__}"}

    wrapper.__name__ = node_func.__name__
    return wrapper


# --- Clotho State Definition ---
class GraphState(TypedDict):
    """
    Clotho Orchestration State.
    Syncs Sophia reasoning with the 14-axis memory concept.
    """

    task: str
    draft: str
    critique: dict | Any
    final_output: str
    iteration: int
    memory_sync: bool
    session_id: str
    contract: dict | None
    image_path: str | None
    vision_analysis: str | None
    anchors: str | None
    calibrated_skills: str | None
    active_agent: str | None
    tool_calls: list[dict] | None
    tool_results: list[dict] | None
    tool_iteration: int
    ru_flow_active: bool
    ru_flow_tier: int

    selected_model_tier: str
    verification_retry: int
    reflection_insight: str | None
    partial_correction: dict | None
    l0_approved: bool
    trajectory_id: int
    step_index: int


# --- Graph Construction (Clotho) ---


def wait_for_l0(state: Any) -> dict[str, Any]:
    """Sovereign Gate: Verifies L0 approval and state integrity before proceeding."""
    logger.info("orchestrator: Sovereign Gate reached. Verifying L0 intent.")

    # Axis 13: Verify State Integrity
    if not state.get("task"):
        logger.error("orchestrator: Gate Violation - Missing task in state.")
        return {"l0_approved": False}

    # Check for L0 approval (SOTA 2026: Explicit state flag required)
    approved = state.get("l0_approved", False)
    if not approved:
        logger.warning("orchestrator: L0 Gate closed. Explicit approval flag missing.")
        return {"l0_approved": False}

    logger.info("orchestrator: L0 Gate PASSED.")
    return {"l0_approved": True}


async def finalize_node(state: Any) -> dict[str, Any]:
    """[SRC:axis_12] Final node to perform cleanup and persistence sync."""
    session_id = state.get("session_id", "default")
    trajectory_id = state.get("trajectory_id", 0) if isinstance(state, dict) else 0

    clear_session_blacklist(session_id)

    if trajectory_id:
        try:
            critique = state.get("critique", {}) if isinstance(state, dict) else {}
            score = critique.get("overall_score") if isinstance(critique, dict) else None
            if score is not None:
                from .ergon.koinonia import get_trajectory_store

                get_trajectory_store().finalize_session(trajectory_id, score)
        except Exception as e:
            logger.warning(f"orchestrator: trajectory finalize failed ({e})")

    try:
        from src.architrave.mcp import get_slm_client

        slm = get_slm_client()
        await slm.aclose_session(session_id=session_id)
    except Exception as e:
        logger.warning(f"orchestrator: SLM close_session failed ({e})")

    logger.info(f"orchestrator: Finalized session {session_id}.")
    return {"memory_sync": True}


def create_clotho_graph() -> Any:
    workflow = StateGraph(GraphState)  # type: ignore

    # --- Node Definitions ---
    workflow.add_node("negotiate", with_timeout(negotiate_node))
    workflow.add_node("wait_for_l0", wait_for_l0)
    workflow.add_node("anchor_inject", with_timeout(anchor_inject_node))
    workflow.add_node("vision", with_timeout(vision_node))
    workflow.add_node("draft", with_timeout(draft_node))
    workflow.add_node("expert_draft", with_timeout(expert_draft_node))
    workflow.add_node("verify_node", with_timeout(verify_node))  # AXIS 11
    workflow.add_node("tool_exec", with_timeout(tool_exec_node))
    workflow.add_node("critique", with_timeout(critique_node))
    workflow.add_node("reflection", with_timeout(reflection_node))  # AXIS 8
    workflow.add_node("refine", with_timeout(refine_node))
    workflow.add_node("deadlock_resolver", with_timeout(deadlock_resolver_node))
    workflow.add_node("finalize", finalize_node)

    # --- Edge Flow ---
    workflow.set_entry_point("negotiate")

    workflow.add_edge("negotiate", "wait_for_l0")

    def check_approval(state: Any) -> Any:
        if not state.get("l0_approved", False):
            logger.error(
                "orchestrator: Sovereign Block - L0 Approval is missing. Terminating flow."
            )
            return END
        return should_use_tier(state)

    workflow.add_conditional_edges(
        "wait_for_l0",
        check_approval,
        {
            "ultra_light": "anchor_inject",
            "light": "anchor_inject",
            "standard": "anchor_inject",
            "expert": "anchor_inject",
            "expert_fallback": "anchor_inject",
            END: END,
        },
    )

    def route_after_inject(state: Any) -> str:
        if state.get("image_path"):
            return "vision"
        return should_use_tier(state)

    workflow.add_conditional_edges(
        "anchor_inject",
        route_after_inject,
        {
            "vision": "vision",
            "ultra_light": "draft",
            "light": "draft",
            "standard": "draft",
            "expert": "expert_draft",
            "expert_fallback": "expert_draft",
        },
    )

    workflow.add_conditional_edges(
        "vision",
        should_use_tier,
        {
            "ultra_light": "draft",
            "light": "draft",
            "standard": "draft",
            "expert": "expert_draft",
            "expert_fallback": "expert_draft",
        },
    )

    # All drafts MUST pass through verification
    workflow.add_edge("draft", "verify_node")
    workflow.add_edge("expert_draft", "verify_node")

    workflow.add_conditional_edges(
        "verify_node",
        should_call_tools,
        {
            "ultra_light": "critique",
            "tool_exec": "tool_exec",
            "critique": "critique",
            "draft": "draft",
            "expert_draft": "expert_draft",
        },
    )

    workflow.add_edge("tool_exec", "critique")

    workflow.add_conditional_edges(
        "critique",
        should_continue,
        {
            "draft": "draft",
            "expert_draft": "expert_draft",
            "reflection": "reflection",
            "deadlock_resolver": "deadlock_resolver",
        },
    )

    workflow.add_conditional_edges(
        "deadlock_resolver",
        should_use_tier,
        {"light": "draft", "standard": "draft", "expert": "expert_draft"},
    )

    workflow.add_conditional_edges(
        "reflection",
        should_after_reflection,
        {"refine": "refine", "draft": "draft", "expert_draft": "expert_draft", "end": "finalize"},
    )

    workflow.add_edge("refine", "finalize")
    workflow.add_edge("finalize", END)

    # Axis 13: Persistence Layer (LangGraph Checkpointer)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "data", "langgraph_checkpoints.sqlite")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # [Sovereign Patch] Patch SqliteSaver to support async calls via sync fallback
        # This prevents NotImplementedError while avoiding AsyncSqliteSaver lifecycle issues
        if not hasattr(SqliteSaver, "_patched"):

            async def aget_tuple_patched(self: Any, config: Any) -> Any:
                return await asyncio.to_thread(self.get_tuple, config)

            SqliteSaver.aget_tuple = aget_tuple_patched

            async def aput_patched(
                self: Any, config: Any, checkpoint: Any, metadata: Any, new_versions: Any
            ) -> Any:
                return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

            SqliteSaver.aput = aput_patched

            async def alist_patched(
                self: Any, config: Any, *, filter: Any = None, before: Any = None, limit: Any = None
            ) -> AsyncGenerator[Any, None]:
                items = await asyncio.to_thread(
                    self.list, config, filter=filter, before=before, limit=limit
                )
                for item in items:
                    yield item

            SqliteSaver.alist = alist_patched

            async def aput_writes_patched(
                self: Any, config: Any, writes: Any, task_id: Any, task_path: str = ""
            ) -> Any:
                return await asyncio.to_thread(self.put_writes, config, writes, task_id, task_path)

            SqliteSaver.aput_writes = aput_writes_patched

            SqliteSaver._patched = True
            logger.info("orchestrator: SqliteSaver patched for Async compatibility.")

        # Axis 13: Using SqliteSaver (Sync) with persistent connection
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        checkpointer = SqliteSaver(conn)
        checkpointer.setup()

        # Verify tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        logger.info(
            f"orchestrator: Checkpointer (Patched Sync) initialized at {db_path}. Tables: {tables}"
        )

        # --- Phase 1.0.10: Set global references for graceful shutdown ---
        global _checkpointer_ref, _checkpointer_conn
        _checkpointer_ref = checkpointer
        _checkpointer_conn = conn

        return workflow.compile(checkpointer=checkpointer, interrupt_before=["wait_for_l0"])
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.critical(
            f"orchestrator: CRITICAL FAILURE - Failed to initialize checkpointer ({e}). Axis 13 persistence is mandatory.",
            exc_info=True,
        )
        raise RuntimeError("System integrity violation: Axis 13 persistence failure.") from e


def should_vision_run(state: Any) -> str:
    """Router: Skips vision_node if no image_path is present in the state."""
    if state.get("image_path"):
        return "vision"
    return "critique"


if __name__ == "__main__":

    async def test_clotho() -> None:
        app = create_clotho_graph()
        initial_state = {
            "task": "Create a high-performance Python decorator for logging execution time.",
            "iteration": 0,
            "memory_sync": False,
            "image_path": None,
            "session_id": "test_session_decoupling",
        }

        logger.info("Clotho: Starting Orchestration Graph...")
        config = {"configurable": {"thread_id": "test_session_decoupling"}}
        async for event in app.astream(initial_state, config=config):
            if isinstance(event, dict):
                for node, values in event.items():
                    sync = values.get("memory_sync", "N/A") if isinstance(values, dict) else "N/A"
                    logger.info(f"  [Node: {node}] sync={sync} completed.")

    asyncio.run(test_clotho())
