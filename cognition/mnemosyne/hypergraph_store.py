import math
import threading
import time
from typing import Optional

import networkx as nx  # type: ignore
from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker

from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
from cognition.mnemosyne.models import MnemosyneBase
from src.utils.logging_config import setup_logger
from src.utils.project_path import to_absolute_path

logger = setup_logger(__name__)


# SQLAlchemy Mapped Models for Persistence
class SqlHyperedge(MnemosyneBase):
    __tablename__ = "hyperedges"
    edge_id = Column(String(64), primary_key=True)
    relation_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(Float, nullable=False)
    valid_until = Column(Float, nullable=True)


class SqlHypernode(MnemosyneBase):
    __tablename__ = "hypernodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    edge_id = Column(
        String(64), ForeignKey("hyperedges.edge_id", ondelete="CASCADE"), nullable=False
    )
    axis_id = Column(Integer, nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_key = Column(String(255), nullable=False)
    label = Column(String(255), default="")


class HypergraphStore:
    """[SRC:axis_15] In-memory networkx MultiDiGraph representing Mnemosyne Hypergraph, persistent via SQLite."""

    _instance: Optional["HypergraphStore"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_url: str | None = None):
        if getattr(self, "_initialized", False):
            return

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )

        # WAL Mode Configuration for SQLite Concurrency
        from sqlalchemy import event

        @event.listens_for(self.engine, "connect")
        def _set_wal_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self._graph = nx.MultiDiGraph()
        self._write_queue: list[Hyperedge] = []
        self._queue_lock = threading.Lock()

        # Load from SQLite database on startup
        self._load_from_db()
        self._initialized = True
        logger.info("[SRC:axis_15] HypergraphStore initialized successfully.")

    def _load_from_db(self) -> None:
        """Loads all nodes and edges from SQLite into in-memory networkx MultiDiGraph."""
        session = self.Session()
        try:
            sql_edges = session.query(SqlHyperedge).all()
            for se in sql_edges:
                # Get associated nodes
                sql_nodes = session.query(SqlHypernode).filter_by(edge_id=se.edge_id).all()
                nodes = [
                    HypernodeRef(
                        axis_id=sn.axis_id,
                        entity_type=sn.entity_type,
                        entity_key=sn.entity_key,
                        label=sn.label,
                    )
                    for sn in sql_nodes
                ]
                edge = Hyperedge(
                    nodes=nodes,
                    relation_type=se.relation_type,
                    weight=se.weight,
                    created_at=se.created_at,
                    valid_until=se.valid_until,
                    edge_id=se.edge_id,
                )
                self._add_to_graph_memory(edge)
            logger.info(
                f"[SRC:axis_15] Loaded {len(sql_edges)} hyperedges into in-memory networkx MultiDiGraph."
            )
        except Exception as e:
            logger.error(f"Failed to load Hypergraph from database: {e}", exc_info=True)
        finally:
            session.close()

    def _add_to_graph_memory(self, edge: Hyperedge) -> None:
        """Helper to inject a hyperedge into networkx in bipartite form."""
        edge_node_id = f"edge_{edge.edge_id}"

        # Add hyperedge as a special central node
        self._graph.add_node(
            edge_node_id,
            node_type="hyperedge",
            relation_type=edge.relation_type,
            weight=edge.weight,
            created_at=edge.created_at,
            valid_until=edge.valid_until,
        )

        for node in edge.nodes:
            node_id = node.to_node_id()
            # Ensure participant node exists
            if not self._graph.has_node(node_id):
                self._graph.add_node(
                    node_id,
                    node_type="hypernode",
                    axis_id=node.axis_id,
                    entity_type=node.entity_type,
                    entity_key=node.entity_key,
                    label=node.label,
                )

            # Bipartite mapping: directed connections in both directions
            self._graph.add_edge(node_id, edge_node_id)
            self._graph.add_edge(edge_node_id, node_id)

    def add_edge(self, edge: Hyperedge) -> str:
        """Adds a hyperedge to the in-memory graph instantly and queues it for batch persistence."""
        with self._lock:
            self._add_to_graph_memory(edge)

        with self._queue_lock:
            self._write_queue.append(edge)
            # Safe sync flushing inside the write calling context to avoid background scheduling issues
            if len(self._write_queue) >= 5:
                self.flush()

        return edge.edge_id

    def flush(self) -> None:
        """Synchronously persists all queued hyperedges to SQLite."""
        with self._queue_lock:
            if not self._write_queue:
                return
            edges_to_write = list(self._write_queue)
            self._write_queue.clear()

        session = self.Session()
        try:
            for edge in edges_to_write:
                # Idempotency: verify uniqueness
                existing = session.query(SqlHyperedge).filter_by(edge_id=edge.edge_id).first()
                if existing:
                    continue

                sql_edge = SqlHyperedge(
                    edge_id=edge.edge_id,
                    relation_type=edge.relation_type,
                    weight=edge.weight,
                    created_at=edge.created_at,
                    valid_until=edge.valid_until,
                )
                session.add(sql_edge)

                for node in edge.nodes:
                    sql_node = SqlHypernode(
                        edge_id=edge.edge_id,
                        axis_id=node.axis_id,
                        entity_type=node.entity_type,
                        entity_key=node.entity_key,
                        label=node.label,
                    )
                    session.add(sql_node)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"HypergraphStore: Flush transaction failed: {e}", exc_info=True)
        finally:
            session.close()

    def query_by_entity(self, axis_id: int, entity_key: str) -> list[Hyperedge]:
        """[SRC:axis_15] Queries all hyperedges in which a specific entity participates."""
        node_id = f"axis_{axis_id}:{entity_key}"
        possible_ids = [node_id]

        # Exact matching respecting the specific memory axis prefix
        for n in self._graph.nodes:
            if n.startswith("edge_"):
                continue
            parts = n.split(":", 2)
            if len(parts) >= 2:
                try:
                    n_axis = int(parts[0].replace("axis_", ""))
                    n_key = parts[-1]
                    if n_axis == axis_id and n_key == entity_key:
                        possible_ids.append(n)
                except ValueError:
                    pass

        edges = []
        with self._lock:
            for p_id in set(possible_ids):
                if not self._graph.has_node(p_id):
                    continue
                # Successors from node_id lead to the hyperedge nodes
                for neighbor in self._graph.successors(p_id):
                    if neighbor.startswith("edge_"):
                        edge_id = neighbor[5:]  # Precise slicing instead of greedy replace
                        edge_data = self._graph.nodes[neighbor]

                        # Reconstruct participant nodes from the bipartite graph
                        participant_node_ids = [
                            pred
                            for pred in self._graph.predecessors(neighbor)
                            if not pred.startswith("edge_")
                        ]
                        nodes = []
                        for p_node_id in participant_node_ids:
                            nd = self._graph.nodes[p_node_id]
                            nodes.append(
                                HypernodeRef(
                                    axis_id=nd["axis_id"],
                                    entity_type=nd["entity_type"],
                                    entity_key=nd["entity_key"],
                                    label=nd.get("label", ""),
                                )
                            )
                        edges.append(
                            Hyperedge(
                                nodes=nodes,
                                relation_type=edge_data["relation_type"],
                                weight=edge_data["weight"],
                                created_at=edge_data["created_at"],
                                valid_until=edge_data["valid_until"],
                                edge_id=edge_id,
                            )
                        )
        return edges

    def query_hop(self, start_node_id: str, k: int = 1) -> list[tuple[str, str, str]]:
        """[SRC:axis_15] Performs multi-hop traversal to find connected entities.
        Returns a list of relations as: (source_node_id, relation_type, target_node_id)
        """
        if not self._graph.has_node(start_node_id):
            return []

        visited = set()
        relations = []

        # BFS style search for k hops. Since it's a bipartite graph,
        # 1-hop between entities is exactly 2 edge traversals (A -> Edge -> B).
        # Therefore, we traverse up to 2 * k steps in networkx.
        queue = [(start_node_id, 0)]
        visited.add(start_node_id)

        with self._lock:
            while queue:
                curr_id, depth = queue.pop(0)
                if depth >= 2 * k:
                    continue

                # If current node is a hypernode, successor edges are hyperedge nodes
                if not curr_id.startswith("edge_"):
                    for edge_node in self._graph.successors(curr_id):
                        if edge_node.startswith("edge_") and edge_node not in visited:
                            visited.add(edge_node)
                            queue.append((edge_node, depth + 1))
                else:
                    # If current node is a hyperedge node, successor edges are other hypernodes
                    edge_data = self._graph.nodes[curr_id]
                    relation_type = edge_data["relation_type"]

                    # Find all hypernode endpoints connected to this hyperedge
                    endpoints = [
                        pred
                        for pred in self._graph.predecessors(curr_id)
                        if not pred.startswith("edge_")
                    ]

                    # Find the source nodes that directed us into this edge
                    sources = [
                        pred
                        for pred in self._graph.predecessors(curr_id)
                        if not pred.startswith("edge_") and pred in visited
                    ]

                    for src in sources:
                        for dest in endpoints:
                            if src != dest:
                                relations.append((src, relation_type, dest))
                                if dest not in visited:
                                    visited.add(dest)
                                    queue.append((dest, depth + 1))

        return relations

    def prune(self, threshold: float = 0.01) -> int:
        """[SRC:axis_15] Prunes expired or Ebbinghaus decayed hyperedges from in-memory and SQLite."""
        current_time = time.time()
        expired_edge_ids = []

        with self._lock:
            for node_id, data in list(self._graph.nodes(data=True)):
                if data.get("node_type") == "hyperedge":
                    edge_id = node_id[5:]  # Precise slicing instead of greedy replace

                    # Temporal validity expiration check
                    valid_until = data.get("valid_until")
                    if valid_until is not None and current_time > valid_until:
                        expired_edge_ids.append(edge_id)
                        continue

                    # Decayed weight check
                    weight = data.get("weight", 1.0)
                    created_at = data.get("created_at", current_time)
                    age_hours = (current_time - created_at) / 3600.0
                    decay_hours = 24.0 * (1.0 + 1.0 * weight)
                    decayed_weight = weight * math.exp(-age_hours / decay_hours)

                    if decayed_weight < threshold:
                        expired_edge_ids.append(edge_id)

            # Delete pruned edges from networkx memory graph
            for edge_id in expired_edge_ids:
                edge_node = f"edge_{edge_id}"
                if self._graph.has_node(edge_node):
                    self._graph.remove_node(edge_node)

        if not expired_edge_ids:
            return 0

        # Delete pruned edges from SQLite database
        session = self.Session()
        try:
            # SQLAlchemy CASCADE on SqlHypernode automatically purges nodes
            session.query(SqlHyperedge).filter(SqlHyperedge.edge_id.in_(expired_edge_ids)).delete(
                synchronize_session=False
            )
            session.commit()
            logger.info(
                f"[SRC:axis_15] Pruned {len(expired_edge_ids)} expired/decayed hyperedges from HypergraphStore."
            )
        except Exception as e:
            session.rollback()
            logger.error(
                f"HypergraphStore: Pruning database transaction failed: {e}", exc_info=True
            )
        finally:
            session.close()

        return len(expired_edge_ids)
