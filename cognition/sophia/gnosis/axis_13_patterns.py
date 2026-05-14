from src.architrave.opencode_store import OpenCodeStore


def _build_axis_13() -> str:
    lines = []
    try:
        patterns = OpenCodeStore().get_cross_session_patterns()
        if patterns.get("sessions", 0) > 0:
            lines.append("### MNEMOSYNE AXIS 13 (CROSS-SESSION PATTERNS)")
            lines.append(f"Global usage: {patterns['sessions']} sessions recorded.")
    except Exception:
        pass
    return "\n".join(lines)
