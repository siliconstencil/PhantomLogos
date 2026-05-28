import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.utils.logging_config import setup_logger

logger = setup_logger("context_optimizer")


DEFAULT_TIER_LIMITS = {
    "reasoning": 3000,
    "task": 4000,
    "global": 5000,
}


def _load_env_limits() -> dict:
    import os

    return {
        "reasoning": int(os.getenv("TOKEN_TIER_REASONING", "3000")),
        "task": int(os.getenv("TOKEN_TIER_TASK", "4000")),
        "global": int(os.getenv("TOKEN_TIER_GLOBAL", "5000")),
    }


def optimize_context(mnemosyne_db: str | None = None, output: str | None = None):
    from sqlalchemy import create_engine, text

    from src.utils.project_path import to_absolute_path

    db_url = mnemosyne_db or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
    engine = create_engine(db_url, connect_args={"timeout": 30})

    logger.info("=== Context Optimization Analysis Started ===")

    with engine.connect() as conn:
        sessions = conn.execute(
            text("""
                SELECT ts.id, ts.session_id, ts.task, ts.cumulative_reward,
                       ts.final_score, ts.total_steps, ts.total_tokens,
                       ts.total_latency_ms, ts.created_at, ts.completed_at
                FROM trajectory_sessions ts
                WHERE ts.completed_at IS NOT NULL
                ORDER BY ts.created_at ASC
            """)
        ).fetchall()

        success_sessions = [r for r in sessions if (r[3] or 0) > 0]
        fail_sessions = [r for r in sessions if (r[3] or 0) <= 0]

        steps = conn.execute(
            text("""
                SELECT ts.trajectory_id, ts.node_name, ts.reward, ts.score,
                       ts.tokens_used, ts.latency_ms, ts.tier, ts.model_tier
                FROM trajectory_steps ts
                JOIN trajectory_sessions sess ON sess.id = ts.trajectory_id
                WHERE sess.completed_at IS NOT NULL
                ORDER BY ts.trajectory_id, ts.step_index
            """)
        ).fetchall()

    token_by_node = defaultdict(list)
    latency_by_node = defaultdict(list)
    success_by_node = defaultdict(list)

    for r in steps:
        node = r[1]
        tokens = r[4] or 0
        latency = r[5] or 0
        reward = r[2] or 0
        token_by_node[node].append(tokens)
        latency_by_node[node].append(latency)
        success_by_node[node].append(reward > 0)

    current = _load_env_limits()
    recommendations = []

    avg_tokens_success = (
        sum(r[6] or 0 for r in success_sessions) / len(success_sessions) if success_sessions else 0
    )
    avg_tokens_fail = (
        sum(r[6] or 0 for r in fail_sessions) / len(fail_sessions) if fail_sessions else 0
    )

    if avg_tokens_success and avg_tokens_fail:
        ratio = avg_tokens_fail / avg_tokens_success if avg_tokens_success else 1.0
        if ratio > 1.3:
            recommendations.append(
                f"HIGH_FAILURE_TOKEN_USAGE: Failed sessions use {ratio:.2f}x "
                f"more tokens than successful ones ({avg_tokens_fail:.0f} vs {avg_tokens_success:.0f}). "
                f"Suggestion: tighten global token budget by 15%."
            )

    node_stats = {}
    for node in sorted(token_by_node.keys()):
        tokens = token_by_node[node]
        latencies = latency_by_node[node]
        successes = success_by_node[node]
        n = len(tokens)
        node_stats[node] = {
            "visits": n,
            "avg_tokens": round(sum(tokens) / n, 1) if n else 0,
            "avg_latency_ms": round(sum(latencies) / n, 1) if n else 0,
            "success_rate": round(sum(successes) / n, 3) if n else 0,
        }

        if n >= 3 and sum(successes) / n > 0.75:
            avg_tok = sum(tokens) / n
            for tier_name, limit in current.items():
                if avg_tok > limit * 0.9:
                    recommendations.append(
                        f"TIER_BUDGET_WARNING: {node} avg_tokens={avg_tok:.0f} "
                        f"approaches {tier_name} limit={limit}. "
                        f"Consider increasing {tier_name} budget to {int(limit * 1.25)}."
                    )
                    break

    summary = {
        "total_sessions": len(sessions),
        "successful_sessions": len(success_sessions),
        "failed_sessions": len(fail_sessions),
        "success_rate": round(len(success_sessions) / len(sessions), 3) if sessions else 0,
        "avg_tokens_success": round(avg_tokens_success, 1),
        "avg_tokens_fail": round(avg_tokens_fail, 1),
        "current_limits": current,
        "node_stats": node_stats,
        "recommendations": recommendations,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    logger.info(f"Sessions analyzed: {len(sessions)}")
    logger.info(f"Success rate: {summary['success_rate']:.2%}")
    logger.info(f"Recommendations: {len(recommendations)}")
    for rec in recommendations:
        logger.warning(f"  {rec}")
    logger.info("=== Context Optimization Analysis Complete ===")

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2))
        logger.info(f"Report saved to {output}")

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4: Weekly Context Optimization Analysis")
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file for optimization report"
    )
    args = parser.parse_args()

    report = optimize_context(output=args.output)
    print(json.dumps(report, indent=2))
