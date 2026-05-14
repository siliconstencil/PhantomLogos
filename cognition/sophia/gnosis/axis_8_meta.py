from typing import Any

from cognition.sophia.hephaestus import _get_meta, _get_reflection


def _build_axis_8_meta(session_id: str = "default") -> str:
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
    except Exception:
        pass
    return "\n".join(lines), block_signal
