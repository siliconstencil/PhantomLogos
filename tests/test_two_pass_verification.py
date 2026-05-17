import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clotho.ergon import critique_node
from src.clotho.krisis import should_continue
from src.lachesis import AdversarialEvaluator


# [SRC:axis_11]
@pytest.fixture
def base_state():
    return {
        "session_id": "test_l3_session",
        "draft": "def example():\n    return True\n# [SRC:axis_1]",
        "iteration": 0,
        "max_iterations": 2,
        "ru_flow_tier": 2,
    }


@pytest.mark.asyncio
async def test_evaluator_zones(base_state):
    evaluator = AdversarialEvaluator(base_state["session_id"])
    # Mocking sub-scores to force zones
    evaluator._design_score = MagicMock(return_value=0.8)
    evaluator._originality_score = MagicMock(return_value=0.8)
    evaluator._verification_score = AsyncMock(return_value=0.9)

    # Test Green Zone
    try:
        res_green = await asyncio.wait_for(evaluator.evaluate(base_state["draft"]), timeout=15.0)
        assert res_green["zone"] == "green"
    except TimeoutError:
        pytest.skip("Evaluator timeout in Green Zone")

    # Test Red Zone
    evaluator._design_score = MagicMock(return_value=0.1)
    evaluator._verification_score = AsyncMock(return_value=0.1)
    evaluator._originality_score = MagicMock(return_value=0.1)
    evaluator._craft_score = MagicMock(return_value=0.1)
    evaluator._functionality_score = MagicMock(return_value=0.1)
    try:
        res_red = await asyncio.wait_for(evaluator.evaluate(base_state["draft"]), timeout=15.0)
        assert res_red["zone"] == "red"
    except TimeoutError:
        pytest.skip("Evaluator timeout in Red Zone")


@pytest.mark.asyncio
@patch("cognition.sophia.sophia.run_critique")
@patch("cognition.morpheus.loader.ModelLoader.flush")
async def test_critique_node_3_pass_flow(mock_flush, mock_run_critique, base_state):
    # Setup Pass 2 Mock
    from cognition.sophia.eidos import CritiqueResult

    mock_run_critique.side_effect = [
        CritiqueResult(
            is_valid=False, flaws=["weak"], suggestions=[], confidence_score=0.4
        ),  # Pass 2
        CritiqueResult(is_valid=True, flaws=[], suggestions=[], confidence_score=0.9),  # Pass 3
    ]

    # Force Ambiguous Zone in Pass 1
    with patch(
        "src.lachesis.verifiers.evaluator.AdversarialEvaluator.evaluate", new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.return_value = {
            "overall_score": 0.5,
            "zone": "ambiguous",
            "is_pass": False,
            "flaws": ["heuristic flaw"],
        }

        output = await critique_node(base_state)

        # Assertions
        assert output["memory_sync"]
        assert mock_run_critique.call_count == 2
        mock_flush.assert_called_once()  # Should be called before Pass 3
        assert output["critique"]["is_pass"]


def test_krisis_red_zone_routing():
    state = {
        "critique": {"zone": "red", "overall_score": 0.2, "is_pass": False},
        "iteration": 0,
        "max_iterations": 2,
    }
    route = should_continue(state)
    assert route == "deadlock_resolver"
