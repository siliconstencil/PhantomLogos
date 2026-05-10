import lancedb
import pandas as pd
import numpy as np
# [SRC:axis_6] Mnemosyne Semantic Vector Store
import os
import json
from typing import List, Dict, Any, Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class SemanticStore:
    """
    Mnemosyne Semantic Memory Layer using LanceDB.
    Supports Matryoshka 256 slicing for high-performance retrieval.
    """
    AXIS_ID = 6
    
    def __init__(self, db_path: str = "data/lancedb"):
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.table_name = "semantic_memory"
        self._ensure_table()
        self._cache_hits = 0
        self._cache_misses = 0

    def _ensure_table(self) -> None:
        """Initializes the table with a schema supporting Matryoshka embeddings and Session Isolation."""
        try:
            table_list = self.db.table_names()
            if self.table_name not in table_list:
                data = [{
                    "vector": np.zeros(256).tolist(),
                    "text": "Stylobate Initialized",
                    "session_id": "system",
                    "metadata": '{"axis": "system", "source": "init"}',
                    "importance": 1.0,
                    "timestamp": 0.0
                }]
                self.db.create_table(self.table_name, data=data)
                logger.info(f"LanceDB Table '{self.table_name}' created with 256-dim Matryoshka + Session Isolation.")
            else:
                self.table = self.db.open_table(self.table_name)
                # Note: In production, we would handle schema migration here if session_id is missing.
                logger.info(f"LanceDB Table '{self.table_name}' opened.")
            self._ensure_fts_index()
        except Exception as e:
            logger.error(f"SemanticStore (Axis {self.AXIS_ID}): _ensure_table failed ({e})", exc_info=True)

    def _ensure_fts_index(self) -> None:
        """Ensures Full-Text Search (FTS) index exists on the 'text' column for hybrid search."""
        try:
            table = self.db.open_table(self.table_name)
            # LanceDB create_fts_index is idempotent or handles existing index gracefully in v0.6+
            table.create_fts_index("text", replace=True)
            logger.info(f"SemanticStore: FTS index ensured on table '{self.table_name}' column 'text'.")
        except Exception as e:
            logger.warning(f"SemanticStore: FTS index creation/verification failed ({e})")

    def add_memories(self, texts: List[str], vectors: List[np.ndarray], metadata: List[Dict[str, Any]], session_id: str = "default") -> None:
        """Adds memories to the semantic store with session isolation."""
        try:
            table = self.db.open_table(self.table_name)
            records = []
            for text, vector, meta in zip(texts, vectors, metadata):
                records.append({
                    "vector": vector.tolist(),
                    "text": text,
                    "session_id": session_id,
                    "metadata": json.dumps(meta),
                    "importance": meta.get("importance", 0.5),
                    "timestamp": meta.get("timestamp", 0.0)
                })
            table.add(records)
            logger.info(f"Added {len(records)} memories to Mnemosyne for session {session_id}.")
        except Exception as e:
            logger.error(f"SemanticStore (Axis {self.AXIS_ID}): add_memories failed ({e})", exc_info=True)

    def search(self, query_vector: np.ndarray, session_id: str, limit: int = 5, mode: str = "hybrid", query_text: str = "") -> List[Dict[str, Any]]:
        """
        Performs a semantic, full-text, or hybrid search isolated by session_id.
        Hybrid mode uses Reciprocal Rank Fusion (RRF) to merge vector and FTS results.
        """
        try:
            # E1: Enforce global RAG limits from .env
            max_chunks = int(os.getenv("RAG_MAX_CHUNKS", "20"))
            limit = min(limit, max_chunks)
            
            safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
            table = self.db.open_table(self.table_name)
            
            results_vec = []
            results_fts = []

            # 1. Vector Search
            if mode in ("vector", "hybrid"):
                try:
                    if query_vector.shape[0] > 256:
                        query_vector = query_vector[:256]
                    results_vec = table.search(query_vector.tolist())\
                        .where(f"session_id = '{safe_session_id}'")\
                        .limit(limit * 2 if mode == "hybrid" else limit)\
                        .to_list()
                except Exception as ve:
                    logger.warning(f"SemanticStore: Vector search failed ({ve})")
                    results_vec = []

            # 2. FTS Search
            if mode in ("fts", "hybrid") and query_text:
                try:
                    results_fts = table.search(query_text)\
                        .where(f"session_id = '{safe_session_id}'")\
                        .limit(limit * 2 if mode == "hybrid" else limit)\
                        .to_list()
                except Exception as fe:
                    # Tantivy missing or index corrupted: log and fall back
                    logger.warning(f"SemanticStore: FTS search failed or tantivy missing ({fe})")
                    results_fts = []

            # 3. Merge / Hybrid logic
            if mode == "hybrid":
                if not results_fts:
                    # Graceful fallback to vector results if FTS is broken/missing
                    results = results_vec[:limit]
                elif not results_vec:
                    results = results_fts[:limit]
                else:
                    results = self._rrf_merge(results_vec, results_fts, limit=limit)
            elif mode == "fts":
                results = results_fts[:limit]
            else:
                results = results_vec[:limit]
            
            if results:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
                
            try:
                from .operational_store import OperationalStore
                op_store = OperationalStore()
                op_store.record_event(
                    name=f"semantic_cache.search.{mode}",
                    level="INFO",
                    message=f"Search for {safe_session_id}: {'HIT' if results else 'MISS'} (RRF merged if hybrid)",
                    agent_id=safe_session_id[:12]
                )
            except Exception as e:
                logger.warning(f"SemanticStore: Operational event recording failed ({e})")
                
            return results
        except Exception as e:
            logger.error(f"SemanticStore (Axis {self.AXIS_ID}): search failed for session {session_id} ({e})", exc_info=True)
            return []

    def _rrf_merge(self, results_vec: List[Dict], results_fts: List[Dict], limit: int, k: int = 60) -> List[Dict]:
        """Merges vector and FTS results using Reciprocal Rank Fusion (RRF)."""
        scores = {} # (text) -> total_rrf_score
        seen_docs = {} # (text) -> doc_dict

        # Rank vec results
        for i, doc in enumerate(results_vec):
            text = doc.get("text", "")
            if not text: continue
            scores[text] = scores.get(text, 0) + 1.0 / (k + i + 1)
            seen_docs[text] = doc

        # Rank FTS results
        for i, doc in enumerate(results_fts):
            text = doc.get("text", "")
            if not text: continue
            # If doc exists in both, scores accumulate
            scores[text] = scores.get(text, 0) + 1.0 / (k + i + 1)
            if text not in seen_docs:
                seen_docs[text] = doc

        # Sort by total RRF score
        sorted_texts = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [seen_docs[t] for t in sorted_texts[:limit]]

    def optimize(self) -> None:
        """Performs table optimization and cleans up old versions (D7)."""
        try:
            table = self.db.open_table(self.table_name)
            table.optimize()
            # cleanup_old_versions is a critical storage hardening step in Phase 11.9
            table.cleanup_old_versions()
            logger.info(f"SemanticStore: Table '{self.table_name}' optimized and old versions cleaned.")
        except Exception as e:
            logger.warning(f"SemanticStore: Optimization failed ({e})")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        store = SemanticStore()
        test_vec = np.random.rand(256)
        store.add_memories(
            ["Test Memory"], 
            [test_vec], 
            [{"axis": "test", "importance": 0.9, "timestamp": 123456789.0}],
            session_id="default"
        )
        search_res = store.search(test_vec, session_id="default", limit=1, query_text="Test")
        logger.info(f"Hybrid Search (with query_text) verification: {search_res[0]['text']}")
    else:
        logger.info("Usage: python semantic_store.py --test")

