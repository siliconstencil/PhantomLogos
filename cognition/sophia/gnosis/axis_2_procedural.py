from ..hephaestus import _get_procedural

def _build_axis_2() -> list:
    lines = []
    try:
        proc = _get_procedural()
        tool_lines = []
        for tt in ("critique", "vision", "semantic", "ls"):
            best = proc.best_tool(tt)
            if best:
                tool_lines.append(f"- {tt}: {best[0][0]} (rate={best[0][1]:.0%})")
        if tool_lines:
            lines.append("### MNEMOSYNE AXIS 2 (PROCEDURAL/TOOLS)")
            lines.extend(tool_lines)
    except Exception: pass
    return lines
