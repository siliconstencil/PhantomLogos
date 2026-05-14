import pytest

from src.lachesis import AdversarialEvaluator


# [SRC:axis_11]
@pytest.fixture
def evaluator():
    return AdversarialEvaluator("test_citation_session")


@pytest.mark.asyncio
async def test_citation_scoring(evaluator):
    # Case 1: No citations
    draft_no_cite = "This is a fact without source."
    score_none = evaluator._citation_score(draft_no_cite)
    assert score_none == 0.0

    # Case 2: One citation
    draft_one = "According to [SRC:axis_6], Python is good."
    score_one = evaluator._citation_score(draft_one)
    assert 0.5 < score_one < 1.0

    # Case 3: Multiple citations
    draft_multi = "Data from [SRC:axis_6] and [SRC:axis_10] confirms this [SRC:axis_3]."
    score_multi = evaluator._citation_score(draft_multi)
    assert score_multi > score_one


@pytest.mark.asyncio
async def test_consistency_hallucination(evaluator):
    anchors = "The project name is Ankyra. It uses LanceDB for memory."
    tool_results = [{"output": "The version is 1.4.2"}]

    # Case 1: Consistent
    draft_ok = "Ankyra project uses LanceDB as confirmed by [SRC:axis_6]."
    score_ok = evaluator._consistency_score(draft_ok, tool_results, anchors)
    assert score_ok == 1.0

    # Case 2: Hallucination (no overlap)
    draft_bad = "Something completely different without any shared words."
    score_bad = evaluator._consistency_score(draft_bad, tool_results, anchors)
    assert score_bad == 0.5


@pytest.mark.asyncio
async def test_full_evaluate_weighted(evaluator):
    import asyncio

    draft = "Task: [SRC:axis_6] Ankyra uses LanceDB. def solve(): return True"
    contract = {"threshold": 0.5}
    try:
        res = await asyncio.wait_for(evaluator.evaluate(draft, contract), timeout=15.0)
        assert "citation" in res["metrics"]
        assert "consistency" in res["metrics"]
        assert res["metrics"]["citation"] > 0
        assert res["metrics"]["consistency"] > 0
    except TimeoutError:
        pytest.skip("Evaluator.evaluate timed out (Ollama/Gateway might be slow)")
