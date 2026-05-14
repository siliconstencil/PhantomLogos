import pytest

from cognition.mnemosyne.reflection_store import ReflectionStore
from cognition.sophia.gnosis import get_dynamic_context
from src.lachesis import AdversarialEvaluator


# [SRC:axis_8]
@pytest.mark.asyncio
async def test_gnosis_injection():
    store = ReflectionStore()
    # Rule must be > 50 chars as per ReflectionStore.store_failure logic
    test_rule = "MANDATORY RULE: Always verify absolute paths in Windows environments to prevent drive mapping errors. [EXTRA_LENGTH_FOR_STORAGE_THRESHOLD]"
    store.store_failure("test_injection", "absolute path error", test_rule, severity=3)

    # Wait for async write/commit
    import asyncio

    await asyncio.sleep(1.0)

    import uuid

    unique_sid = f"test_session_{uuid.uuid4().hex[:8]}"

    # Verify rule is actually in store before calling gnosis
    rules_in_store = store.get_prevention_rules(limit=5)
    assert any("MANDATORY RULE" in r["prevention_rule"] for r in rules_in_store), (
        "Rule failed to commit to ReflectionStore"
    )

    # Axis 11: dynamic context assembly check with safety timeout
    # [SRC:axis_8] get_dynamic_context returns (context_str, metadata_dict)
    try:
        stable, dynamic, _ = await asyncio.wait_for(
            get_dynamic_context(agent_id="sophia", task_hint="windows path", session_id=unique_sid),
            timeout=10.0,
        )
        context_str = f"{stable}\n\n{dynamic}"
    except TimeoutError:
        pytest.skip("Gnosis context assembly timed out (check Ollama/LanceDB)")

    # Verify the header and content
    print(f"\nDEBUG CONTEXT START\n{context_str}\nDEBUG CONTEXT END\n")
    assert "### MNEMOSYNE AXIS 8 (PREVENTION RULES)" in context_str, (
        f"Header missing in context. Context sample: {context_str[:200]}"
    )
    assert "MANDATORY RULE: Always verify absolute paths" in context_str


@pytest.mark.asyncio
async def test_evaluator_trigger():
    import asyncio

    evaluator = AdversarialEvaluator("test_eval_session")
    poor_draft = "print('hello world')\nexcept: pass\nx = 2+2\n# TODO: fix later"
    try:
        res = await asyncio.wait_for(
            evaluator.evaluate(poor_draft, contract={"threshold": 0.7}), timeout=15.0
        )
        assert res["overall_score"] < 0.5
    except TimeoutError:
        pytest.skip("Evaluator timeout in trigger test")

    store = ReflectionStore()
    rules = store.get_prevention_rules(limit=5)
    found = [r for r in rules if "critical_quality_drop" in r["error_type"]]

    assert len(found) > 0
