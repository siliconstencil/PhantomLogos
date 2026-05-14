from typing import Any

from cognition.sophia.hephaestus import _get_reflection, _get_semantic


async def _build_axis_6(task_hint: str, session_id: str, vec: Any | None = None) -> str:
    lines = []
    if not task_hint:
        return ""
    try:
        # [SRC:axis_6] Semantic Memory Search
        mode = "hybrid" if vec is not None else "fts"
        semantic = _get_semantic().search(
            vec, session_id=session_id, limit=2, mode=mode, query_text=task_hint
        )
        if semantic:
            lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
            for s in semantic:
                text = s.get("text") or s.get("content") or "Empty fragment"
                lines.append(f"- {text[:300]}...")

        # [SRC:axis_6] Entity Recall (B4)
        keywords = task_hint.lower().split()[:5]
        store = _get_reflection()
        entities = store.get_relevant_entities(keywords, limit=5)
        if entities:
            if "### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)" not in lines:
                lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
            for e in entities:
                lines.append(f"- ENTITY: {e['name']} ({e['type']})")

    except Exception:
        pass
    return "\n".join(lines)
