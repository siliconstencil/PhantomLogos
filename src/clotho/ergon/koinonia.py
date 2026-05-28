from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# --- Internal Helpers ---

_TRAJECTORY_STORE = None


def _get_trajectory_store():
    global _TRAJECTORY_STORE
    if _TRAJECTORY_STORE is None:
        from cognition.mnemosyne.trajectory_store import TrajectoryStore

        _TRAJECTORY_STORE = TrajectoryStore()
    return _TRAJECTORY_STORE


def record_step(state: dict | Any, node_name: str) -> None:
    trajectory_id = state.get("trajectory_id", 0) if isinstance(state, dict) else 0
    session_id = state.get("session_id", "default") if isinstance(state, dict) else "default"
    if not trajectory_id:
        return
    step_index = state.get("step_index", 0) + 1 if isinstance(state, dict) else 0

    critique = state.get("critique", {}) if isinstance(state, dict) else {}
    score = critique.get("overall_score") if isinstance(critique, dict) else None
    tier = state.get("ru_flow_tier", 2) if isinstance(state, dict) else 2
    model_tier = state.get("selected_model_tier", "") if isinstance(state, dict) else ""
    flaws = critique.get("flaws") if isinstance(critique, dict) else None

    # Axis 4 (Temporal Metrics) write path activation
    try:
        from cognition.mnemosyne.temporal_store import TemporalStore

        temp_store = TemporalStore()
        temp_store.record(
            session_id=session_id,
            event_type=f"node.{node_name}",
            event_key=f"traj_{trajectory_id}.step_{step_index}",
            model_name=model_tier,
            latency_ms=state.get("latency_ms", 0.0) if isinstance(state, dict) else 0.0,
            tokens_used=state.get("tokens_used", 0) if isinstance(state, dict) else 0,
        )
    except Exception as e:
        logger.debug(f"record_step: TemporalStore record skipped ({e})")

    store = _get_trajectory_store()
    store.record_step(
        session_id=session_id,
        trajectory_id=trajectory_id,
        step_index=step_index,
        node_name=node_name,
        score=score,
        tier=tier,
        model_tier=model_tier,
    )

    _feed_slm_trajectory_step(session_id, node_name, score, tier, model_tier, step_index, flaws)


def _feed_slm_trajectory_step(
    _session_id: str,
    node_name: str,
    score: float | None,
    _tier: int,
    model_tier: str,
    step_index: int,
    flaws: Any,
) -> None:
    try:
        from src.architrave.mcp import get_slm_client

        slm = get_slm_client()
        if not slm.health():
            logger.warning("_feed_slm_trajectory_step: SLM unhealthy, skipping.")
            return
        if score is not None:
            clamped_score = max(0.0, min(1.0, score))
            reward = round((clamped_score - 0.5) * 2, 4)
        else:
            reward = 0.0
        try:
            slm.remember(
                {
                    "text": f"OTL Trajectory Step: {node_name} | Score: {score} | Reward: {reward} | Tier: {model_tier}",
                    "metadata": {
                        "category": "trajectory",
                        "node_name": node_name,
                        "model_tier": model_tier,
                        "reward": reward,
                        "score": score,
                        "step_index": step_index,
                        "flaws": flaws or [],
                    },
                    "axis_id": 6,
                    "agent_id": "clotho",
                },
                table_name="trajectory_memory",
            )
        except Exception as e:
            logger.warning(f"_feed_slm_trajectory_step: SLM remember failed ({e})")
    except Exception as e:
        logger.warning(f"_feed_slm_trajectory_step: SLM feed failed ({e})")


async def _verify_draft_sync() -> bool:
    """Verify that GoalStore and EpisodicStore persisted the draft."""
    try:
        from cognition.mnemosyne.episodic_store import EpisodicStore
        from cognition.mnemosyne.goal_store import GoalStore

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
