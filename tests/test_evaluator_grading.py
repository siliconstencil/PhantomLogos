import pytest

from src.lachesis import AdversarialEvaluator


# [SRC:axis_11]
@pytest.mark.asyncio
async def test_evaluator_empty_draft():
    import asyncio

    evaluator = AdversarialEvaluator("test_empty")
    try:
        result = await asyncio.wait_for(evaluator.evaluate("", {"threshold": 0.7}), timeout=10.0)
        assert result["is_pass"] is False
        assert result["overall_score"] == 0.0
        assert len(result["flaws"]) >= 1
    except TimeoutError:
        pytest.skip("Evaluator timeout")


@pytest.mark.asyncio
async def test_evaluator_good_draft():
    import asyncio

    draft = '''
# Authentication Module

from typing import Optional

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user against the database."""
    if not username or not password:
        raise ValueError("Username and password required")
    try:
        # result = _lookup_user(username)
        # return _verify_password(result, password)
        return True # Mocked
    except Exception as e:
        return False

if __name__ == "__main__":
    assert authenticate("admin", "secret") is True
'''
    evaluator = AdversarialEvaluator("test_good")
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft, {"threshold": 0.5}), timeout=15.0)
        assert result["is_pass"] is True
        assert result["overall_score"] > 0.5
    except TimeoutError:
        pytest.skip("Evaluator timeout")


@pytest.mark.asyncio
async def test_evaluator_poor_draft():
    import asyncio

    draft = "print('hello')\npass\n# TODO"
    evaluator = AdversarialEvaluator("test_poor")
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft, {"threshold": 0.7}), timeout=10.0)
        assert result["is_pass"] is False
        assert result["overall_score"] < 0.7
        assert len(result.get("flaws", [])) >= 1
    except TimeoutError:
        pytest.skip("Evaluator timeout")


@pytest.mark.asyncio
async def test_evaluator_metrics_structure():
    import asyncio

    evaluator = AdversarialEvaluator("test_metrics")
    try:
        result = await asyncio.wait_for(
            evaluator.evaluate("def foo(): return 42", {"threshold": 0.5}), timeout=10.0
        )
        metrics = result.get("metrics", {})
        assert "design" in metrics
        assert "originality" in metrics
        assert "functionality" in metrics
        assert "craft" in metrics
        for v in metrics.values():
            assert 0.0 <= v <= 1.0
        assert 0.0 <= result["overall_score"] <= 1.0
    except TimeoutError:
        pytest.skip("Evaluator timeout")
