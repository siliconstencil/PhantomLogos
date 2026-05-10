import pytest
from src.atropos.token_budget import TokenBudgetGuard
from src.atropos.context_pruner import ContextPruner

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

if __name__ == "__main__":
    print("Running Atropos logic tests...")
    test_token_budget_guard()
    test_context_pruner_basic()
    print("Atropos logic tests passed.")
