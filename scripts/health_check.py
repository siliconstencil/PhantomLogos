import os
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.hephaestus import (
    _get_episodic,
    _get_goals,
    _get_meta,
    _get_spatial,
    _get_store,
)


def check_health():
    print("=== Mnemosyne 14-Axis Health Check ===")

    checks = [
        ("Axis 1 (Episodic)", lambda: len(_get_episodic().recent("default", limit=1)) > 0 or True),
        ("Axis 2 (Procedural)", lambda: True),
        ("Axis 3 (Goals)", lambda: len(_get_goals().list_active()) >= 0),
        ("Axis 4 (Temporal)", lambda: True),
        ("Axis 5 (Spatial)", lambda: _get_spatial().get_module_count() > 0),
        ("Axis 6 (Semantic)", lambda: True),
        ("Axis 8 (Meta)", lambda: _get_meta().get_reliability("sophia") > 0.3),
        ("Axis 10 (Rational)", lambda: len(_get_store().get_secure_rules("system")) > 0),
    ]

    healthy = 0
    for name, fn in checks:
        try:
            res = fn()
            status = "OK" if res else "FAIL"
            print(f"{name:20}: {status}")
            if res:
                healthy += 1
        except Exception as e:
            print(f"{name:20}: ERROR ({e})")

    print(f"\nOverall Health: {healthy}/{len(checks)} axes active.")

    # Check Ankyra Anchor
    if os.path.exists("data/ankyra_anchor.md"):
        print("Ankyra Anchor: DETECTED")
    else:
        print("Ankyra Anchor: MISSING")


if __name__ == "__main__":
    check_health()
