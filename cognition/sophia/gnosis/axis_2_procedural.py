from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph
from cognition.mnemosyne.models import ToolPath

from ..hephaestus import _get_procedural


def _build_axis_2() -> str:
    lines = []
    try:
        proc = _get_procedural()
        session = proc.Session()
        try:
            rows = session.query(ToolPath).order_by(ToolPath.success_count.desc()).limit(10).all()
            if rows:
                lines.append("### MNEMOSYNE AXIS 2 (PROCEDURAL/TOOLS)")
                for r in rows:
                    total = r.success_count + r.failure_count
                    rate = r.success_count / total if total > 0 else 0
                    lines.append(
                        f"- {r.tool_name} ({r.task_type}): "
                        f"success={r.success_count}/{total} "
                        f"rate={rate:.0%} "
                        f"latency={r.avg_latency_ms:.0f}ms"
                    )
                feed_hypergraph(
                    source_axis_id=2,
                    entities=[
                        {"name": r.tool_name, "type": "tool", "axis_id": 2, "label": r.task_type}
                        for r in rows
                    ],
                    relation_type="has_tool_pattern",
                )
        finally:
            session.close()
    except Exception:
        pass
    return "\n".join(lines)
