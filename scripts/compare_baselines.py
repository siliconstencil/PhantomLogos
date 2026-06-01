import datetime
import json
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
_ROOT = str(root)


def compare():
    pre_path = os.path.join(_ROOT, "data", "baseline_pre_v121.json")
    post_path = os.path.join(_ROOT, "data", "baseline_latest.json")

    if not os.path.exists(pre_path):
        print(f"[ERROR] Pre-change baseline not found at {pre_path}")
        return
    if not os.path.exists(post_path):
        print(f"[ERROR] Post-change baseline not found at {post_path}")
        return

    with open(pre_path, encoding="utf-8") as f:
        pre_data = json.load(f)
    with open(post_path, encoding="utf-8") as f:
        post_data = json.load(f)

    pre_sum = pre_data.get("summary", {})
    post_sum = post_data.get("summary", {})

    pre_lat = pre_sum.get("total_latency_ms", 1)
    post_lat = post_sum.get("total_latency_ms", 0)
    lat_change = round(((post_lat - pre_lat) / pre_lat) * 100, 2)

    pre_avg_lat = pre_sum.get("avg_latency_ms", 1)
    post_avg_lat = post_sum.get("avg_latency_ms", 0)
    avg_lat_change = round(((post_avg_lat - pre_avg_lat) / pre_avg_lat) * 100, 2)

    pre_peak = pre_sum.get("peak_vram_gb", 0)
    post_peak = post_sum.get("peak_vram_gb", 0)
    peak_change = round(post_peak - pre_peak, 2)

    pre_avg_vram = pre_sum.get("avg_vram_gb", 0)
    post_avg_vram = post_sum.get("avg_vram_gb", 0)
    avg_vram_change = round(post_avg_vram - pre_avg_vram, 2)

    pre_succ = pre_sum.get("overall_success_rate", 0)
    post_succ = post_sum.get("overall_success_rate", 0)
    succ_change = round((post_succ - pre_succ) * 100, 2)

    table = f"""# Performance Comparison Report (PERFORMANCE_v1.2.1.md)

This report presents a comparison of system performance metrics before and after the Phantom Logos v1.2.1 release.

## Performance Comparison Table

| Metric | Before (v1.2.0) | After (v1.2.1) | Change / Status |
| :--- | :--- | :--- | :--- |
| **Total Latency** | {pre_sum.get("total_latency_ms", 0)} ms | {post_sum.get("total_latency_ms", 0)} ms | {lat_change:+}% |
| **Avg Axis Latency** | {pre_sum.get("avg_latency_ms", 0)} ms | {post_sum.get("avg_latency_ms", 0)} ms | {avg_lat_change:+}% |
| **Peak VRAM Usage** | {pre_sum.get("peak_vram_gb", 0)} GB | {post_sum.get("peak_vram_gb", 0)} GB | {peak_change:+} GB |
| **Avg VRAM Usage** | {pre_sum.get("avg_vram_gb", 0)} GB | {post_sum.get("avg_vram_gb", 0)} GB | {avg_vram_change:+} GB |
| **Overall Success Rate** | {pre_succ * 100}% | {post_succ * 100}% | {succ_change:+}% |

---
*Report Generated At: {datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p PT")}*
"""

    report_path = os.path.join(_ROOT, "docs", "PERFORMANCE_v1.2.1.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(table)
    print(f"[SUCCESS] Performance comparison report saved to {report_path}")


if __name__ == "__main__":
    compare()
