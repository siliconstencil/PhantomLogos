from ..hephaestus import _get_episodic


def _build_axis_1(session_id: str) -> str:
    lines = []
    episodes = _get_episodic().recent(session_id, limit=3)
    if episodes:
        lines.append("### MNEMOSYNE AXIS 1 (EPISODIC HISTORY)")
        for ep in episodes:
            lines.append(f"- {ep.get('timestamp')}: {ep.get('action')} -> {ep.get('outcome')}")
    return "\n".join(lines)
