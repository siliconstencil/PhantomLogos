import sqlite3
import time

import pytest

from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
from cognition.mnemosyne.hypergraph_store import HypergraphStore, SqlHyperedge
from src.utils.project_path import to_absolute_path


def test_hypergraph_models_and_decay():
    # 1. Test Node Serialization
    node = HypernodeRef(axis_id=5, entity_type="module", entity_key="sweeper.py", label="Sweeper")
    assert node.to_node_id() == "axis_5:module:sweeper.py"

    rebuilt = HypernodeRef.from_node_id("axis_5:module:sweeper.py", label="Sweeper")
    assert rebuilt.axis_id == 5
    assert rebuilt.entity_type == "module"
    assert rebuilt.entity_key == "sweeper.py"

    # 2. Test Edge Deterministic Hash
    node2 = HypernodeRef(
        axis_id=8, entity_type="reflection", entity_key="ebbinghaus", label="Ebbinghaus"
    )
    edge = Hyperedge(nodes=[node, node2], relation_type="optimization")
    assert len(edge.edge_id) == 16

    # Determinism check (sorting order in nodes list shouldn't change the ID)
    edge_reverse = Hyperedge(nodes=[node2, node], relation_type="optimization")
    assert edge.edge_id == edge_reverse.edge_id

    # 3. Test Ebbinghaus Adaptive Decay Calculation
    t0 = time.time()
    decayed_init = edge.get_decayed_weight(current_time=t0)
    assert decayed_init == pytest.approx(1.0)

    # 48 hours age check (importance=1.0 -> decay half-life = 48h)
    t48 = t0 + 48.0 * 3600.0
    decayed_48 = edge.get_decayed_weight(current_time=t48)
    # expected decayed weight = 1.0 * exp(-48 / 48) = 1/e ~ 0.367
    assert 0.35 <= decayed_48 <= 0.38


def test_hypergraph_store_persistence():
    db_path = to_absolute_path("data/mnemosyne.db")
    store = HypergraphStore()

    # Cleanup previous test records if any
    session = store.Session()
    try:
        session.query(SqlHyperedge).filter(SqlHyperedge.edge_id.like("test_edge_%")).delete(
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()

    node1 = HypernodeRef(axis_id=5, entity_type="module", entity_key="sweeper.py", label="Sweeper")
    node2 = HypernodeRef(
        axis_id=1, entity_type="episodic", entity_key="session_test", label="TestSession"
    )
    edge = Hyperedge(nodes=[node1, node2], relation_type="maintenance", edge_id="test_edge_1")

    # Insert edge and trigger flush
    store.add_edge(edge)
    store.flush()

    # Query by SQLite direct connection
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT relation_type, weight FROM hyperedges WHERE edge_id='test_edge_1'")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "maintenance"
        assert row[1] == 1.0

        cursor.execute("SELECT axis_id, entity_key FROM hypernodes WHERE edge_id='test_edge_1'")
        rows = cursor.fetchall()
        assert len(rows) == 2
        keys = [r[1] for r in rows]
        assert "sweeper.py" in keys
        assert "session_test" in keys
    finally:
        conn.close()

    # Query via in-memory Graph Store
    queried_edges = store.query_by_entity(axis_id=5, entity_key="sweeper.py")
    assert len(queried_edges) > 0
    assert any(e.edge_id == "test_edge_1" for e in queried_edges)


def test_hypergraph_multi_hop_query():
    store = HypergraphStore()

    # Build Bipartite relations:
    # A (axis_5:module:sweeper.py) <-> Edge 1 (relation: trigger) <-> B (axis_8:failure:lock_error)
    # B (axis_8:failure:lock_error) <-> Edge 2 (relation: resolve) <-> C (axis_2:procedural:flush)

    nodeA = HypernodeRef(axis_id=5, entity_type="module", entity_key="sweeper.py", label="Sweeper")
    nodeB = HypernodeRef(
        axis_id=8, entity_type="failure", entity_key="lock_error", label="LockError"
    )
    nodeC = HypernodeRef(axis_id=2, entity_type="procedural", entity_key="flush", label="Flush")

    edge1 = Hyperedge(nodes=[nodeA, nodeB], relation_type="trigger", edge_id="test_edge_hop1")
    edge2 = Hyperedge(nodes=[nodeB, nodeC], relation_type="resolve", edge_id="test_edge_hop2")

    store.add_edge(edge1)
    store.add_edge(edge2)
    store.flush()

    # Query 2 Hops from nodeA to nodeC
    relations = store.query_hop(nodeA.to_node_id(), k=2)

    # Assertions
    assert len(relations) >= 2
    # Verify relations contains: (A, trigger, B) and (B, resolve, C)
    rel_map = {(r[0], r[1], r[2]) for r in relations}

    assert (nodeA.to_node_id(), "trigger", nodeB.to_node_id()) in rel_map
    assert (nodeB.to_node_id(), "resolve", nodeC.to_node_id()) in rel_map


def test_hypergraph_ebbinghaus_pruning():
    store = HypergraphStore()

    # Inject 2 edges: 1 active, 1 expired/decayed
    nodeA = HypernodeRef(axis_id=5, entity_type="module", entity_key="sweeper.py", label="Sweeper")
    nodeB = HypernodeRef(
        axis_id=1, entity_type="episodic", entity_key="session_test", label="TestSession"
    )

    # Edge 1: Active
    edge_active = Hyperedge(
        nodes=[nodeA, nodeB], relation_type="active", edge_id="test_edge_active"
    )

    # Edge 2: Expired 100 hours ago
    t_past = time.time() - 100.0 * 3600.0
    edge_expired = Hyperedge(
        nodes=[nodeA, nodeB],
        relation_type="expired",
        weight=0.1,
        created_at=t_past,
        edge_id="test_edge_expired",
    )

    store.add_edge(edge_active)
    store.add_edge(edge_expired)
    store.flush()

    # Verify both exist in DB
    session = store.Session()
    try:
        assert (
            session.query(SqlHyperedge).filter_by(edge_id="test_edge_expired").first() is not None
        )
        assert session.query(SqlHyperedge).filter_by(edge_id="test_edge_active").first() is not None
    finally:
        session.close()

    # Run pruning with threshold=0.15
    # The expired edge weight decayed to: 0.1 * exp(-100 / (24 * 1.1)) = 0.1 * exp(-3.78) ~ 0.0022 < 0.15 -> should prune!
    # The active edge decayed weight = 1.0 >= 0.15 -> should stay!
    pruned_count = store.prune(threshold=0.15)
    assert pruned_count >= 1

    # Verify expired was deleted and active remained
    session = store.Session()
    try:
        assert session.query(SqlHyperedge).filter_by(edge_id="test_edge_expired").first() is None
        assert session.query(SqlHyperedge).filter_by(edge_id="test_edge_active").first() is not None

        # Cleanup
        session.query(SqlHyperedge).filter(SqlHyperedge.edge_id.like("test_edge_%")).delete(
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()
