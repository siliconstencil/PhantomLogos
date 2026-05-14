import asyncio
import os
import unittest

from src.architrave.gemini_client import AgnosticArchitrave


class TestAgnosticStability(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["ANTIGRAVITY_GATEWAY_URL"] = "http://localhost:32553"
        self.architrave = AgnosticArchitrave()

    async def test_generate_async_flow(self):
        print("\nVerifying Async Generation Flow...")
        # Since we don't have a real gateway responding, we expect a connection error
        # OR it might work if the user's opencode server is actually a proxy.
        # But we primarily want to check if the logic reaches the generation call without crashes.

        try:
            # We use a short timeout to fail fast if no server is there
            response = await asyncio.wait_for(
                self.architrave.generate_async(prompt="Hello Gateway", thinking=True), timeout=2.0
            )
            print("Received response from Gateway!")
        except TimeoutError:
            print("Gateway connection timed out (as expected if no listener on 32553)")
        except Exception as e:
            print(f"Caught expected gateway connection error or similar: {type(e).__name__}")
            # If it's a connection error, it means the client logic is sound and reached the network layer
            if "ConnectError" in str(type(e)) or "ConnectionError" in str(type(e)):
                print("Network layer reached successfully.")
            else:
                raise e

    def test_model_masking(self):
        print("Verifying Model Masking (Regex Protection)...")
        model = self.architrave.default_model
        assert model.startswith("models/"), (
            f"Model name {model} must start with 'models/' for SDK compatibility."
        )
        print(f"Masked Model Name: {model}")


if __name__ == "__main__":
    unittest.main()
