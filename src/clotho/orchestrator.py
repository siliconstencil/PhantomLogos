# [SRC:axis_2] Clotho Orchestration Graph
import os
import asyncio
import operator
from typing import Annotated, TypedDict, List, Union, Any, Optional
from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.sqlite import SqliteSaver (Removed)
import sqlite3

from src.utils.logging_config import setup_logger
from .ergon import (
    negotiate_node, anchor_inject_node, vision_node, 
    draft_node, expert_draft_node, verify_node, 
    tool_exec_node, critique_node, refine_node, reflection_node,
    deadlock_resolver_node
)
from .krisis import (
    should_use_tier, should_call_tools, 
    should_continue, should_after_reflection
)

logger = setup_logger(__name__)

# --- Clotho State Definition ---
class GraphState(TypedDict):
    """
    Clotho Orchestration State.
    Syncs Sophia reasoning with the 13-axis memory concept.
    """
    task: str
    draft: str
    critique: Union[dict, Any]
    final_output: str
    iteration: int
    max_iterations: int
    memory_sync: Annotated[bool, operator.and_]
    session_id: str
    contract: Optional[dict]
    image_path: Optional[str]
    vision_analysis: Optional[str]
    anchors: Optional[str]
    active_agent: Optional[str]
    tool_calls: Optional[List[dict]]
    tool_results: Optional[List[dict]]
    tool_iteration: int
    ru_flow_active: bool
    ru_flow_tier: int
    ru_flow_trace: List[str]
    selected_model_tier: str
    verification_retry: int
    reflection_insight: Optional[str]
    l0_approved: bool
    spatial_context: List[str]

# --- Graph Construction (Clotho) ---

def wait_for_l0(state: Any):
    """Dummy node. Execution pauses here if l0_approved is False."""
    logger.info("orchestrator: Waiting for L0 approval (Sovereign Gate).")
    return {"l0_approved": state.get("l0_approved", False)}

def create_clotho_graph():
    workflow = StateGraph(GraphState)

    # --- Node Definitions ---
    workflow.add_node("negotiate", negotiate_node)
    workflow.add_node("wait_for_l0", wait_for_l0)
    workflow.add_node("anchor_inject", anchor_inject_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("expert_draft", expert_draft_node)
    workflow.add_node("verify_node", verify_node) # AXIS 11
    workflow.add_node("tool_exec", tool_exec_node)
    workflow.add_node("critique", critique_node)
    workflow.add_node("reflection", reflection_node) # AXIS 8
    workflow.add_node("refine", refine_node)
    workflow.add_node("deadlock_resolver", deadlock_resolver_node)

    # --- Edge Flow ---
    workflow.set_entry_point("negotiate")
    
    workflow.add_edge("negotiate", "wait_for_l0")
    
    def check_approval(state: Any):
        if not state.get("l0_approved", False):
            logger.error("orchestrator: Sovereign Block - L0 Approval is missing. Terminating flow.")
            return END
        return should_use_tier(state)

    workflow.add_conditional_edges("wait_for_l0", check_approval, {
        "ultra_light": "anchor_inject", "light": "anchor_inject", 
        "standard": "anchor_inject", "expert": "anchor_inject", "expert_fallback": "anchor_inject",
        END: END
    })
    
    def route_after_inject(state: Any):
        if state.get("image_path"):
            return "vision"
        return should_use_tier(state)

    workflow.add_conditional_edges("anchor_inject", route_after_inject, {
        "vision": "vision",
        "ultra_light": "draft", "light": "draft", "standard": "draft", 
        "expert": "expert_draft", "expert_fallback": "expert_draft"
    })
    
    workflow.add_conditional_edges("vision", should_use_tier, {
        "ultra_light": "draft", "light": "draft", "standard": "draft", 
        "expert": "expert_draft", "expert_fallback": "expert_draft"
    })
    
    # All drafts MUST pass through verification
    workflow.add_edge("draft", "verify_node")
    workflow.add_edge("expert_draft", "verify_node")
    
    workflow.add_conditional_edges("verify_node", should_call_tools, {
        "ultra_light": "critique",
        "tool_exec": "tool_exec",
        "critique": "critique",
        "draft": "draft",
        "expert_draft": "expert_draft"
    })
    
    workflow.add_edge("tool_exec", "reflection")
    
    workflow.add_conditional_edges("critique", should_continue, {
        "draft": "draft", "expert_draft": "expert_draft", "reflection": "reflection",
        "deadlock_resolver": "deadlock_resolver"
    })

    workflow.add_conditional_edges("deadlock_resolver", should_use_tier, {
        "light": "draft", "standard": "draft", "expert": "expert_draft"
    })

    workflow.add_conditional_edges("reflection", should_after_reflection, {
        "refine": "refine",
        "draft": "draft",
        "expert_draft": "expert_draft",
        "end": END
    })

    workflow.add_edge("refine", END)

    # Axis 13: Persistence Layer (LangGraph Checkpointer)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "data", "langgraph_checkpoints.sqlite")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # [Sovereign Patch] Patch SqliteSaver to support async calls via sync fallback
        # This prevents NotImplementedError while avoiding AsyncSqliteSaver lifecycle issues
        if not hasattr(SqliteSaver, "_patched"):
            import asyncio
            original_aget_tuple = SqliteSaver.aget_tuple
            async def aget_tuple_patched(self, config):
                return await asyncio.to_thread(self.get_tuple, config)
            SqliteSaver.aget_tuple = aget_tuple_patched
            
            async def aput_patched(self, config, checkpoint, metadata, new_versions):
                return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)
            SqliteSaver.aput = aput_patched
            
            async def alist_patched(self, config, *, filter=None, before=None, limit=None):
                return await asyncio.to_thread(self.list, config, filter=filter, before=before, limit=limit)
            SqliteSaver.alist = alist_patched
            
            async def aput_writes_patched(self, config, writes, task_id):
                return await asyncio.to_thread(self.put_writes, config, writes, task_id)
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
        logger.info(f"orchestrator: Checkpointer (Patched Sync) initialized at {db_path}. Tables: {tables}")
        
        return workflow.compile(checkpointer=checkpointer, interrupt_before=["wait_for_l0"])
    except Exception as e:
        logger.error(f"orchestrator: Failed to initialize checkpointer ({e}). Compiling without persistence.", exc_info=True)
        return workflow.compile(interrupt_before=["wait_for_l0"])

def should_vision_run(state: Any):
    """Router: Skips vision_node if no image_path is present in the state."""
    if state.get("image_path"):
        return "vision"
    return "critique"

if __name__ == "__main__":
    async def test_clotho():
        app = create_clotho_graph()
        initial_state = {
            "task": "Create a high-performance Python decorator for logging execution time.",
            "iteration": 0,
            "max_iterations": 2,
            "memory_sync": False,
            "image_path": None,
            "session_id": "test_session_decoupling"
        }

        logger.info("Clotho: Starting Orchestration Graph...")
        async for event in app.astream(initial_state):
            if isinstance(event, dict):
                for node, values in event.items():
                    sync = values.get("memory_sync", "N/A") if isinstance(values, dict) else "N/A"
                    logger.info(f"  [Node: {node}] sync={sync} completed.")

    asyncio.run(test_clotho())
