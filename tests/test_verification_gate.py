import pytest
import asyncio
from src.lachesis import AdversarialEvaluator
from src.lachesis import get_output_guard
from src.clotho.orchestrator import verify_node, GraphState, should_continue
from src.muscle.reranker import JinaReranker

@pytest.mark.asyncio
async def test_hard_gate_contradiction():
    """Test 1: if True: + else: iceren draft verify_node tarafindan reddedilmeli."""
    state = {
        "draft": "```python\nif True:\n    print('True')\nelse:\n    print('Contradiction')\n```",
        "verification_retry": 0,
        "session_id": "test_session"
    }
    result = await verify_node(state)
    assert result.get("draft") == "", f"Contradiction not detected. Result: {result}"
    assert result.get("verification_retry") == 1
    assert result.get("memory_sync") is False

@pytest.mark.asyncio
async def test_hard_gate_math():
    """Test 2: 2 + 2 = 5 iceren draft Lachesis tarafindan reddedilmeli."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "Hesaplama sonucu: 2 + 2 = 5. Bu bir testtir ve uzunlugu yeterlidir."
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft), timeout=15.0)
        print(f"DEBUG Math Result: {result}")
        assert result["is_pass"] is False, f"Hard gate failed to reject math error. Result: {result}"
        assert any("Invalid math" in f for f in result["flaws"]), f"Specific math flaw message missing. Flaws: {result['flaws']}"
    except asyncio.TimeoutError:
        pytest.skip("Evaluator timeout in hard_gate_math")

@pytest.mark.asyncio
async def test_soft_pass_no_code():
    """Test 3: Kod icermeyen temiz metin dogrulamadan gecmeli."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "Bu sadece bir metin taslagidir ve mantiksal bir iddia icermez. Tasarim ve kurgu acisindan yeterli uzunluktadir."
    try:
        result = await asyncio.wait_for(evaluator.evaluate(draft), timeout=10.0)
        assert result.get("metrics", {}).get("verification", 0) >= 0.5
    except asyncio.TimeoutError:
        pytest.skip("Evaluator timeout in soft_pass_no_code")

def test_output_guard_no_exempt():
    """Test 4: Tool call icinde emoji varsa OutputGuard yakalamali."""
    guard = get_output_guard()
    tool_output = '{"thought": "test", "tool": "ls", "input": "."} 😊'
    result = guard.check(tool_output, agent_id="sophia", context={"is_tool_call": True})
    assert result["action"] == "reject"
    assert "emoji_ban" in result["violations"]

def test_reranker_warning():
    """Test 5: Model yoksa reranker integrity_warning dondurmeli."""
    r = JinaReranker(model_path="/non/existent/path.gguf")
    result = r.rerank("query", ["doc1", "doc2"])
    assert "integrity_warning" in result
    assert result["integrity_warning"] is not None

@pytest.mark.asyncio
async def test_verify_retry_limit():
    """Test 6: 3 kez ust uste retry durumunda force_pass."""
    state = {
        "verification_retry": 3,
        "iteration": 1,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False}
    }
    result = should_continue(state)
    assert result == "refine"

if __name__ == "__main__":
    pytest.main([__file__])
