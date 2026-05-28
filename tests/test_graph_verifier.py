import pytest

from src.lachesis.verifiers import GraphVerifier


@pytest.fixture
def verifier():
    return GraphVerifier()


@pytest.mark.asyncio
async def test_red_zone_gate_trigger_active(verifier):
    # Case: overall_score = 0.3 (Red Zone score threshold is < 0.4) -> Should trigger
    res = await verifier.verify_red_zone_gate(overall_score=0.3, verification_retry=0)
    assert res.get("is_valid") is True
    assert res.get("result") == "Satisfiable"


@pytest.mark.asyncio
async def test_red_zone_gate_trigger_retry(verifier):
    # Case: retry >= 3 -> Should trigger even if overall_score is high
    res = await verifier.verify_red_zone_gate(overall_score=0.5, verification_retry=3)
    assert res.get("is_valid") is True
    assert res.get("result") == "Satisfiable"


@pytest.mark.asyncio
async def test_red_zone_gate_inactive(verifier):
    # Case: score >= 0.4 and retry < 3 -> Should NOT trigger (UNSAT)
    res = await verifier.verify_red_zone_gate(overall_score=0.5, verification_retry=1)
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_deadlock_resolver_threshold_safe(verifier):
    # Case: threshold is 0.5 (>= 0.5 is safe) -> SAT
    res = await verifier.verify_deadlock_resolver(
        threshold=0.5, verification_retry=3, overall_score=0.5
    )
    assert res.get("is_valid") is True
    assert res.get("result") == "Satisfiable"


@pytest.mark.asyncio
async def test_deadlock_resolver_threshold_violation(verifier):
    # Case: threshold is 0.4 (< 0.5 violation) -> UNSAT
    res = await verifier.verify_deadlock_resolver(
        threshold=0.4, verification_retry=3, overall_score=0.5
    )
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_deadlock_mutation_pass(verifier):
    # Case: threshold relaxed correctly (0.7 -> 0.6), retry reset (0), iteration incremented (2), mem_sync=True -> SAT
    res = await verifier.verify_deadlock_mutation(
        threshold=0.6, old_threshold=0.7, retry=0, iteration=2, old_iteration=1, mem_sync=True
    )
    assert res.get("is_valid") is True
    assert res.get("result") == "Satisfiable"


@pytest.mark.asyncio
async def test_deadlock_mutation_fail_retry_not_reset(verifier):
    # Case: retry not reset -> UNSAT
    res = await verifier.verify_deadlock_mutation(
        threshold=0.6, old_threshold=0.7, retry=3, iteration=2, old_iteration=1, mem_sync=True
    )
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_deadlock_mutation_fail_threshold_not_relaxed(verifier):
    # Case: threshold not relaxed -> UNSAT
    res = await verifier.verify_deadlock_mutation(
        threshold=0.7, old_threshold=0.7, retry=0, iteration=2, old_iteration=1, mem_sync=True
    )
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_deadlock_error_path_sat(verifier):
    # Case: deadlock resolver failed -> no mutation, retry not reset, mem_sync=False -> SAT
    res = await verifier.verify_deadlock_error(
        threshold=0.7,
        old_threshold=0.7,
        retry=3,
        old_retry=3,
        iteration=1,
        old_iteration=1,
        mem_sync=False,
    )
    assert res.get("is_valid") is True
    assert res.get("result") == "Satisfiable"


@pytest.mark.asyncio
async def test_deadlock_error_path_unsat_retry_wrongly_reset(verifier):
    # Case: retry reset on failure path -> violates error path invariants -> UNSAT
    res = await verifier.verify_deadlock_error(
        threshold=0.7,
        old_threshold=0.7,
        retry=0,
        old_retry=3,
        iteration=1,
        old_iteration=1,
        mem_sync=False,
    )
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_is_pass_false_override_edge_case(verifier):
    # Bulgu 3: verification_score = 0.45 (< 0.5, so is_pass = False)
    # but verification_retry = 1 (so zone is not red, since retry < 3 and score >= 0.4)
    # The red zone gate should NOT trigger immediately, but loopback instead (verify_red_zone_gate is UNSAT)
    res = await verifier.verify_red_zone_gate(overall_score=0.45, verification_retry=1)
    assert res.get("is_valid") is False
    assert res.get("result") == "Unsatisfiable"


@pytest.mark.asyncio
async def test_run_all_success_flow(verifier):
    state = {
        "overall_score": 0.5,
        "verification_retry": 0,
        "threshold": 0.6,
        "iteration": 2,
        "memory_sync": True,
    }
    old_state = {"threshold": 0.7, "verification_retry": 3, "iteration": 1}
    results = await verifier.run_all(state, old_state)
    assert "red_zone" in results
    assert "deadlock_pre" in results
    assert "deadlock_mutation" in results
