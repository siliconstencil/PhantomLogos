import pytest
from src.clotho.orchestrator import create_clotho_graph

# [SRC:axis_13]
@pytest.mark.asyncio
async def test_reflection_trace():
    """Verify that the Clotho graph contains the required nodes and compiles correctly."""
    app = create_clotho_graph()
    nodes = app.nodes
    assert "reflection" in nodes
    assert "negotiate" in nodes
    assert "verify_node" in nodes
    assert "deadlock_resolver" in nodes
