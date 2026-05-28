from unittest.mock import patch

import pytest

from src.architrave.sovereign_middleware import (
    AntiLoopCircuitBreaker,
    MiddlewarePipeline,
    MiddlewareRequest,
    MiddlewareResponse,
)
from src.atropos.context_cache_middleware import ContextCacheMiddleware
from src.atropos.token_budget_middleware import TokenBudgetMiddleware
from src.lachesis.verifiers.local_repair import LocalRepairMiddleware


class MockGateway:
    async def generate_async(self, prompt, **kwargs):
        from src.architrave.gateway_client import MockResponse

        return MockResponse(
            text=f"Mock response for: {prompt}",
            thoughts="Mock thoughts",
            model="mock-model",
        )

    async def generate_async_stream(self, prompt, **kwargs):
        yield "Chunk 1"
        yield "Chunk 2"


@pytest.mark.asyncio
async def test_basic_pipeline_execution():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    req = MiddlewareRequest(prompt="Hello World", session_id="test_session")
    resp = await pipeline.execute(req)

    assert isinstance(resp, MiddlewareResponse)
    assert "Mock response for: Hello World" in resp.text
    assert resp.session_id == "test_session"
    assert any(log["hook"] == "pipeline_start" for log in resp.middleware_log)


@pytest.mark.asyncio
async def test_anti_loop_circuit_breaker():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    cb = AntiLoopCircuitBreaker(max_loop_count=3, cooldown_seconds=2.0)
    pipeline.add_before(cb)

    # First 3 requests should pass
    for _ in range(3):
        resp = await pipeline.execute(MiddlewareRequest(prompt="test", session_id="loop_session"))
        assert "[MIDDLEWARE GUARD]" not in resp.text

    # 4th request should trip the circuit breaker and be blocked
    resp_blocked = await pipeline.execute(
        MiddlewareRequest(prompt="test", session_id="loop_session")
    )
    assert "[MIDDLEWARE GUARD]" in resp_blocked.text
    assert any(
        log.get("reason") == "circuit_open" or log.get("action") == "tripped"
        for log in resp_blocked.middleware_log
    )

    # Reset circuit breaker
    cb.reset("loop_session")
    resp_after_reset = await pipeline.execute(
        MiddlewareRequest(prompt="test", session_id="loop_session")
    )
    assert "[MIDDLEWARE GUARD]" not in resp_after_reset.text


@pytest.mark.asyncio
async def test_token_budget_middleware_allow():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    # High limits, should pass
    tb = TokenBudgetMiddleware(daily_limit=100000, hourly_limit=10000)
    pipeline.add_before(tb)

    req = MiddlewareRequest(prompt="Tiny prompt", session_id="budget_session")
    resp = await pipeline.execute(req)
    assert "[MIDDLEWARE GUARD]" not in resp.text
    assert any(
        log["hook"] == "TokenBudget" and log["action"] == "allowed" for log in resp.middleware_log
    )


@pytest.mark.asyncio
async def test_token_budget_middleware_block():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    # Super low limits to trigger block
    tb = TokenBudgetMiddleware(daily_limit=1, hourly_limit=1)
    tb.guard.daily_limit = 1
    tb.guard.hourly_limit = 1
    tb.guard._daily_used = 0
    tb.guard._hourly_used = 0
    pipeline.add_before(tb)

    req = MiddlewareRequest(
        prompt="This is a prompt that will exceed limit of 1 token", session_id="budget_session_low"
    )
    resp = await pipeline.execute(req)
    assert "[MIDDLEWARE GUARD]" in resp.text
    assert any(
        log["hook"] == "TokenBudget" and log["action"] == "blocked" for log in resp.middleware_log
    )


@pytest.mark.asyncio
async def test_context_cache_middleware():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    cache_mw = ContextCacheMiddleware(ttl_seconds=10)
    pipeline.add_around(cache_mw)

    # First request - Miss and store
    req = MiddlewareRequest(prompt="Unique Cache Prompt", session_id="cache_session")
    resp1 = await pipeline.execute(req)
    assert any(
        log["hook"] == "ContextCache" and log["action"] == "miss" for log in resp1.middleware_log
    )

    # Second request - Hit (short-circuit)
    resp2 = await pipeline.execute(req)
    assert any(
        log["hook"] == "ContextCache" and log["action"] == "hit" for log in resp2.middleware_log
    )
    assert resp2.text == resp1.text


@pytest.mark.asyncio
async def test_local_repair_middleware_ok():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    # We mock _assess_quality to return high score (1.0)
    repair_mw = LocalRepairMiddleware(threshold=0.6)

    with patch.object(repair_mw, "_assess_quality", return_value=1.0) as mock_assess:
        pipeline.add_after(repair_mw)
        req = MiddlewareRequest(prompt="Test quality", session_id="repair_session")
        resp = await pipeline.execute(req)
        mock_assess.assert_called_once()
        assert "[REPAIRED" not in (resp.thoughts or "")


@pytest.mark.asyncio
async def test_local_repair_middleware_repair():
    pipeline = MiddlewarePipeline()
    pipeline.set_gateway(MockGateway())

    repair_mw = LocalRepairMiddleware(threshold=0.6)

    # Mock low quality score and successful repair
    with (
        patch.object(repair_mw, "_assess_quality", return_value=0.3) as mock_assess,
        patch.object(
            repair_mw, "_repair_response", return_value="Repaired Response Text"
        ) as mock_repair,
    ):
        pipeline.add_after(repair_mw)
        req = MiddlewareRequest(prompt="Test low quality", session_id="repair_session_low")
        resp = await pipeline.execute(req)
        mock_assess.assert_called_once()
        mock_repair.assert_called_once()
        assert resp.text == "Repaired Response Text"
        assert "[REPAIRED" in resp.thoughts
