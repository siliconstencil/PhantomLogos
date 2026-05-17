import asyncio
import os
import signal
import uuid

from src.utils.logging_config import setup_logger

from .orchestrator import checkpoint_exists, create_clotho_graph

logger = setup_logger(__name__)

# --- Phase 1.0.10: Resilient Shutdown & Signal Management ---
_CLOTHO_GRAPH = None
_SIGNALS_REGISTERED = False
_shutdown_requested = False
_SHUTDOWN_HARD_TIMEOUT = 10  # Seconds before os._exit


def _signal_handler(sig, frame):
    """Sovereign Signal Handler: Initiates graceful shutdown sequence."""
    global _shutdown_requested
    if not _shutdown_requested:
        _shutdown_requested = True
        sig_name = signal.Signals(sig).name if hasattr(signal, "Signals") else str(sig)
        logger.warning(
            f"clotho_handoff: Signal {sig_name} received. "
            f"Graceful shutdown initiated. Current tasks will attempt cleanup."
        )


def _asyncio_exception_handler(loop, context):
    """Global asyncio loop exception handler to catch unhandled crashes."""
    exception = context.get("exception")
    message = context.get("message")

    if isinstance(exception, asyncio.CancelledError):
        from src.utils.logging_config import log_system_event

        log_system_event("WARNING", f"clotho_handoff: Task cancelled: {message}")
        return

    logger.error(f"clotho_handoff: Unhandled loop exception: {message} ({exception})")
    # Trigger shutdown flag to prevent further ingestion
    global _shutdown_requested
    _shutdown_requested = True


def _register_signals():
    """Register OS signals for Windows (SIGINT, SIGBREAK)."""
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        logger.debug("clotho_handoff: SIGINT (Ctrl+C) handler registered.")
    except (ValueError, AttributeError) as e:
        logger.warning(f"clotho_handoff: SIGINT registration failed ({e})")

    try:
        # SIGBREAK is Windows-specific (Ctrl+Break)
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, _signal_handler)
            logger.debug("clotho_handoff: SIGBREAK (Ctrl+Break) handler registered.")
    except (ValueError, AttributeError) as e:
        logger.warning(f"clotho_handoff: SIGBREAK registration failed ({e})")

    # Hook into the event loop exception handler
    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(_asyncio_exception_handler)
        logger.debug("clotho_handoff: Asyncio loop exception handler registered.")
    except Exception as e:
        logger.warning(f"clotho_handoff: Loop handler registration failed ({e})")


async def _emergency_cleanup():
    """Final flush and resource release before hard process termination."""
    from .orchestrator import close_checkpointer, flush_checkpointer

    logger.warning("clotho_handoff: Emergency cleanup (Axis 13) initiated.")

    # Surgical flush of checkpointer WAL
    await flush_checkpointer()
    await close_checkpointer()

    logger.warning(f"clotho_handoff: Shutdown complete. Force exit in {_SHUTDOWN_HARD_TIMEOUT}s.")
    await asyncio.sleep(_SHUTDOWN_HARD_TIMEOUT)
    os._exit(0)


async def clotho_handoff(task_description: str, session_id: str | None = None):
    """
    ControlFlow-compatible hand-off logic.
    Breaks down user requests and delegates to Clotho (LangGraph).
    """
    global _CLOTHO_GRAPH, _SIGNALS_REGISTERED, _shutdown_requested

    # 1) Shutdown check: Reject new ingestion if termination is in progress
    if _shutdown_requested:
        logger.warning("clotho_handoff: Rejecting new task - System is shutting down.")
        return "[Shutdown] System is shutting down."

    # 2) Signal Registration: Ensure handlers are active (once per process)
    if not _SIGNALS_REGISTERED:
        _register_signals()
        _SIGNALS_REGISTERED = True

    logger.info(f"Clotho: Initializing Task Hand-off for: {task_description[:80]}")
    actual_session_id = session_id or str(uuid.uuid4())

    # [Phase 1.0.21] Tone Analysis (Axis 9) Restoration
    try:
        from cognition.mnemosyne.tone_store import ToneStore

        ToneStore().record_tone(session_id=actual_session_id, message=task_description)
    except Exception:
        pass

    if _CLOTHO_GRAPH is None:
        _CLOTHO_GRAPH = create_clotho_graph()
    app = _CLOTHO_GRAPH

    # 3) Checkpoint Recovery: Log if a previous state exists for this session
    recovered_state = await checkpoint_exists(actual_session_id)
    if recovered_state:
        # Phase 1.0.10: Found valid checkpoint. Logging for future resume support.
        logger.info(f"clotho_handoff: Recovered valid checkpoint (Axis 13) for {actual_session_id}")

    initial_state = {
        "task": task_description,
        "session_id": actual_session_id,
        "iteration": 0,
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
        "spatial_dirty": False,
        "selected_model_tier": "primary",
    }
    logger.info(f"Clotho: Session {actual_session_id} initialized.")
    config = {"configurable": {"thread_id": actual_session_id}}
    try:
        if recovered_state:
            result = await asyncio.wait_for(app.ainvoke(None, config=config), timeout=120.0)
        else:
            result = await asyncio.wait_for(app.ainvoke(initial_state, config=config), timeout=120.0)

        # Basarili gorev sonrasi control_handoff.py'ye positive reward (1.0 success score) ekle!
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            MetaCognitionStore().adjust_reliability(
                agent_id="sophia",
                delta=1.0,
                violation_type="",
                session_id=actual_session_id,
            )
        except Exception as e_reward:
            logger.warning(
                f"clotho_handoff: Failed to award success reliability to sophia ({e_reward})"
            )

        return result.get("final_output", "")
    except asyncio.CancelledError:
        # Triggered by signal handler or external cancellation
        logger.info(f"clotho_handoff: Task {actual_session_id} cancelled.")
        raise
    except TimeoutError:
        logger.error(f"Clotho: Task execution timed out after 120s for session {actual_session_id}")
        return "[Clotho Timeout] The task took too long to complete. Please try a simpler request or check system health."
    except Exception as e:
        logger.error(
            f"Clotho: Hand-off failed for session {actual_session_id} ({e})", exc_info=True
        )
        # [Phase 1.0.21] Meta-Cognition (Axis 8) Restoration
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            MetaCognitionStore().record_experience(
                agent_id="sophia",
                session_id=actual_session_id,
                task_pattern="general",
                success=False,
                quality=0.0,
            )
        except Exception:
            pass
        return f"[Clotho Error] {e!s}"
    finally:
        # Ensure cleanup if shutdown was requested during execution
        if _shutdown_requested:
            await _emergency_cleanup()


if __name__ == "__main__":
    import asyncio

    async def test():
        final_res = await clotho_handoff(
            "Design a modular authentication system for a FastAPI app."
        )
        print(f"\nClotho Final Handoff Result:\n{final_res[:200]}...")

    asyncio.run(test())
