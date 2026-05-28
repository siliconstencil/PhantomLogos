import pytest

from cognition.sophia.eidos import ReasoningState
from cognition.sophia.sophia import run_draft


@pytest.mark.asyncio
async def test_tier_ultra_light_routing():
    state = ReasoningState(
        task="simple test",
        flags={"tier": "ultra_light"},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_tier_light_routing():
    state = ReasoningState(
        task="simple test",
        flags={"tier": "light"},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_tier_primary_routing():
    state = ReasoningState(
        task="simple test",
        flags={"tier": "primary"},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_tier_expert_routing():
    state = ReasoningState(
        task="simple test",
        flags={"tier": "expert"},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_tier_unknown_routing():
    state = ReasoningState(
        task="simple test",
        flags={"tier": "unknown_tier"},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_no_tier_routing():
    state = ReasoningState(task="simple test")
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_hard_gate_routing():
    state = ReasoningState(
        task="simple test",
        flags={},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_bypass_memory_gate_routing():
    state = ReasoningState(
        task="simple test",
        flags={"bypass_memory_gate": True},
    )
    result = await run_draft(state, thinking=False)
    assert result is not None


@pytest.mark.asyncio
async def test_get_temperature_default():
    from cognition.sophia import get_temperature

    assert get_temperature("unknown_role") == 0.1
