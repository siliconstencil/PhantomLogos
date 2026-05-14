import asyncio
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

from cognition.sophia.gnosis.axis_1_episodic import _build_axis_1
from cognition.sophia.gnosis.axis_2_procedural import _build_axis_2
from cognition.sophia.gnosis.axis_3_goals import _build_axis_3
from cognition.sophia.gnosis.axis_4_temporal import _build_axis_4
from cognition.sophia.gnosis.axis_5_spatial import _build_axis_5
from cognition.sophia.gnosis.axis_6_semantic import _build_axis_6
from cognition.sophia.gnosis.axis_7_operational import _build_axis_7
from cognition.sophia.gnosis.axis_8_meta import _build_axis_8_meta
from cognition.sophia.gnosis.axis_9_tone import _build_axis_9
from cognition.sophia.gnosis.axis_10_rational import _build_axis_10
from cognition.sophia.gnosis.axis_11_verify import _build_axis_11
from cognition.sophia.gnosis.axis_12_cache import _build_axis_12
from cognition.sophia.gnosis.axis_13_patterns import _build_axis_13
from cognition.sophia.gnosis.axis_14_visual import _build_axis_14

# --- Known-broken axes from audit_022.log ---
# These axes have 0 write callers at runtime. Their content is structurally
# returned by gnosis builders, but reflects stale or no runtime data.
KNOWN_BROKEN = {
    "Axis 3 (Goals)": "GoalStore.add() has 0 callers at runtime.",
    "Axis 8 (Meta)": "record_experience() has 0 callers at runtime.",
    "Axis 9 (Tone)": "record_tone() has 0 callers at runtime.",
    "Axis 12 (Cache)": "ContextCacheStore.set/get() has 0 callers at runtime.",
}

# Minimum non-trivial content threshold (lines).
# An axis returning 0 or 1 lines is considered EMPTY/BROKEN.
MINIMUM_LINES = 2


def _classify(name: str, res: str) -> tuple:
    """
    Classify axis result into: OK / WARN / BROKEN / ERROR.
    Returns (status_label, detail).
    """
    line_count = len([l for l in res.splitlines() if l.strip()])

    if name in KNOWN_BROKEN:
        return "BROKEN", f"0 lines (Known: {KNOWN_BROKEN[name]})"

    if line_count == 0:
        return "BROKEN", "0 lines -- axis has no data"

    if line_count < MINIMUM_LINES:
        return "WARN", f"{line_count} lines -- sparse data"

    return "OK", f"{line_count} lines"


async def check_all_14_axes():
    print("=== Mnemosyne 14-Axis Stability Audit (Hardened) ===")

    session_id = "default"
    agent_id = "sophia"
    task_hint = "integrity check"

    axes = [
        ("Axis 1 (Episodic)", False, lambda: _build_axis_1(session_id)),
        ("Axis 2 (Procedural)", False, lambda: _build_axis_2()),
        ("Axis 3 (Goals)", False, lambda: _build_axis_3()),
        ("Axis 4 (Temporal)", False, lambda: _build_axis_4(session_id)),
        ("Axis 5 (Spatial)", False, lambda: _build_axis_5(task_hint)),
        ("Axis 6 (Semantic)", True, lambda: _build_axis_6(task_hint, session_id)),
        ("Axis 7 (Operational)", False, lambda: _build_axis_7()),
        ("Axis 8 (Meta)", False, lambda: _build_axis_8_meta(session_id)),
        ("Axis 9 (Tone)", False, lambda: _build_axis_9(session_id, task_hint)),
        ("Axis 10 (Rational)", False, lambda: _build_axis_10(agent_id)),
        ("Axis 11 (Verify)", False, lambda: _build_axis_11()),
        ("Axis 12 (Cache)", False, lambda: _build_axis_12()),
        ("Axis 13 (Patterns)", False, lambda: _build_axis_13()),
        ("Axis 14 (Visual)", False, lambda: _build_axis_14(session_id)),
    ]

    results = {"OK": 0, "WARN": 0, "BROKEN": 0, "ERROR": 0}

    for name, is_async, fn in axes:
        try:
            res = await fn() if is_async else fn()

            if not isinstance(res, str):
                status, detail = "FAIL", f"Non-string return: {type(res)}"
                results["ERROR"] += 1
            else:
                status, detail = _classify(name, res)
                results[status if status in results else "OK"] += 1

            marker = "[!]" if status in ("BROKEN", "WARN", "ERROR", "FAIL") else "   "
            print(f"{marker} {name:22}: {status:6} ({detail})")

        except Exception as e:
            results["ERROR"] += 1
            print(f"[!] {name:22}: ERROR  ({e})")

    ok = results["OK"]
    broken = results["BROKEN"]
    warn = results["WARN"]
    err = results["ERROR"]

    print("\n=== Audit Summary ===")
    print(f"  OK     : {ok}")
    print(f"  WARN   : {warn}")
    print(f"  BROKEN : {broken}")
    print(f"  ERROR  : {err}")
    print(f"  Total  : {ok + warn + broken + err}/14")

    if broken == 0 and err == 0:
        if warn == 0:
            print("\nSovereign Integrity: VERIFIED (0.98+)")
        else:
            print(f"\nSovereign Integrity: DEGRADED -- {warn} axis(es) sparse data.")
    else:
        print(f"\nSovereign Integrity: BROKEN -- {broken} broken + {err} error axis(es).")
        print("Action Required: Review BROKEN axes and inject missing write callers.")


if __name__ == "__main__":
    asyncio.run(check_all_14_axes())
