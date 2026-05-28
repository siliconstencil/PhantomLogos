import os
from typing import Any

from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph
from cognition.sophia.hephaestus import _get_meta, _get_reflection
from src.architrave.mcp import get_slm_client


async def _build_axis_8_meta(session_id: str = "default") -> str:
    lines = []
    try:
        # Reliability Metrics
        rel = _get_meta().get_reliability("sophia")
        lines.append("### MNEMOSYNE AXIS 8 (META-COGNITION/RELIABILITY)")
        lines.append(f"Agent reliability score: {rel:.2f}")

        # [SRC:axis_8] Cross-Session Reflection Recall (P3)
        store = _get_reflection()
        reflections = store.get_relevant_reflections(session_id, limit=3)
        if reflections:
            lines.append("- RECENT REFLECTIONS:")
            for r in reflections:
                lines.append(f"  * {r['insight']}")

        # SLM Recall integration (Axis 8)
        if os.getenv("SLM_ENABLED", "true").lower() == "true":
            try:
                slm = get_slm_client()
                if slm.health():
                    slm_results = await slm.asearch(
                        query="meta-cognition reflections insights reliability",
                        limit=3,
                        table_name="default",
                        session_id=session_id,
                    )
                    if slm_results:
                        lines.append("- SLM RECALLED METADATA:")
                        for r in slm_results:
                            if r.get("axis_id") == 8:
                                lines.append(f"  * {r.get('text')}")
            except Exception:
                pass

    except Exception:
        pass
    return "\n".join(lines)


async def _build_axis_8_failures(task_hint: str, vec: Any | None = None) -> tuple[str, dict]:
    lines = []
    block_signal = {"block": False, "reason": None}
    try:
        # Phase 5.1: Enforcement based on Reliability Score (Bulgu C)
        rel = _get_meta().get_reliability("sophia")
        if rel <= 0.3:
            block_signal["block"] = True
            block_signal["reason"] = (
                f"Agent reliability critical ({rel:.2f}). Locked by Sovereign Protocol."
            )

        rules = _get_reflection().get_prevention_rules(limit=5)
        if rules:
            lines.append("### MNEMOSYNE AXIS 8 (PREVENTION RULES)")
            for r in rules:
                sev, rec = r.get("severity", 1), r.get("recurrence_count", 1)
                # Only overwrite reason if not already blocked by reliability
                if sev >= 3 and rec >= 3 and not block_signal["block"]:
                    block_signal["block"] = True
                    block_signal["reason"] = r.get("prevention_rule")
                lines.append(f"- [{r.get('error_type')}] {r.get('prevention_rule')}")
            feed_hypergraph(
                source_axis_id=8,
                entities=[
                    {
                        "name": r.get("error_type", "unknown"),
                        "type": "error_type",
                        "axis_id": 8,
                        "label": r.get("prevention_rule", ""),
                    }
                    for r in rules
                ],
                relation_type="has_failure_pattern",
            )
    except Exception:
        pass
    return "\n".join(lines), block_signal
