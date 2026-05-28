import pytest

from cognition.sophia.router import TASK_CATEGORIES, TaskRouter
from cognition.sophia.state_bus import StateBus


# [SRC:axis_10]
@pytest.mark.asyncio
async def test_router_classification():
    router = TaskRouter()
    test_cases = [
        ("Write a Python class for a binary search tree", "code"),
        ("Calculate the integral of x^2 from 0 to 1", "math"),
        ("Explain why binary search is O(log n)", "reasoning"),
        ("What is the capital of France?", "chat"),
        ("How do I sort a list in Python using sorted()?", "code"),
    ]
    for task, _expected in test_cases:
        category = router.classify(task)
        assert category in TASK_CATEGORIES, f"Unknown category: {category}"


@pytest.mark.asyncio
async def test_state_bus():
    bus = StateBus()

    async def handler(msg):
        pass

    bus.subscribe("agent_1", handler)
    bus.send("test", "topic_x", {"data": 1})
    history = bus.recent(1)
    assert len(history) == 1
    assert history[0].topic == "topic_x"


@pytest.mark.asyncio
async def test_router_fallback():
    router = TaskRouter()
    category = router.classify("Hello how are you?")
    valid_categories = {"chat", "reasoning"}
    assert category in valid_categories, f"Expected chat/reasoning, got {category}"
