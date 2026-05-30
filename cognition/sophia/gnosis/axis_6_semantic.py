from typing import Any

from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph
from cognition.mnemosyne.hypergraph_store import HypergraphStore
from cognition.sophia.hephaestus import get_reflection, get_semantic


async def _build_axis_6(task_hint: str, session_id: str, vec: Any | None = None) -> str:
    lines = []
    if not task_hint:
        return ""
    try:
        # [SRC:axis_6] Semantic Memory Search
        mode = "hybrid" if vec is not None else "fts"
        semantic = get_semantic().search(
            vec, session_id=session_id, limit=2, mode=mode, query_text=task_hint
        )
        if semantic:
            lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
            for s in semantic:
                text = s.get("text") or s.get("content") or "Empty fragment"
                lines.append(f"- {text[:300]}...")

        # [SRC:axis_6] Entity Recall (B4)
        keywords = task_hint.lower().split()[:5]
        store = get_reflection()
        entities = store.get_relevant_entities(keywords, limit=5)
        if entities:
            if "### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)" not in lines:
                lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
            for e in entities:
                lines.append(f"- ENTITY: {e['name']} ({e['type']})")
            feed_hypergraph(
                source_axis_id=6,
                entities=[
                    {"name": e["name"], "type": e.get("type", "entity"), "axis_id": 6, "label": ""}
                    for e in entities
                ],
                relation_type="mentioned_in_memory",
            )

        # [SRC:axis_6] Hypergraph context (moved from Axis 15)
        hg = HypergraphStore()
        hg_edges = hg.query_by_entity(axis_id=6, entity_key=" ".join(keywords))
        if hg_edges:
            for edge in hg_edges[:5]:
                if not edge.is_valid():
                    continue
                nodes = [f"Axis {n.axis_id} [{n.label or n.entity_key}]" for n in edge.nodes]
                if "### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)" not in lines:
                    lines.append("### MNEMOSYNE AXIS 6 (SEMANTIC MEMORY)")
                lines.append(
                    f"- HYPERGRAPH ({edge.relation_type}): {' <-> '.join(nodes)} (w: {edge.get_decayed_weight():.2f})"
                )

    except Exception:
        pass
    return "\n".join(lines)
