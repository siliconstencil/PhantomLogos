import os

from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph
from src.architrave.mcp import get_slm_client

from ..hephaestus import get_episodic


async def _build_axis_1(session_id: str) -> str:
    lines = []
    episodes = get_episodic().recent(session_id, limit=3)
    if episodes:
        lines.append("### MNEMOSYNE AXIS 1 (EPISODIC HISTORY)")
        for ep in episodes:
            lines.append(f"- {ep.get('timestamp')}: {ep.get('action')} -> {ep.get('outcome')}")
        feed_hypergraph(
            source_axis_id=1,
            entities=[
                {
                    "name": ep.get("action", "unknown"),
                    "type": "action",
                    "axis_id": 1,
                    "label": ep.get("outcome", ""),
                }
                for ep in episodes
                if ep.get("action")
            ],
            relation_type="performed_action",
        )

    # SLM Recall integration (Axis 1)
    if os.getenv("SLM_ENABLED", "true").lower() == "true":
        try:
            slm = get_slm_client()
            if slm.health():
                slm_results = await slm.asearch(
                    query="episodic history action outcome",
                    limit=3,
                    table_name="default",
                    session_id=session_id,
                )
                if slm_results:
                    lines.append("- SLM RECALLED EPISODES:")
                    for r in slm_results:
                        if r.get("axis_id") == 1:
                            lines.append(f"  * {r.get('text')}")
        except Exception:
            pass

    return "\n".join(lines)
