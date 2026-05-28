import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.utils.logging_config import setup_logger

logger = setup_logger("trajectory_mining")


def run_mining(mnemosyne_db: str | None = None, min_visits: int = 3):
    from sqlalchemy import create_engine, text

    from src.utils.project_path import to_absolute_path

    db_url = mnemosyne_db or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
    engine = create_engine(db_url, connect_args={"timeout": 30})

    logger.info("=== Trajectory Mining Started ===")
    results = {}

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT ts.id, ts.session_id, ts.task, ts.cumulative_reward,
                       ts.final_score, ts.total_steps, ts.total_tokens,
                       ts.completed_at, ts.created_at
                FROM trajectory_sessions ts
                WHERE ts.completed_at IS NOT NULL
                ORDER BY ts.created_at DESC
            """)
        ).fetchall()

        if not rows:
            logger.info("No completed trajectory sessions found.")
            return {"sessions": 0, "pairs": {}, "report": "No data"}

        sessions = []
        for r in rows:
            sessions.append(
                {
                    "id": r[0],
                    "session_id": r[1],
                    "task": r[2],
                    "cumulative_reward": r[3],
                    "final_score": r[4],
                    "total_steps": r[5],
                    "total_tokens": r[6],
                    "completed_at": str(r[7]) if r[7] else None,
                    "created_at": str(r[8]) if r[8] else None,
                }
            )

        step_rows = conn.execute(
            text("""
                SELECT ts.trajectory_id, ts.node_name, ts.reward, ts.score,
                       ts.tokens_used, ts.latency_ms, ts.tier, ts.model_tier,
                       ts.created_at
                FROM trajectory_steps ts
                JOIN trajectory_sessions sess ON sess.id = ts.trajectory_id
                WHERE sess.completed_at IS NOT NULL
                ORDER BY ts.trajectory_id, ts.step_index
            """)
        ).fetchall()

        pair_data = defaultdict(list)
        pair_counts = defaultdict(int)
        pair_success = defaultdict(int)
        pair_latency = defaultdict(list)
        pair_tokens = defaultdict(list)

        for r in step_rows:
            key = (r[1], r[7] or "unknown")
            pair_counts[key] += 1
            pair_data[key].append(r[2])
            pair_latency[key].append(r[5] or 0)
            pair_tokens[key].append(r[6] or 0)
            if r[2] > 0:
                pair_success[key] += 1

        summary = {}
        recommendations = []
        for key, rewards in sorted(pair_data.items()):
            node, tier = key
            n = pair_counts[key]
            avg_r = sum(rewards) / n if n else 0
            success_rate = pair_success[key] / n if n else 0
            avg_lat = sum(pair_latency[key]) / n if n else 0
            avg_tok = sum(pair_tokens[key]) / n if n else 0

            entry = {
                "node_name": node,
                "model_tier": tier,
                "visits": n,
                "avg_reward": round(avg_r, 3),
                "success_rate": round(success_rate, 3),
                "avg_latency_ms": round(avg_lat, 1),
                "avg_tokens": round(avg_tok, 1),
            }
            summary[f"{node}/{tier}"] = entry

            if n >= min_visits and success_rate < 0.4:
                recommendations.append(
                    f"LOW_PERFORMANCE: {node}/{tier} (sr={success_rate:.2f}, "
                    f"avg_r={avg_r:.3f}, n={n}) - consider reducing weight"
                )
            elif n >= min_visits and success_rate > 0.8:
                recommendations.append(
                    f"HIGH_PERFORMANCE: {node}/{tier} (sr={success_rate:.2f}, "
                    f"avg_r={avg_r:.3f}, n={n}) - consider increasing weight"
                )

        results = {
            "sessions": len(sessions),
            "total_steps": len(step_rows),
            "total_pairs": len(summary),
            "min_visits": min_visits,
            "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "pairs": summary,
            "recommendations": recommendations,
            "session_ids": [s["session_id"] for s in sessions],
        }

        logger.info(f"Sessions mined: {len(sessions)}")
        logger.info(f"Total steps: {len(step_rows)}")
        logger.info(f"(node, tier) pairs: {len(summary)}")
        for rec in recommendations:
            logger.warning(f"  {rec}")

    from src.architrave.otl_engine import get_otl_engine

    otl = get_otl_engine()
    update_count = 0
    for key, entry in summary.items():
        node = entry["node_name"]
        tier = entry["model_tier"]
        visits = entry["visits"]
        if visits >= min_visits:
            otl.update_weight(node, tier, entry["avg_reward"])
            update_count += 1

    logger.info(f"OTL weights updated: {update_count} pairs")
    logger.info("=== Trajectory Mining Complete ===")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 3: Weekly Trajectory Mining for OTL")
    parser.add_argument(
        "--min-visits",
        type=int,
        default=3,
        help="Minimum visits to trigger OTL weight update (default: 3)",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file for mining report"
    )
    args = parser.parse_args()

    report = run_mining(min_visits=args.min_visits)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        logger.info(f"Report saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))
