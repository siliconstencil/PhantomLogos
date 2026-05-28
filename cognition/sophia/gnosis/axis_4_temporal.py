from ..hephaestus import _get_temporal


def _build_axis_4(session_id: str) -> str:
    lines = []
    temporal = _get_temporal().query(session_id, limit=3)
    if not temporal:
        temporal = _get_temporal().query("system", limit=3)
    if not temporal:
        import sqlite3
        import time

        store = _get_temporal()
        conn = sqlite3.connect(store._db_path)
        conn.row_factory = sqlite3.Row
        try:
            one_day_ago = time.time() - 86400
            rows = conn.execute(
                "SELECT * FROM temporal_metrics WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 3",
                (one_day_ago,),
            ).fetchall()
            temporal = [dict(r) for r in rows]
        except Exception:
            temporal = []
        finally:
            conn.close()

    if temporal:
        lines.append("### MNEMOSYNE AXIS 4 (TEMPORAL METRICS)")
        for t in temporal:
            lines.append(f"- {t.get('event_type')}: {t.get('latency_ms')}ms")

    try:
        import sqlite3

        store = _get_temporal()
        conn = sqlite3.connect(store._db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT event_type, avg_latency, total_count, period FROM weekly_summary ORDER BY created_at DESC LIMIT 3"
        ).fetchall()
        if rows:
            lines.append("Weekly summary:")
            for r in rows:
                lines.append(
                    f"  - {r['event_type']}: avg {r['avg_latency']:.0f}ms ({r['total_count']} ops, period {r['period']})"
                )
        conn.close()
    except Exception:
        pass

    return "\n".join(lines)
