import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.architrave.gateway_client import GatewayArchitrave, MockResponse


@pytest.fixture
def configure_dual_gateway():
    # Set env vars for dual-gateway testing
    os.environ["ANTIGRAVITY_GATEWAY_URL"] = "http://localhost:32553"
    os.environ["ANTIGRAVITY_GATEWAY_URL_SECONDARY"] = "http://localhost:32554"
    os.environ["ANTIGRAVITY_GATEWAY_SECONDARY_TIMEOUT"] = "2.0"
    yield
    # Cleanup
    if "ANTIGRAVITY_GATEWAY_URL_SECONDARY" in os.environ:
        del os.environ["ANTIGRAVITY_GATEWAY_URL_SECONDARY"]


@pytest.mark.asyncio
async def test_primary_success(configure_dual_gateway):
    """Primary OK, secondary is not called."""
    architrave = GatewayArchitrave()

    # Mock clients
    mock_primary_client = MagicMock()
    mock_secondary_client = MagicMock()

    primary_response = MagicMock(text="Primary Response", thoughts="Primary Thoughts")
    mock_primary_client.aio.models.generate_content = AsyncMock(return_value=primary_response)
    mock_secondary_client.aio.models.generate_content = AsyncMock()

    architrave.client = mock_primary_client
    architrave._secondary_client = mock_secondary_client

    # Mock health check to be True
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Primary Response"
    mock_primary_client.aio.models.generate_content.assert_called_once()
    mock_secondary_client.aio.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_primary_fail_secondary_success(configure_dual_gateway):
    """Primary fails with ConnectError, secondary succeeds."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_secondary_client = MagicMock()

    # Primary fails with ConnectionRefusedError
    mock_primary_client.aio.models.generate_content = AsyncMock(
        side_effect=ConnectionRefusedError("Connection refused")
    )

    secondary_response = MagicMock(text="Secondary Response", thoughts="Secondary Thoughts")
    mock_secondary_client.aio.models.generate_content = AsyncMock(return_value=secondary_response)

    architrave.client = mock_primary_client
    architrave._secondary_client = mock_secondary_client
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Secondary Response"
    mock_primary_client.aio.models.generate_content.assert_called()
    mock_secondary_client.aio.models.generate_content.assert_called_once()
    # Primary CB should be triggered
    assert architrave._breaker._cb_until_primary > time.time()


@pytest.mark.asyncio
async def test_both_fail_local_fallback(configure_dual_gateway):
    """Both endpoints fail, falls back to local model."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_secondary_client = MagicMock()

    mock_primary_client.aio.models.generate_content = AsyncMock(
        side_effect=ConnectionRefusedError("Primary dead")
    )
    mock_secondary_client.aio.models.generate_content = AsyncMock(
        side_effect=ConnectionRefusedError("Secondary dead")
    )

    architrave.client = mock_primary_client
    architrave._secondary_client = mock_secondary_client
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    # Mock local fallback to return mock response
    mock_fallback_response = MockResponse("Local Output")
    architrave._local_fallback = AsyncMock(return_value=mock_fallback_response)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Local Output"
    assert architrave._breaker._cb_until_primary > time.time()
    assert architrave._breaker._cb_until_secondary > time.time()


@pytest.mark.asyncio
async def test_secondary_2s_timeout(configure_dual_gateway):
    """Secondary takes 3s, triggers 2s timeout and falls back to local."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_secondary_client = MagicMock()

    mock_primary_client.aio.models.generate_content = AsyncMock(
        side_effect=ConnectionRefusedError("Primary dead")
    )

    async def slow_call(*args, **kwargs):
        await asyncio.sleep(3.0)
        return MagicMock(text="Too slow")

    mock_secondary_client.aio.models.generate_content = AsyncMock(side_effect=slow_call)

    architrave.client = mock_primary_client
    architrave._secondary_client = mock_secondary_client
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    mock_fallback_response = MockResponse("Local Output via Timeout")
    architrave._local_fallback = AsyncMock(return_value=mock_fallback_response)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Local Output via Timeout"
    assert architrave._breaker._cb_until_secondary > time.time()


@pytest.mark.asyncio
async def test_secondary_not_configured():
    """Secondary not set, primary fail -> local fallback without secondary attempt."""
    if "ANTIGRAVITY_GATEWAY_URL_SECONDARY" in os.environ:
        del os.environ["ANTIGRAVITY_GATEWAY_URL_SECONDARY"]

    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_primary_client.aio.models.generate_content = AsyncMock(
        side_effect=ConnectionRefusedError("Primary dead")
    )

    architrave.client = mock_primary_client
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    mock_fallback_response = MockResponse("Direct Local Output")
    architrave._local_fallback = AsyncMock(return_value=mock_fallback_response)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Direct Local Output"
    assert architrave._breaker._cb_until_primary > time.time()
    assert architrave._secondary_client is None


@pytest.mark.asyncio
async def test_independent_cb(configure_dual_gateway):
    """Primary CB is active (blocked), secondary is healthy and succeeds immediately."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_secondary_client = MagicMock()

    mock_primary_client.aio.models.generate_content = AsyncMock()
    secondary_response = MagicMock(text="Secondary Direct Output")
    mock_secondary_client.aio.models.generate_content = AsyncMock(return_value=secondary_response)

    architrave.client = mock_primary_client
    architrave._secondary_client = mock_secondary_client

    # Primary CB active in the future
    architrave._breaker._cb_until_primary = int(time.time() + 30)
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    res = await architrave.generate_async("Test Prompt")

    assert res.text == "Secondary Direct Output"
    # Primary must NOT be called since it is blocked by CB
    mock_primary_client.aio.models.generate_content.assert_not_called()
    mock_secondary_client.aio.models.generate_content.assert_called_once()
