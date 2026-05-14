from ...mnemosyne.tone_store import ToneStore


def _build_axis_9(session_id: str, task_hint: str) -> str:
    lines = []
    try:
        recent = ToneStore().get_recent_tone(session_id)
        if recent != "neutral":
            lines.append("### MNEMOSYNE AXIS 9 (USER TONE)")
            lines.append(f"Tone detected: {recent}")
    except Exception:
        pass
    return "\n".join(lines)
