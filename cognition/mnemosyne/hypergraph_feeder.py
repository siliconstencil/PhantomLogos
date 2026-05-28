from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def feed_hypergraph(
    source_axis_id: int,
    entities: list[dict[str, Any]],
    relation_type: str,
    weight: float = 1.0,
) -> None:
    if not entities:
        return
    try:
        from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
        from cognition.mnemosyne.hypergraph_store import HypergraphStore

        nodes: list[HypernodeRef] = []
        for ent in entities:
            node = HypernodeRef(
                axis_id=ent.get("axis_id", source_axis_id),
                entity_type=ent.get("type", "unknown"),
                entity_key=ent.get("name", ""),
                label=ent.get("label", ""),
            )
            nodes.append(node)

        source_node = HypernodeRef(
            axis_id=source_axis_id,
            entity_type="axis_context",
            entity_key=f"axis_{source_axis_id}_build",
            label=f"Axis {source_axis_id} Builder",
        )

        edge = Hyperedge(
            nodes=[source_node, *nodes],
            relation_type=relation_type,
            weight=weight,
        )

        store = HypergraphStore()
        store.add_edge(edge)
        logger.debug(
            f"[SRC:axis_15] feed_hypergraph: axis={source_axis_id} "
            f"relation={relation_type} entities={len(entities)}"
        )
    except Exception:
        logger.debug(
            f"feed_hypergraph: failed for axis={source_axis_id} "
            f"relation={relation_type} - graceful degradation"
        )
