import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.architrave.gateway_client import GatewayArchitrave, MockResponse
from src.architrave.kratos import async_retry


@pytest.mark.asyncio
async def test_async_retry_early_exit_on_quota():
    """Verify async_retry breaks immediately on quota/429/limit error strings instead of 3 retries."""
    call_count = 0

    @async_retry(max_attempts=3, base_delay=0.1)
    async def failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Resource has exceeded its quota limit.")

    with pytest.raises(ValueError) as exc:
        await failing_func()

    assert "quota limit" in str(exc.value)
    # Must only call once because "quota" breaks out early!
    assert call_count == 1


@pytest.mark.asyncio
async def test_async_retry_standard_retry():
    """Verify async_retry does NOT break on standard exceptions and retries max_attempts times."""
    call_count = 0

    @async_retry(max_attempts=3, base_delay=0.01)
    async def standard_failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Some random socket timeout error.")

    with pytest.raises(ValueError):
        await standard_failing_func()

    assert call_count == 3


@pytest.mark.asyncio
async def test_generate_async_cb_keywords():
    """Verify generate_async triggers CB on quota/limit keywords, but not on validation errors."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    # Mocking exceptions that contain quota limit keywords
    mock_primary_client.aio.models.generate_content = AsyncMock(
        side_effect=ValueError("Quota exhausted on model call.")
    )
    architrave.client = mock_primary_client
    architrave.is_gateway_healthy = AsyncMock(return_value=True)

    # Mock local fallback to avoid real local calls
    architrave._local_fallback = AsyncMock(return_value=MockResponse("Local backup"))

    # Call generate_async
    res = await architrave.generate_async("Test")
    assert res.text == "Local backup"
    # Primary CB must be triggered because "quota/exhausted" is a CB keyword!
    assert architrave._breaker._cb_until_primary > time.time()


def test_generate_sync_cb_keywords():
    """Verify synchronous generate triggers CB on overloaded/quota errors."""
    architrave = GatewayArchitrave()

    mock_primary_client = MagicMock()
    mock_primary_client.models.generate_content = MagicMock(
        side_effect=ValueError("Server is overloaded and busy.")
    )
    architrave.client = mock_primary_client

    # Mock fallback
    architrave._local_fallback = AsyncMock(return_value=MockResponse("Local backup sync"))

    # Call generate (synchronous)
    res = architrave.generate("Test")
    assert res.text == "Local backup sync"
    # Primary CB must be triggered because "overloaded" is a CB keyword!
    assert architrave._breaker._cb_until_primary > time.time()
