import os
import asyncio
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# --- Internal Helpers ---

async def _verify_draft_sync() -> bool:
    """Verify that GoalStore and EpisodicStore persisted the draft."""
    try:
        from cognition.mnemosyne.goal_store import GoalStore
        from cognition.mnemosyne.episodic_store import EpisodicStore
        goals = GoalStore()
        active = goals.list_active(limit=1)
        episodes = EpisodicStore()
        recent = episodes.recent("local_session", limit=1)
        ok = bool(active) and bool(recent)
        if not ok:
            logger.warning("memory_sync: Draft stores verification failed")
        return ok
    except Exception as e:
        logger.error(f"memory_sync: draft verify error ({e})", exc_info=True)
        return False

async def _verify_critique_sync() -> bool:
    """Verify that ProceduralStore persisted the critique."""
    try:
        from cognition.mnemosyne.procedural_store import ProceduralStore
        proc = ProceduralStore()
        tools = proc.best_tool("critique")
        if tools:
            return True
        logger.warning("memory_sync: Critique store verification failed")
        return False
    except Exception as e:
        logger.error(f"memory_sync: critique verify error ({e})", exc_info=True)
        return False