class FailureMemoryStore:
    """
    Axis 6 Extension (Phase 11.19): Vector-based retrieval for Prevention Rules.
    Separated from general semantic memory to avoid noise and context poisoning.
    """
    def __init__(self, db_path: str = "data/lancedb"):
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.table_name = "failure_memory"
        self._ensure_table()

    def _ensure_table(self):
        try:
            table_list = self.db.table_names()
            if self.table_name not in table_list:
                data = [{
                    "vector": np.zeros(256).tolist(),
                    "prevention_rule": "System Initialized",
                    "error_type": "init",
                    "context_hash": "0000000000000000",
                    "metadata": '{}',
                    "timestamp": 0.0
                }]
                self.db.create_table(self.table_name, data=data)
                logger.info(f"LanceDB Failure Table '{self.table_name}' created.")
            else:
                self.table = self.db.open_table(self.table_name)
        except Exception as e:
            logger.error(f"FailureMemoryStore: _ensure_table failed ({e})")

    def add_failure_vector(self, prevention_rule: str, vector: np.ndarray, error_type: str, context_hash: str, metadata: Dict[str, Any] = None):
        """Adds a failure rule vector for semantic retrieval."""
        try:
            table = self.db.open_table(self.table_name)
            if vector.shape[0] > 256:
                vector = vector[:256]
            
            record = {
                "vector": vector.tolist(),
                "prevention_rule": prevention_rule,
                "error_type": error_type,
                "context_hash": context_hash,
                "metadata": json.dumps(metadata or {}),
                "timestamp": metadata.get("timestamp", 0.0) if metadata else 0.0
            }
            # Note: Deduplication is handled primarily in SQLite (Axis 8).
            # We add to LanceDB to ensure the rule is searchable.
            table.add([record])
            logger.info(f"FailureMemoryStore: Semantic lesson indexed. Hash: {context_hash}")
        except Exception as e:
            logger.error(f"FailureMemoryStore: add_failure_vector failed ({e})")

    def search_similar_failures(self, query_vector: np.ndarray, limit: int = 3) -> List[Dict[str, Any]]:
        """Finds prevention rules related to the current task context."""
        try:
            table = self.db.open_table(self.table_name)
            if query_vector.shape[0] > 256:
                query_vector = query_vector[:256]
            
            return table.search(query_vector.tolist()).limit(limit).to_list()
        except Exception as e:
            logger.error(f"FailureMemoryStore: search_similar_failures failed ({e})")
            return []
