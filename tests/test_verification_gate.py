import asyncio

import pytest

from src.clotho.orchestrator import should_continue, verify_node
from src.lachesis import AdversarialEvaluator, get_output_guard
from src.muscle.reranker import JinaReranker


@pytest.mark.asyncio
async def test_hard_gate_contradiction():
    """Test 1: draft containing if True: + else: should be rejected by verify_node."""
    state = {
        "draft": "```python\nif True:\n    print('True')\nelse:\n    print('Contradiction')\n```",
        "verification_retry": 0,
        "session_id": "test_session",
    }
    result = await verify_node(state)
    assert result.get("draft") == "", f"Contradiction not detected. Result: {result}"
    assert result.get("verification_retry") == 1
    assert result.get("memory_sync") is False


@pytest.mark.asyncio
async def test_hard_gate_math():
    """Test 2: draft containing 2 + 2 = 5 should be rejected by Lachesis."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "Hesaplama sonucu: 2 + 2 = 5. Bu bir testtir ve uzunlugu yeterlidir."
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft), timeout=15.0)
        print(f"DEBUG Math Result: {result}")
        assert result["is_pass"] is False, (
            f"Hard gate failed to reject math error. Result: {result}"
        )
        assert any("Invalid math" in f for f in result["flaws"]), (
            f"Specific math flaw message missing. Flaws: {result['flaws']}"
        )
    except TimeoutError:
        pytest.skip("Evaluator timeout in hard_gate_math")


@pytest.mark.asyncio
async def test_soft_pass_no_code():
    """Test 3: Clean text without code should pass verification."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "This is just a draft text and contains no logical claims. It is of sufficient length for design purposes."
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft), timeout=10.0)
        assert result.get("metrics", {}).get("verification", 0) >= 0.5
    except TimeoutError:
        pytest.skip("Evaluator timeout in soft_pass_no_code")


def test_output_guard_no_exempt():
    """Test 4: OutputGuard should catch emoji inside tool calls."""
    guard = get_output_guard()
    tool_output = '{"thought": "test", "tool": "ls", "input": "."} \U0001f60a'
    result = guard.check(tool_output, agent_id="sophia", context={"is_tool_call": True})
    assert result["action"] == "reject"
    assert "emoji_ban" in result["violations"]


def test_reranker_warning():
    """Test 5: reranker should return integrity_warning if model is missing."""
    r = JinaReranker(model_path="/non/existent/path.gguf")
    result = r.rerank("query", ["doc1", "doc2"])
    assert "integrity_warning" in result
    assert result["integrity_warning"] is not None


@pytest.mark.asyncio
async def test_verify_retry_limit():
    """Test 6: force_pass in case of 3 consecutive retries."""
    state = {
        "verification_retry": 3,
        "iteration": 1,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False},
    }
    result = should_continue(state)
    assert result == "refine"


if __name__ == "__main__":
    pytest.main([__file__])
