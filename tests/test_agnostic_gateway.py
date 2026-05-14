import os

import pytest

from src.architrave.gateway_client import GatewayArchitrave
from src.architrave.model_registry import resolve_capability


# [SRC:axis_10]
@pytest.mark.asyncio
async def test_agnostic_initialization():
    """Verify that GatewayArchitrave initializes correctly with the sovereign gateway URL."""
    # Set gateway env for testing
    os.environ["ANTIGRAVITY_GATEWAY_URL"] = "http://localhost:32553"

    architrave = GatewayArchitrave()

    assert architrave.sovereign_mode is True

    expected_model = resolve_capability("strategic")
    assert architrave.default_model == expected_model

    if architrave.client:
        # Check base_url in http_options
        assert architrave.gateway_url == "http://localhost:32553"
