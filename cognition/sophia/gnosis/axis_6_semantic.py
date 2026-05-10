from typing import Any, Optional
from ..hephaestus import _get_semantic

async def _build_axis_6(task_hint: str, session_id: str, vec: Optional[Any] = None) -> list:
    lines = []
    if not task_hint: return lines
    try:
        semantic = _get_semantic().search(vec, session_id=session_id, limit=2)
        if semantic:
            lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
            for s in semantic:
                lines.append(f"- {s.get('content')[:300]}...")
    except Exception: pass
    return lines
