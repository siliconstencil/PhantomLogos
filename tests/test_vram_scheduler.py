import pytest
import time
from cognition.morpheus.registry import find_fitting_model
from cognition.morpheus.monitor import get_gpu_memory_info
from src.atropos.token_budget import TokenBudgetGuard
from src.atropos.context_pruner import ContextPruner

# [SRC:axis_7]
@pytest.mark.asyncio
async def test_model_fitting():
    assert find_fitting_model("router", 1.0) == "granite-3-0-2b-instruct-q4_k_m:latest"
    assert find_fitting_model("critique", 3.0) == "phi-4-mini-reasoning-ud-q5_k_xl:latest"
    result = find_fitting_model("draft", 4.0)
    assert result is not None

@pytest.mark.asyncio
async def test_vram_monitor():
    info = get_gpu_memory_info()
    assert "total_gb" in info
    assert "free_gb" in info

@pytest.mark.asyncio
async def test_token_budget():
    guard = TokenBudgetGuard(daily_limit=500, hourly_limit=200)
    assert guard.consume(50)
    assert guard.remaining_daily() == 450
    assert guard.remaining_hourly() == 150
    assert not guard.consume(200)

@pytest.mark.asyncio
async def test_context_pruner_tiers():
    pruner = ContextPruner()
    mems = [{"text": f"Memory {i}", "importance": 0.5 + i * 0.05, "timestamp": time.time()}
            for i in range(10)]
    result = pruner.prune_by_tier(mems, "reasoning")
    assert len(result) > 0
    assert len(result) <= len(mems)

@pytest.mark.asyncio
async def test_token_pruner_overflow():
    pruner = ContextPruner()
    huge_mem = [{"text": "x " * 5000, "importance": 1.0, "timestamp": time.time()}]
    result = pruner.prune_context(huge_mem, token_limit=100)
    tokens = pruner.count_tokens(huge_mem[0]["text"])
    assert tokens > 100
