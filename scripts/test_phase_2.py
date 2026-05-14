import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.gnosis.axis_1_episodic import _build_axis_1
from cognition.sophia.hephaestus import _get_episodic


def test_episodic():
    print("=== Phase 2 Verification: Episodic Write Path ===")

    # 1. Manually log a test episode to see if timestamp works
    store = _get_episodic()
    session_id = "verification_session"
    store.log(
        session_id=session_id,
        action="phase_2_test",
        detail="Testing timestamp repair",
        outcome="success",
    )

    # 2. Build axis 1
    lines = _build_axis_1(session_id)

    print("Axis 1 Output:")
    for line in lines:
        print(f"  {line}")

    if any(":" in line and "->" in line for line in lines):
        print("SUCCESS: Phase 2 Episodic repair verified (Timestamp present).")
    else:
        print("FAILURE: Timestamp missing or format incorrect.")


if __name__ == "__main__":
    test_episodic()
