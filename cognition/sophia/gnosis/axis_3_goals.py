from ..hephaestus import get_goals


def _build_axis_3() -> str:
    lines = []
    goals = get_goals().list_active(limit=3)
    if goals:
        lines.append("### MNEMOSYNE AXIS 3 (ACTIVE GOALS)")
        for g in goals:
            lines.append(f"- [{g.get('priority')}] {g.get('title')}: {g.get('description')}")
    return "\n".join(lines)
