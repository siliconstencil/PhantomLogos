import asyncio
from .orchestrator import create_clotho_graph
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

_CLOTHO_GRAPH = None


async def clotho_handoff(task_description: str):
    """
    ControlFlow-compatible hand-off logic.
    Breaks down user requests and delegates to Clotho (LangGraph).
    """
    global _CLOTHO_GRAPH
    logger.info(f"Clotho: Initializing Task Hand-off for: {task_description[:80]}")
    import uuid
    session_id = str(uuid.uuid4())

    if _CLOTHO_GRAPH is None:
        _CLOTHO_GRAPH = create_clotho_graph()
    app = _CLOTHO_GRAPH
    initial_state = {
        "task": task_description,
        "session_id": session_id,
        "iteration": 0,
        "max_iterations": 2,
        "memory_sync": True,
        "image_path": None,
        "draft": "",
        "critique": {},
        "final_output": "",
        "anchors": "",
        "vision_analysis": "",
        "active_agent": {},
        "contract": {},
        "tool_calls": [],
        "tool_results": [],
        "tool_iteration": 0,
        "ru_flow_active": False,
        "ru_flow_tier": 2,
        "ru_flow_trace": [],
        "selected_model_tier": "primary",
    }
    logger.info(f"Clotho: Session {session_id} initialized.")
    config = {"configurable": {"thread_id": session_id}}
    try:
        result = await asyncio.wait_for(app.ainvoke(initial_state, config=config), timeout=120.0)
        return result.get("final_output", "")
    except asyncio.TimeoutError:
        logger.error(f"Clotho: Task execution timed out after 120s for session {session_id}")
        return "[Clotho Timeout] The task took too long to complete. Please try a simpler request or check system health."
    except Exception as e:
        logger.error(f"Clotho: Hand-off failed for session {session_id} ({e})", exc_info=True)
        return f"[Clotho Error] {str(e)}"


if __name__ == "__main__":
    import asyncio

    async def test():
        final_res = await clotho_handoff(
            "Design a modular authentication system for a FastAPI app."
        )
        print(f"\nClotho Final Handoff Result:\n{final_res[:200]}...")

    asyncio.run(test())
