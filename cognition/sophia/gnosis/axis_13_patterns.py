from cognition.sophia.hephaestus import get_episodic, get_temporal
from src.architrave.opencode_store import OpenCodeStore


def _build_axis_13(session_id: str = "default") -> str:
    lines = []
    try:
        patterns = OpenCodeStore().get_cross_session_patterns()
        if patterns.get("sessions", 0) > 0:
            lines.append("### MNEMOSYNE AXIS 13 (CROSS-SESSION PATTERNS)")
            agents = patterns.get("top_agents")
            models = patterns.get("top_models")
            lines.append(
                f"Global: {patterns['sessions']} sessions, "
                f"avg {patterns.get('avg_messages_per_session', 0)} msgs/session"
            )
            if agents:
                lines.append(
                    f"Most active agent: {agents[0]['agent']} ({agents[0]['count']} sessions)"
                )
            if models:
                lines.append(
                    f"Most used model: {models[0]['model']} ({models[0]['count']} sessions)"
                )

        recent_events = get_episodic().recent(session_id, limit=10)
        errors = [
            e
            for e in recent_events
            if "error" in e.get("outcome", "").lower() or "fail" in e.get("outcome", "").lower()
        ]
        if errors:
            lines.append(f"Recent session errors: {len(errors)}")
            for e in errors[:3]:
                lines.append(f"  - {e.get('action')}: {e.get('outcome')[:60]}")

        temps = get_temporal().query(session_id, limit=5)
        if temps:
            total_latency = sum(t.get("latency_ms", 0) or 0 for t in temps)
            avg_lat = total_latency / len(temps)
            lines.append(f"Avg latency (this session): {avg_lat:.0f}ms ({len(temps)} ops)")
    except Exception:
        pass
    return "\n".join(lines)
