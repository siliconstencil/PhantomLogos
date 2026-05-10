from ..hephaestus import _get_mapper

def _build_axis_5(task_hint: str) -> list:
    lines = []
    if not task_hint: return lines
    try:
        keywords = task_hint.lower().split()[:5]
        relevant = _get_mapper().suggest_context(keywords)
        if relevant:
            lines.append("### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)")
            lines.extend([f"- {m}" for m in relevant])
    except Exception: pass
    return lines
