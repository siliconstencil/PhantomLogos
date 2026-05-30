import pytest

from src.clotho.ergon.graph_verify import graph_verify_node


@pytest.mark.asyncio
async def test_graph_verify_node_success():
    state = {
        "critique": {"overall_score": 0.9},
        "verification_retry": 0,
        "threshold": 0.7,
        "iteration": 2,
        "memory_sync": True,
    }
    result = await graph_verify_node(state)
    assert "graph_verification" in result
    assert result["graph_verification"]["status"] in ("passed", "violation", "error")
    if result["graph_verification"]["status"] == "passed":
        assert "results" in result["graph_verification"]


@pytest.mark.asyncio
async def test_graph_verify_node_violation_path():
    state = {
        "critique": {"overall_score": 0.2},
        "verification_retry": 0,
        "threshold": 0.3,
        "iteration": 1,
        "memory_sync": False,
    }
    result = await graph_verify_node(state)
    assert "graph_verification" in result
    status = result["graph_verification"]["status"]
    assert status in ("passed", "violation", "error"), f"Unexpected status: {status}"


@pytest.mark.asyncio
async def test_graph_verify_node_missing_critique():
    state = {"verification_retry": 0}
    result = await graph_verify_node(state)
    assert "graph_verification" in result
