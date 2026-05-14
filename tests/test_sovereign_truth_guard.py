import unittest
from unittest.mock import MagicMock, patch

import pytest

from cognition.sophia.hephaestus import ReasoningState
from cognition.sophia.sophia import run_draft
from src.clotho.bridge import ToolBridge
from src.clotho.krisis import BLACKLISTED_MODELS


@pytest.mark.smoke
class TestSovereignTruthGuard(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "test_truth_session"
        if self.session_id in BLACKLISTED_MODELS:
            del BLACKLISTED_MODELS[self.session_id]

    @patch("src.clotho.bootstrap.quick_vram_check")
    async def test_shadow_vram_lie(self, mock_vram):
        """S1: Test if a VRAM lie triggers a Shadow Verification failure."""
        mock_vram.return_value = 4.0  # Reality is 4GB

        bridge = ToolBridge(session_id=self.session_id, agent_id="sophia")

        # Simulate a lie: Agent claims 8GB free VRAM
        input_data = {"claimed_free_gb": 8.0}

        # We expect record_shadow_violation to be called via output_guard
        with patch(
            "src.lachesis.verifiers.output_guard.OutputGuard.record_shadow_violation"
        ) as mock_record:
            await bridge.execute("vram", input_data)
            mock_record.assert_called_once()
            args, kwargs = mock_record.call_args
            self.assertIn("Claimed 8.0 GB", args[1])

    @patch("cognition.sophia.sophia.get_dynamic_context")
    async def test_hard_gate_blocking(self, mock_context):
        """S3: Test if a Hard Gate block prevents Sophia from generating."""
        # Simulate a severe recurring failure match
        mock_context.return_value = (
            "Context text",
            {"block": True, "reason": "Severe Hallucination Loop Detected"},
        )

        state = ReasoningState(task="Format C drive", session_id=self.session_id)
        output, tool_calls = await run_draft(state)

        self.assertIn("HARD GATE", output)
        self.assertEqual(tool_calls, [])

    @patch("src.lachesis.verifiers.output_guard.get_output_guard")
    @patch("src.clotho.bootstrap.quick_vram_check")
    async def test_auto_rotation_trigger(self, mock_vram, mock_guard):
        """S4: Test if 2 consecutive shadow failures trigger model rotation."""
        mock_vram.return_value = 2.0

        # We need to test the MetaCognitionStore logic which is integrated in adjust_reliability
        from cognition.mnemosyne.meta_cognition import MetaCognitionStore

        store = MetaCognitionStore()

        # First failure
        store.adjust_reliability(
            "sophia", -0.3, "shadow_verification_failed", session_id=self.session_id
        )
        self.assertNotIn(
            "gemini-2.0-flash-thinking-exp:latest", BLACKLISTED_MODELS.get(self.session_id, [])
        )

        # Second failure (Consecutive)
        store.adjust_reliability(
            "sophia", -0.3, "shadow_verification_failed", session_id=self.session_id
        )

        # Rotation should be triggered and primary model blacklisted
        from src.architrave.model_registry import ROLE_TO_MODEL

        primary = ROLE_TO_MODEL["draft"]["primary"]
        self.assertIn(primary, BLACKLISTED_MODELS.get(self.session_id, []))

    @patch("cognition.sophia.sophia.get_dynamic_context")
    async def test_schema_enforcement_fail(self, mock_context):
        """S2: Test if Sophia rejects non-JSON / Invalid Schema output."""
        mock_context.return_value = ("Stable", "Dynamic", {"block": False})

        # Invalid JSON
        bad_output = "I am a helpful assistant and I don't want to use JSON."

        with patch("src.architrave.gateway_client.GatewayArchitrave.generate_async") as mock_gen:
            mock_gen.return_value = MagicMock(text=bad_output)

            state = ReasoningState(task="test", session_id=self.session_id)
            output, tool_calls = await run_draft(state)

            # Should return empty on schema failure
            self.assertEqual(output, "")
            self.assertEqual(tool_calls, [])


if __name__ == "__main__":
    unittest.main()
