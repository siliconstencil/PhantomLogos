from ..hephaestus import _get_temporal


def _build_axis_4(session_id: str) -> str:
    lines = []
    store = _get_temporal()
    temporal = store.query(session_id, limit=3)
    if not temporal:
        temporal = store.query("system", limit=3)
    if not temporal:
        temporal = store.query_last_24h(limit=3)

    if temporal:
        lines.append("### MNEMOSYNE AXIS 4 (TEMPORAL METRICS)")
        for t in temporal:
            lines.append(f"- {t.get('event_type')}: {t.get('latency_ms')}ms")

    try:
        weekly = store.query_weekly_summary(limit=3)
        if weekly:
            lines.append("Weekly summary:")
            for r in weekly:
                lines.append(
                    f"  - {r['event_type']}: avg {r['avg_latency']:.0f}ms ({r['total_count']} ops, period {r['period']})"
                )
    except Exception:
        pass

    return "\n".join(lines)
