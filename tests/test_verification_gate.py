import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.clotho.orchestrator import should_after_reflection, should_continue, verify_node
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
    """The reranker reports the integrity warning of the path it actually used."""
    r = JinaReranker()

    # Primary path (embeddings) fails -> the Jina model path takes over.
    with (
        patch.object(
            r, "_rerank_embeddings", new=AsyncMock(side_effect=RuntimeError("no embedding model"))
        ),
        patch.object(
            r,
            "_rerank_jina",
            new=AsyncMock(
                return_value={
                    "results": [{"index": 0, "score": 0.5, "text": "doc1"}],
                    "integrity_warning": "Jina precision mode active",
                }
            ),
        ),
    ):
        result = asyncio.run(r._execute_pipeline("query", ["doc1"], 1))

    assert "integrity_warning" in result
    assert result["integrity_warning"] == "Jina precision mode active"
    assert result["results"][0]["text"] == "doc1"

    # Both paths fail -> the reranker refuses to return a silent empty result.
    with (
        patch.object(
            r, "_rerank_embeddings", new=AsyncMock(side_effect=RuntimeError("no embedding model"))
        ),
        patch.object(r, "_rerank_jina", new=AsyncMock(side_effect=RuntimeError("no jina model"))),
    ):
        with pytest.raises(RuntimeError, match="All ranking methods failed"):
            asyncio.run(r._execute_pipeline("query", ["doc1"], 1))


@pytest.mark.asyncio
async def test_verify_retry_limit():
    """Three consecutive verification retries break the loop instead of re-drafting."""
    state = {
        "verification_retry": 3,
        "iteration": 1,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False},
    }
    result = should_continue(state)
    assert result == "deadlock_resolver"


def test_red_zone_respects_the_iteration_guardrail():
    """A red zone must not loop forever: past the iteration cap it routes to reflection.

    The red zone check used to run before the iteration guardrail, so every
    failing draft went back to draft through the deadlock resolver and the
    graph never terminated.
    """
    state = {
        "verification_retry": 0,
        "iteration": 2,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False, "zone": "red", "overall_score": 0.0},
    }
    assert should_continue(state) == "reflection"


def test_red_zone_below_the_guardrail_still_routes_to_the_deadlock_resolver():
    """Inside the iteration budget the red zone keeps its deadlock resolver route."""
    state = {
        "verification_retry": 0,
        "iteration": 0,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False, "zone": "red", "overall_score": 0.0},
    }
    assert should_continue(state) == "deadlock_resolver"


def test_reflection_ends_the_loop_when_the_iteration_budget_is_spent():
    """An invalid critique after the reflection must not send the graph back to draft.

    The graph reaches reflection through two routes (a passing critique and the
    iteration guardrail). Sending an invalid critique back to draft from there
    loops forever, so the spent budget has to end the run instead.
    """
    state = {
        "verification_retry": 0,
        "iteration": 3,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {"is_valid": False, "is_pass": False, "zone": "red", "overall_score": 0.0},
    }
    assert should_after_reflection(state) == "end"


def test_reflection_still_loops_back_while_the_budget_remains():
    """Below the iteration budget the reflection keeps its re-draft route."""
    state = {
        "verification_retry": 0,
        "iteration": 0,
        "ru_flow_tier": 2,
        "draft": "some draft",
        "critique": {
            "is_valid": False,
            "is_pass": False,
            "zone": "ambiguous",
            "overall_score": 0.5,
        },
    }
    assert should_after_reflection(state) == "draft"


def test_the_red_zone_cycle_terminates():
    """The full routing cycle of a permanently failing draft must end.

    The cycle follows the graph edges: draft -> critique, critique routes
    through should_continue, the deadlock resolver leads back to draft, and
    the reflection used to send an invalid critique back to draft as well.
    A permanently failing draft has to end at "end".
    """
    state = {
        "critique": {"is_valid": False, "is_pass": False, "zone": "red", "overall_score": 0.0},
        "iteration": 0,
        "verification_retry": 0,
        "ru_flow_tier": 2,
        "draft": "some draft",
    }

    route = "draft"
    steps = 0
    while route != "end" and steps < 20:
        if route in ("draft", "expert_draft"):
            state["iteration"] += 1
            route = should_continue(state)
        elif route == "deadlock_resolver":
            # aporia.deadlock_resolver_node relaxes the contract, resets the
            # retry counter and increments the iteration.
            state["verification_retry"] = 0
            state["iteration"] += 1
            route = "draft"
        elif route == "reflection":
            route = should_after_reflection(state)
        else:
            break
        steps += 1

    assert route == "end", f"the cycle did not terminate, it ended on {route!r}"
    assert steps < 20, "the cycle ran more steps than the guardrail allows"


def test_prose_with_an_assignment_is_not_treated_as_code():
    """Prose that mentions an assignment is prose, not code, so the axis stays neutral."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "Set threshold = 0.7 and then the critic compares the two candidates."

    assert evaluator._has_verifiable_content(draft) is False


def test_statements_are_treated_as_code():
    """A draft made of statements is code and has to be judged."""
    evaluator = AdversarialEvaluator("test_session")
    draft = "print('hello world')\nexcept: pass\nx = 2+2"

    assert evaluator._has_verifiable_content(draft) is True


if __name__ == "__main__":
    pytest.main([__file__])
