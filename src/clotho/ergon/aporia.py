from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import record_step

logger = setup_logger(__name__)


async def deadlock_resolver_node(state: Any) -> dict[str, Any]:
    """
    SOTA 2026: Logic Deadlock Resolver.
    Triggered when L3 audit repeatedly rejects a draft.
    Action: Simplifies the contract or adds clarifying constraints to resolve the spiral.
    """
    try:
        logger.warning(f"ergon: Deadlock Resolver activated for session {state.get('session_id')}")
        contract = state.get("contract", {})

        # Strategy: Constraint Relaxation
        original_threshold = contract.get("threshold", 0.7)
        # Reduce strictness slightly to allow progress
        new_threshold = max(0.5, round(original_threshold - 0.1, 2))

        contract["threshold"] = new_threshold
        if "success_criteria" not in contract:
            contract["success_criteria"] = []
        contract["success_criteria"].append(
            "DEADLOCK RESOLUTION: Threshold relaxed to bypass hallucination spiral."
        )

        record_step(state, "deadlock_resolver")
        # Reset retry and increment iteration to force a fresh perspective
        return {
            "contract": contract,
            "verification_retry": 0,
            "iteration": state.get("iteration", 0) + 1,
            "memory_sync": True,
        }
    except Exception as e:
        logger.error(f"ergon: deadlock_resolver_node failed ({e})")
        return {"memory_sync": False}
