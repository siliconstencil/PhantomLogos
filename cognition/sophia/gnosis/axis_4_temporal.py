from ..hephaestus import _get_temporal


def _build_axis_4(session_id: str) -> str:
    lines = []
    temporal = _get_temporal().query(session_id, limit=3)
    if temporal:
        lines.append("### MNEMOSYNE AXIS 4 (TEMPORAL METRICS)")
        for t in temporal:
            lines.append(f"- {t.get('event_type')}: {t.get('latency_ms')}ms")
    return "\n".join(lines)
