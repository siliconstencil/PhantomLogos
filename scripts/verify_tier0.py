import asyncio
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.clotho.ergon.symmachia import negotiate_node


async def test_tier0():
    print("=== Testing Tier 0 Routing (Complexity 0.2) ===")
    mock_state = {"session_id": "test_tier0_session", "task": "list files in root"}

    # Mocking dependencies to avoid full system boot
    # SprintContract will be mocked or used if simple enough

    try:
        # We need to mock SprintContract.negotiate to return complexity 0.2
        from unittest.mock import patch

        with (
            patch(
                "cognition.sophia.sprint_contract.SprintContract.negotiate",
                return_value={"complexity": 0.2, "threshold": 0.5},
            ),
            patch("src.clotho.bootstrap.quick_vram_check", return_value={"free_gb": 6.0}),
            patch(
                "cognition.mnemosyne.meta_cognition.MetaCognitionStore.get_reliability",
                return_value=1.0,
            ),
        ):
            result = await negotiate_node(mock_state)

            tier = result.get("ru_flow_tier")
            model_tier = result.get("selected_model_tier")

            print(f"Result: Tier {tier}, Model Tier: {model_tier}")

            if tier == 0 and model_tier == "ultra_light":
                print("SUCCESS: Tier 0 correctly assigned for low complexity.")
                return True
            else:
                print(f"FAILED: Expected Tier 0/ultra_light, got Tier {tier}/{model_tier}")
                return False
    except Exception as e:
        print(f"ERROR during test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tier0())
    sys.exit(0 if success else 1)
