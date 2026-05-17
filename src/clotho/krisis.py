from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

from cognition.mnemosyne.operational_store import OperationalStore
from cognition.mnemosyne.procedural_store import ProceduralStore

# Phase 11.18.4: Session-level model blacklist to handle Hallucination Penalties
BLACKLISTED_MODELS = {}  # {session_id: [model_names]}


def clear_session_blacklist(session_id: str):
    """[SRC:axis_12] Purges the model blacklist for a specific session to prevent memory leaks."""
    if session_id in BLACKLISTED_MODELS:
        del BLACKLISTED_MODELS[session_id]
        logger.info(f"krisis: Session {session_id} model blacklist cleared.")


def get_hermes_bridge_context(session_id: str) -> str:
    """
    Fetches cross-agent context (Hermes/Observability facts) from Mnemosyne.
    Includes Axis 7 (Operational telemetry), Axis 8 (Meta-Cog reliability),
    and Axis 2 (Procedural best tools).
    """
    ctx = ""
    try:
        # -- Axis 7: Hermes + Tool events --
        op_store = OperationalStore()
        events = op_store.get_recent_logs(limit=20)
        if events:
            part = "\n\n### CROSS-AGENT SHARED MEMORY (AXIS 7):\n"
            for e in events:
                name = getattr(e, "name", "") or ""
                msg = getattr(e, "message", "") or ""
                if name.startswith("hermes.") or name.startswith("tool_bridge."):
                    part += f"- [{name}] {msg[:200]}\n"
            ctx += part

        # -- Axis 8: Agent Reliability Score --
        from cognition.mnemosyne.meta_cognition import MetaCognitionStore
        meta = MetaCognitionStore()
        rel = meta.get_reliability("sophia")
        ctx += "\n### SYSTEM RELIABILITY (AXIS 8):\n"
        ctx += f"Sophia reliability score: {rel:.2f}\n"
        if rel < 0.5:
            ctx += "WARNING: Low reliability. Conservative execution advised.\n"

        # -- Axis 2: Best performing tools --
        proc = ProceduralStore()
        for task_type in ("critique", "vision", "semantic"):
            best = proc.best_tool(task_type)
            if best:
                ctx += (
                    f"Best tool for [{task_type}]: {best[0][0]} (success rate: {best[0][1]:.0%})\n"
                )

        # -- Axis 13: OpenCode Patterns (Bridge Audit) --
        try:
            from src.architrave.opencode_store import OpenCodeStore

            opencode = OpenCodeStore()
            patterns = opencode.get_cross_session_patterns()
            if patterns.get("sessions", 0) > 0:
                ctx += "\n### OPENCODE BRIDGE PATTERNS (AXIS 13):\n"
                ctx += f"Total external sessions: {patterns['sessions']}\n"
                if patterns.get("top_agents"):
                    ctx += f"Top external agents: {', '.join(a['agent'] for a in patterns['top_agents'][:3])}\n"
                if patterns.get("top_models"):
                    ctx += f"Top external models: {', '.join(m['model'] for m in patterns['top_models'][:3])}\n"
                ctx += f"Avg messages/session: {patterns.get('avg_messages_per_session')}\n"
        except Exception as e13:
            logger.debug(f"krisis: Axis 13 bridge context failed ({e13})")

    except Exception as e:
        logger.warning(f"krisis: get_hermes_bridge_context failed ({e})")

    return ctx


def should_use_tier(state: Any):
    """Router: Directs flow based on RuFlow Tier and Model Blacklist (Rotation)."""
    tier = state.get("ru_flow_tier", 2)
    session_id = state.get("session_id", "default")
    task_lower = state.get("task", "").lower()

    # Axis 14: Visual Pipeline Hardening
    if any(kw in task_lower for kw in ["image", "vision", "png", "jpg", "jpeg", "screenshot"]):
        logger.info("Krisis: Vision-heavy task detected. Forcing Tier 3 (Expert) for fidelity.")
        tier = 3

    # 4. Phase 11.18.4: Model Rotation Check
    current_blacklisted = BLACKLISTED_MODELS.get(session_id, [])

    if tier == 0:
        return "ultra_light"
    if tier == 1:
        return "light"
    if tier == 3:
        # Check if primary expert model is blacklisted
        from src.architrave.model_registry import ROLE_TO_MODEL

        expert_model = ROLE_TO_MODEL.get("draft", {}).get("primary")
        if expert_model in current_blacklisted:
            logger.warning(
                f"krisis: Primary Expert model '{expert_model}' is BLACKLISTED. Rotating to fallback."
            )
            return "expert_fallback"  # New state or logic handled in graph
        return "expert"
    return "standard"


def blacklist_model(session_id: str, model_name: str):
    """Adds a model to the session blacklist for rotation."""
    if session_id not in BLACKLISTED_MODELS:
        BLACKLISTED_MODELS[session_id] = []
    if model_name not in BLACKLISTED_MODELS[session_id]:
        BLACKLISTED_MODELS[session_id].append(model_name)
        logger.error(f"krisis: Model '{model_name}' has been BLACKLISTED for session {session_id}")


