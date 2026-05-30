# [SRC:axis_11] LangGraph node for Z3 formal verification of graph transitions
from src.lachesis.verifiers.graph_verifier import GraphVerifier
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def graph_verify_node(state: dict) -> dict:
    """Runs Z3 formal verification on LangGraph transition invariants after verify_node.
    Checks red zone gates, deadlock resolver pre/post-conditions, and error path invariants.
    Stores results in graph_verification state field.
    """
    logger.info("graph_verify_node: Starting Z3 formal verification of graph transitions.")

    verifier = GraphVerifier()
    old_state = {}

    overall_score = (
        state.get("critique", {}).get("overall_score", 1.0)
        if isinstance(state.get("critique"), dict)
        else 1.0
    )
    verification_retry = state.get("verification_retry", 0)

    if overall_score < 0.4 or verification_retry >= 3:
        logger.warning(
            f"graph_verify_node: Red zone detected (score={overall_score}, retry={verification_retry})"
        )

    try:
        results = await verifier.run_all(state, old_state)
    except Exception as e:
        logger.error(f"graph_verify_node: Z3 verification failed ({e})")
        return {"graph_verification": {"status": "error", "error": str(e)}}

    all_valid = all(r.get("is_valid", False) for r in results.values() if isinstance(r, dict))

    if not all_valid:
        failed = [
            k for k, v in results.items() if isinstance(v, dict) and not v.get("is_valid", False)
        ]
        logger.warning(f"graph_verify_node: Invariant violations detected: {failed}")
        return {
            "graph_verification": {
                "status": "violation",
                "results": results,
                "failed_checks": failed,
            }
        }

    logger.info(f"graph_verify_node: All Z3 invariants satisfied ({len(results)} checks passed).")
    return {
        "graph_verification": {
            "status": "passed",
            "results": results,
        }
    }
