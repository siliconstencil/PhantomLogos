import pytest
import sqlite3
from src.utils.logging_config import setup_logger
from src.architrave.context_cache import AnchorContextBuilder
from cognition.mnemosyne.memory_arbitrator import MemoryArbitrator
from src.clotho.orchestrator import create_clotho_graph

# [SRC:axis_12]
@pytest.mark.asyncio
async def test_ankyra_v2_atomic_anchors():
    """Verify Atomic Anchor & DB Persistence (Axis 7, 12)."""
    # 1. DB Persistence
    logger = setup_logger("test_v2")
    logger.info("Verification: SQLiteHandler writing to mnemosyne.db")
    
    conn = sqlite3.connect("data/mnemosyne.db")
    res = conn.execute("SELECT message FROM operational_logs_v2 ORDER BY id DESC LIMIT 1").fetchone()
    assert res and 'Verification' in res[0]  
    # 2. Atomic Anchors
    builder = AnchorContextBuilder()
    builder.add_fragment("test_frag", "This is an atomic fragment content", axis=12, precedence=150)
    xml = builder.build_anchors_xml()
    assert '<anchor id="test_frag"' in xml
    
    # 3. FIR Scoring
    arb = MemoryArbitrator()
    score_low = arb.score(importance=0.5, timestamp=0, frequency=1)
    score_high = arb.score(importance=0.5, timestamp=0, frequency=100)
    assert score_high > score_low
    
    # 4. Orchestrator Integration
    graph = create_clotho_graph()
    nodes = graph.nodes.keys()
    assert 'anchor_inject' in nodes
