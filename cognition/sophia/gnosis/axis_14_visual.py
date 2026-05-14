from ..hephaestus import _get_visual


def _build_axis_14(session_id: str) -> str:
    lines = []
    try:
        visual = _get_visual()
        recent = visual.get_recent(session_id, limit=3)
        if recent:
            lines.append("### MNEMOSYNE AXIS 14 (VISUAL PIPELINE)")
            for r in recent:
                lines.append(
                    f"- [{r['variant'].upper()}] {r['timestamp']}: {r['description'][:200]}..."
                )
    except Exception:
        pass
    return "\n".join(lines)