def should_call_tools(state: Any):
    """
    Bypasses tools for Tier 1 tasks.
    Enforces loopback to draft if verification failed.
    """
    tier = state.get("ru_flow_tier", 2)
    if tier == 0:
        logger.info("krisis: Tier 0 detected (Ultra-light). Bypassing tool loop and verification.")
        return "critique"
    if tier == 1:
        logger.info("krisis: Tier 1 detected. Bypassing tool loop.")
        return "critique"

    draft = state.get("draft")
    verify_retry = state.get("verification_retry", 0)

    # [Phase 1.0.24] Partial Correction Route: Skip tools and go to reflection -> refine
    if state.get("partial_correction"):
        logger.info(
            f"krisis: Partial Correction detected (Retry {verify_retry}). Routing to reflection."
        )
        return "reflection"

    if not draft:
        if verify_retry < 3:
            logger.warning(
                f"krisis: Draft cleared by verification (Retry {verify_retry}). Routing to loopback."
            )
            return "expert_draft" if state.get("ru_flow_tier") == 3 else "draft"
        else:
            logger.warning(
                f"krisis: Verification max retry ({verify_retry}) reached with empty draft. Forcing critique."
            )
            return "critique"

    tool_calls = state.get("tool_calls", [])
    iteration = state.get("tool_iteration", 0)

    if tool_calls and iteration < 3:
        logger.info(f"krisis: Routing to tool_exec (Iteration {iteration + 1})")
        return "tool_exec"

    logger.info("krisis: Routing to critique")
    return "critique"


def should_continue(state: Any):
    """SOTA 2026 adversarial loop: critique FAIL -> re-draft, PASS -> refine."""
    critique = state["critique"]
    zone = critique.get("zone", "ambiguous")

    if hasattr(critique, "is_pass"):
        is_valid = critique.is_pass
    elif hasattr(critique, "is_valid"):
        is_valid = critique.is_valid
    else:
        is_valid = critique.get("is_pass", critique.get("is_valid", False))

    iteration = state.get("iteration", 0)
    max_iter = 2  # SOTA Guardrail: Hard limit for reasoning loops

    # Phase 11.19.2: Red Zone (Score < 0.4) triggers immediate deadlock resolver
    if zone == "red":
        logger.error(
            f"krisis: RED ZONE detected (Score: {critique.get('overall_score')}). Routing to deadlock_resolver."
        )
        return "deadlock_resolver"

    if is_valid:
        logger.info(
            f"krisis: Critique PASS (Zone: {zone}, iter={iteration}). Routing to reflection before refine."
        )
        return "reflection"

    if iteration >= max_iter:
        logger.warning(
            f"krisis: Max iterations reached ({iteration}/{max_iter}). Routing to reflection."
        )
        return "reflection"

    try:
        from langgraph.graph import END

        from cognition.mnemosyne.meta_cognition import MetaCognitionStore
        meta = MetaCognitionStore()
        reliability = meta.get_reliability("sophia")
        if reliability < 0.2:
            logger.error(
                f"FATAL VETO: Agent reliability critically low ({reliability:.2f}). Emergency Lockdown (END)."
            )
            return END
        elif reliability <= 0.3:
            logger.warning(
                f"VETO: Agent reliability too low ({reliability:.2f}). Stopping loop via reflection."
            )
            return "reflection"
    except Exception as e:
        logger.warning(f"krisis: Meta-cognition reliability check bypassed ({e})")

    logger.info(
        f"krisis: Critique FAIL (iter={iteration}). Looping back to draft for adversarial refinement."
    )

    verify_retry = state.get("verification_retry", 0)
    if verify_retry >= 3:
        logger.error(
            f"krisis: Verification Max Retry reached ({verify_retry}). DEADLOCK DETECTED (Hallucination Spiral). Routing to deadlock_resolver."
        )
        return "deadlock_resolver"

    tier = state.get("ru_flow_tier", 2)
    return "expert_draft" if tier == 3 else "draft"


async def classify_tool_needs(task: str) -> dict[str, bool]:
    """
    [Phase 1.0.29] Local Tool Classification via FunctionGemma.
    Determines if the task requires specific local resources to optimize parallel execution.
    """
    from src.architrave.model_registry import resolve_local_model
    from src.utils.ollama_utils import get_ollama_client

    model_name = resolve_local_model("tool_calling")
    prompt = f"""<start_of_turn>user
Task: {task}
Analyze if this task requires:
1. file_ops: Creating, reading, or modifying files/directories.
2. search: Searching the web or external knowledge.
3. vision: Processing images, screenshots, or visual data.

Output only a JSON object:
{{"needs_file_ops": bool, "needs_search": bool, "needs_vision": bool}}<end_of_turn>
<start_of_turn>model
"""
    try:
        import json
        client = get_ollama_client()
        resp = await client.generate(
            model=model_name,
            prompt=prompt,
            format="json",
            options={"temperature": 0.0, "stop": ["<end_of_turn>"]}
        )
        if resp and resp.response:
            return json.loads(resp.response)
    except Exception as e:
        logger.warning(f"krisis: classify_tool_needs failed ({e}). Defaulting to all False.")
    
    return {"needs_file_ops": False, "needs_search": False, "needs_vision": False}


def should_after_reflection(state: Any):
    """Router: After reflection, decide if we refine (end) or draft (continue)."""
    critique = state.get("critique", {})
    confidence = 0.0
    is_valid = False

    if isinstance(critique, dict):
        is_valid = critique.get("is_pass", critique.get("is_valid", False))
        confidence = critique.get("overall_score", 0.0)  # Using overall_score as confidence
    elif hasattr(critique, "overall_score"):
        confidence = critique.overall_score
        is_valid = getattr(critique, "is_pass", getattr(critique, "is_valid", False))

    if is_valid or state.get("partial_correction"):
        # Phase 1.0.24: Also route to refine if partial_correction is pending
        if not state.get("partial_correction") and confidence >= 0.9:
            logger.info(
                f"krisis: ADAPTIVE SKIP - High confidence ({confidence:.2f}) detected. Bypassing refine phase."
            )
            return "end"
        return "refine"

    tier = state.get("ru_flow_tier", 2)
    return "expert_draft" if tier == 3 else "draft"
