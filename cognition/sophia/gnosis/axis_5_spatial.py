from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph
from cognition.sophia.hephaestus import get_mapper, get_reflection


def _build_axis_5(task_hint: str) -> str:
    lines = []
    if not task_hint:
        return ""
    try:
        # Codebase Mapping
        keywords = task_hint.lower().split()[:5]
        relevant = get_mapper().suggest_context(keywords)
        if relevant:
            lines.append("### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)")
            lines.extend([f"- {m}" for m in relevant])
            feed_hypergraph(
                source_axis_id=5,
                entities=[
                    {"name": m, "type": "module", "axis_id": 5, "label": "suggested_context"}
                    for m in relevant
                ],
                relation_type="references_module",
            )

        # [SRC:axis_5] Semantic Relations Injection (B4)
        store = get_reflection()
        matched_entities = store.get_relevant_entities(keywords, limit=5)
        entity_names = [e["name"] for e in matched_entities] if matched_entities else []
        if entity_names:
            feed_hypergraph(
                source_axis_id=5,
                entities=[
                    {"name": e["name"], "type": e.get("type", "entity"), "axis_id": 6, "label": ""}
                    for e in matched_entities
                ],
                relation_type="references_entity",
            )
        relations = []
        if entity_names:
            relations = store.get_relevant_relations(entity_names, limit=5)
        if relations:
            if "### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)" not in lines:
                lines.append("### MNEMOSYNE AXIS 5 (SPATIAL/CODEBASE)")
            for r in relations:
                lines.append(f"- REL: ({r['subject']}) {r['predicate']} ({r['object']})")

    except Exception:
        pass
    return "\n".join(lines)
