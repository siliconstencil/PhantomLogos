import pytest

from src.atropos.context_pruner import ContextPruner
from src.atropos.token_budget import TokenBudgetGuard


def test_token_budget_guard():
    guard = TokenBudgetGuard(daily_limit=1000, hourly_limit=500)
    assert guard.consume(100) is True
    assert guard.remaining_daily() == 900
    assert guard.consume(600) is False


def test_context_pruner_basic():
    pruner = ContextPruner()
    long_text = "This is a test " * 10
    shortened = pruner.count_tokens(long_text)
    assert shortened > 0


def test_context_pruner_prioritization():
    pruner = ContextPruner()
    context = (
        "### MNEMOSYNE AXIS 15 (HYPERGRAPH)\nHigh priority text but lowest rank axis.\n"
        "### MNEMOSYNE AXIS 8 (META-COGNITION/RELIABILITY)\nCrucial reliability info, highest priority.\n"
        "### PROJECT ANCHOR (ANKYRA)\nAbsolute anchor text, priority 0.\n"
    )
    # With a small limit, Axis 8 and Anchor should be preserved, Axis 15 dropped
    sliced = pruner.slice_context_window(context, "reasoning")
    assert "PROJECT ANCHOR" in sliced
    assert "AXIS 8" in sliced
    # Check prioritization logic: AXIS 15 has lower priority (15) and should be pruned if limit is exceeded, but here reasoning limit is 3000 tokens so let's set a smaller limit
    pruner.tier_limits["reasoning"] = 50
    sliced_strict = pruner.slice_context_window(context, "reasoning")
    assert "PROJECT ANCHOR" in sliced_strict
    assert "AXIS 8" in sliced_strict
    assert "AXIS 15" not in sliced_strict


def test_context_pruner_budget_exceeded():
    from src.atropos.token_budget import TokenBudgetGuard

    # Set a tiny daily limit
    guard = TokenBudgetGuard(daily_limit=10, hourly_limit=10)
    pruner = ContextPruner()
    pruner.budget_guard = guard

    assert pruner.budget_exceeded is False
    # This should consume more than 10 tokens
    pruner.slice_context_window(
        "This is a longer text that exceeds ten tokens for sure.", "reasoning"
    )
    assert pruner.budget_exceeded is True


def test_context_pruner_slice_safety():
    pruner = ContextPruner()
    # Test None
    assert pruner.slice_context_window(None, "reasoning") == ""
    # Test Empty
    assert pruner.slice_context_window("", "reasoning") == ""
    assert pruner.slice_context_window("   ", "reasoning") == ""

    # Test Exception recovery
    # Force tier_limits to raise AttributeError or similar by making it None
    pruner.tier_limits = None
    # slice_context_window should catch Exception and fall back gracefully without crashing
    res = pruner.slice_context_window(
        "Some text input that would normally trigger slicing", "reasoning"
    )
    assert isinstance(res, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
