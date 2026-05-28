import os
import sqlite3

from src.architrave.context_cache import ContextCacheStore


def _build_axis_12(session_id: str = "default") -> str:
    lines = []
    try:
        active_caches = ContextCacheStore().count_active()
        lines.append("### MNEMOSYNE AXIS 12 (EFFICIENCY/CACHE)")
        if active_caches > 0:
            lines.append(f"Active context caches: {active_caches}")

        base = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        db_path = os.path.join(base, "data", "mnemosyne.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*), SUM(cached_tokens), SUM(total_tokens), AVG(latency_ms)
                    FROM axis_12_cache_metrics
                    WHERE session_id = ?
                """,
                    (session_id,),
                )
                row = cursor.fetchone()
                if row and row[0] > 0:
                    count, cached_sum, total_sum, avg_lat = row
                    cached_sum = cached_sum or 0
                    total_sum = total_sum or 0
                    avg_lat = avg_lat or 0.0
                    hit_rate = (cached_sum / total_sum) * 100.0 if total_sum > 0 else 0.0
                    lines.append(
                        f"Session Caching: Requests={count}, CachedTokens={cached_sum}, TotalTokens={total_sum}, HitRate={hit_rate:.1f}%, AvgLatency={avg_lat:.1f}ms"
                    )

                cursor.execute(
                    """
                    SELECT hit_status, COUNT(*)
                    FROM axis_12_cache_metrics
                    WHERE session_id = ?
                    GROUP BY hit_status
                """,
                    (session_id,),
                )
                dist = cursor.fetchall()
                if dist:
                    dist_str = ", ".join(f"{status}={c}" for status, c in dist)
                    lines.append(f"Cache Hit Distribution: {dist_str}")
            finally:
                conn.close()
    except Exception:
        pass
    return "\n".join(lines)
