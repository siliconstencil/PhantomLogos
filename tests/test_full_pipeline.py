import time

import numpy as np
import pytest

from cognition.mnemosyne import MemoryArbitrator
from cognition.morpheus import find_fitting_model

# [SRC:axis_10]
# Import nodes from cognition and src
from cognition.sophia import (
    TaskRouter,
    ToolValidator,
    extract_tool_calls,
    get_dynamic_context,
    get_temperature,
    strip_thinking_block,
)
from src.architrave import resolve_local_model, resolve_model
from src.atropos import AtroposMonitor, ContextPruner, MatryoshkaEmbedding
from src.atropos.token_budget import TokenBudgetGuard


@pytest.mark.asyncio
async def test_router_classification():
    router = TaskRouter()
    cat, prompt = router.route("Write a python function to sort a list")
    assert cat in ("code", "chat")


@pytest.mark.asyncio
async def test_tool_validator_json():
    tv = ToolValidator()
    data = tv.validate_json(
        '{"is_valid": true, "flaws": ["ok"], "suggestions": []}',
        ["is_valid", "flaws", "suggestions"],
    )
    assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_temperature_profiles():
    assert get_temperature("draft") == 0.4
    assert get_temperature("critique") == 0.0


@pytest.mark.asyncio
async def test_context_pruner():
    pruner = ContextPruner()
    mems = [{"text": "important", "importance": 1.0, "timestamp": time.time()}]
    pruned = pruner.prune_context(mems, token_limit=10)
    assert len(pruned) == 1


@pytest.mark.asyncio
async def test_mnemosyne_rational_store():
    # Placeholder for rational store test as requested by L0
    # In Phase 8, this verifies the dynamic context assembly
    stable, dynamic, _ = await get_dynamic_context("test")
    ctx = f"{stable}\n\n{dynamic}"
    assert len(ctx) > 0


@pytest.mark.asyncio
async def test_goal_store_lifecycle():
    # Placeholder for goal store lifecycle
    from cognition.mnemosyne import GoalStore

    gs = GoalStore()
    assert gs is not None


@pytest.mark.asyncio
async def test_memory_arbitrator_scoring():
    arb = MemoryArbitrator()
    now = time.time()
    items = [
        {"relevance": 0.9, "timestamp": now, "reliability": 1.0},
        {"relevance": 0.5, "timestamp": now - 99999, "reliability": 0.8},
    ]
    ranked = arb.rank(items)
    assert ranked[0]["relevance"] > ranked[1]["relevance"]


@pytest.mark.asyncio
async def test_model_resolution():
    # [SRC:axis_10] Models are resolved via Gateway aliases. Specific strings are secondary.
    resolved = resolve_model("gemini-flash")
    assert resolved is not None

    draft_model = resolve_local_model("draft", "primary")
    assert draft_model is not None  # Should resolve based on current registry


@pytest.mark.asyncio
async def test_morpheus_model_fitting():
    model = find_fitting_model("critique", 3.0)
    assert model is not None  # Registry must provide a fitting model


@pytest.mark.asyncio
async def test_atropos_monitor():
    monitor = AtroposMonitor()

    @monitor.trace("test")
    def sync_test():
        return True

    assert sync_test() is True


@pytest.mark.asyncio
async def test_token_budget():
    guard = TokenBudgetGuard(daily_limit=100, hourly_limit=50)
    ok = guard.consume(10)
    assert ok is True
    assert guard.remaining_daily() == 90


@pytest.mark.asyncio
async def test_matryoshka_embedding():
    me = MatryoshkaEmbedding(lambda texts: np.random.rand(len(texts), 768))
    v = me.embed_query("test", 256)
    assert len(v) == 256


@pytest.mark.asyncio
async def test_tool_extraction_robustness():
    # Nested JSON
    text_nested = 'Some text {"tool": "ls", "input": {"path": ".", "recursive": true}} more text'
    calls = extract_tool_calls(text_nested)
    assert len(calls) == 1 and calls[0]["input"]["recursive"] is True

    # Malformed JSON
    text_malformed = (
        'Bad {"tool": "ls", "input": "missing quote} Good {"tool": "vram", "input": ""}'
    )
    calls_malformed = extract_tool_calls(text_malformed)
    assert len(calls_malformed) == 1 and calls_malformed[0]["tool"] == "vram"

    # Thinking block
    text_think = (
        '<think>{"tool": "ls", "input": "."}</think>Final answer: {"tool": "report", "input": ""}'
    )
    stripped = strip_thinking_block(text_think)
    assert "<think>" not in stripped
    calls_think = extract_tool_calls(stripped)
    assert len(calls_think) == 1 and calls_think[0]["tool"] == "report"
