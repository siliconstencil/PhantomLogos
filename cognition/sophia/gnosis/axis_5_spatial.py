from cognition.sophia.hephaestus import _get_mapper, _get_reflection


def _build_axis_5(task_hint: str) -> str:
    lines = []
    if not task_hint:
        return ""
    try:
        # Codebase Mapping
        keywords = task_hint.lower().split()[:5]
        relevant = _get_mapper().suggest_context(keywords)
        if relevant:
            lines.append("### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)")
            lines.extend([f"- {m}" for m in relevant])

        # [SRC:axis_5] Semantic Relations Injection (B4)
        store = _get_reflection()
        relations = store.get_relevant_relations(keywords, limit=5)
        if relations:
            if "### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)" not in lines:
                lines.append("### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)")
            for r in relations:
                lines.append(f"- REL: ({r['subject']}) {r['predicate']} ({r['object']})")

    except Exception:
        pass
    return "\n".join(lines)
