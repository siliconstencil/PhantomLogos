import json

# [SRC:axis_6] Mnemosyne Semantic Vector Store
import os
from typing import Any

import lancedb
import numpy as np

from src.utils.logging_config import setup_logger
from src.utils.run_async import run_async

logger = setup_logger(__name__)


class SemanticStore:
    """
    Mnemosyne Semantic Memory Layer using LanceDB.
    Supports Matryoshka 256 slicing for high-performance retrieval.
    """

    AXIS_ID = 6

    def _is_slm_active(self) -> bool:
        if os.getenv("SLM_ENABLED", "true").lower() != "true":
            return False
        try:
            from src.architrave.mcp import get_slm_client

            return get_slm_client().health()
        except Exception:
            return False

    def __init__(self, db_path: str = "data/lancedb") -> None:
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.table_name = "semantic_memory"
        self._ensure_table()
        self._cache_hits = 0
        self._cache_misses = 0

        # Phase 1.0.29: Matryoshka Integration
        try:
            from src.utils.service_locator import get_matryoshka

            self.matryoshka = get_matryoshka()
        except Exception:
            self.matryoshka = None

    def _ensure_table(self) -> None:
        """Initializes the table with a schema supporting Matryoshka embeddings and Session Isolation."""
        try:
            table_list = self.db.table_names()
            if self.table_name not in table_list:
                data = [
                    {
                        "vector": np.zeros(256).tolist(),
                        "text": "Stylobate Initialized",
                        "session_id": "system",
                        "metadata": '{"axis": "system", "source": "init"}',
                        "importance": 1.0,
                        "timestamp": 0.0,
                    }
                ]
                self.db.create_table(self.table_name, data=data)
                logger.info(
                    f"LanceDB Table '{self.table_name}' created with 256-dim Matryoshka + Session Isolation."
                )
            else:
                self.table = self.db.open_table(self.table_name)
                # Note: In production, we would handle schema migration here if session_id is missing.
                logger.info(f"LanceDB Table '{self.table_name}' opened.")
            self._ensure_fts_index()
        except Exception as e:
            logger.error(
                f"SemanticStore (Axis {self.AXIS_ID}): _ensure_table failed ({e})", exc_info=True
            )

    def _ensure_fts_index(self) -> None:
        """Ensures Full-Text Search (FTS) index exists on the 'text' column for hybrid search."""
        try:
            table = self.db.open_table(self.table_name)
            # LanceDB create_fts_index is idempotent or handles existing index gracefully in v0.6+
            table.create_fts_index("text", replace=True)
            logger.info(
                f"SemanticStore: FTS index ensured on table '{self.table_name}' column 'text'."
            )
        except Exception as e:
            logger.warning(f"SemanticStore: FTS index creation/verification failed ({e})")

    def add_memories(
        self,
        texts: list[str],
        vectors: list[np.ndarray],
        metadata: list[dict[str, Any]],
        session_id: str = "default",
    ) -> None:
        """Adds memories to the semantic store with session isolation."""
        sliced_vectors = []
        for v in vectors:
            if self.matryoshka:
                sliced_vectors.append(self.matryoshka._slice_and_normalize(v, 256))
            else:
                # Fallback: slice raw if no service locator
                sliced = v[:256]
                norm = np.linalg.norm(sliced)
                sliced_vectors.append(sliced / norm if norm > 1e-10 else sliced)

        if self._is_slm_active():
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                for text, vector, meta in zip(texts, sliced_vectors, metadata, strict=False):
                    entry = {
                        "text": text,
                        "vector": vector.tolist() if hasattr(vector, "tolist") else list(vector),
                        "session_id": session_id,
                        "metadata": meta,
                        "importance": meta.get("importance", 0.5),
                        "timestamp": meta.get("timestamp", 0.0),
                    }
                    agent_id = meta.get("agent_id") or "system"
                    slm.remember(
                        entry, table_name=self.table_name, agent_id=agent_id, axis_id=self.AXIS_ID
                    )
                logger.info(f"SLM: Added {len(texts)} memories to SLM for session {session_id}.")
            except Exception as e:
                logger.error(f"SemanticStore: SLM add_memories failed ({e})")

        try:
            table = self.db.open_table(self.table_name)
            records = []
            for text, vector, meta in zip(texts, sliced_vectors, metadata, strict=False):
                records.append(
                    {
                        "vector": vector.tolist() if hasattr(vector, "tolist") else list(vector),
                        "text": text,
                        "session_id": session_id,
                        "metadata": json.dumps(meta),
                        "importance": meta.get("importance", 0.5),
                        "timestamp": meta.get("timestamp", 0.0),
                    }
                )
            table.add(records)
            logger.info(f"Added {len(records)} memories to Mnemosyne for session {session_id}.")
        except Exception as e:
            logger.error(
                f"SemanticStore (Axis {self.AXIS_ID}): add_memories failed ({e})", exc_info=True
            )

    def search(
        self,
        query_vector: np.ndarray | None = None,
        session_id: str = "default",
        limit: int = 5,
        mode: str = "hybrid",
        query_text: str = "",
    ) -> list[dict[str, Any]]:
        """
        Performs a semantic, full-text, or hybrid search isolated by session_id.
        Hybrid mode uses Reciprocal Rank Fusion (RRF) to merge vector and FTS results.
        query_vector can be None (auto-generate from query_text) or a numpy array.
        """
        # E1: Enforce global RAG limits from .env
        max_chunks = int(os.getenv("RAG_MAX_CHUNKS", "20"))
        limit = min(limit, max_chunks)

        results_slm = []
        if self._is_slm_active():
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                if query_vector is None and query_text and self.matryoshka:
                    query_vector = run_async(self.matryoshka.embed_query(query_text))
                query_str = query_text or (
                    str(query_vector.tolist())
                    if hasattr(query_vector, "tolist")
                    else str(query_vector)
                )
                results_slm = slm.search(
                    query=query_str,
                    limit=limit * 2,
                    table_name=self.table_name,
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(f"SemanticStore: SLM search failed ({e}). LanceDB fallback active.")

        try:
            safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
            table = self.db.open_table(self.table_name)

            results_vec = []
            results_fts = []

            # 1. Vector Search
            if mode in ("vector", "hybrid"):
                if query_vector is None and query_text and self.matryoshka:
                    # Generate embedding from text if vector is missing
                    query_vector = run_async(self.matryoshka.embed_query(query_text))

                if query_vector is not None:
                    try:
                        # Standardized 256-dim Matryoshka Vector
                        if self.matryoshka:
                            query_vector = self.matryoshka._slice_and_normalize(query_vector, 256)
                        else:
                            # Fallback: raw slicing
                            sliced = query_vector[:256]
                            norm = np.linalg.norm(sliced)
                            query_vector = sliced / norm if norm > 1e-10 else sliced

                        vec_list = (
                            query_vector.tolist()
                            if hasattr(query_vector, "tolist")
                            else list(query_vector)
                        )
                        results_vec = (
                            table.search(vec_list)
                            .where(
                                f"session_id IN ('{safe_session_id}', 'system', 'default', 'global')"
                            )
                            .limit(limit * 2 if mode == "hybrid" else limit)
                            .to_list()
                        )
                    except Exception as ve:
                        logger.warning(f"SemanticStore: Vector search failed ({ve})")
                        results_vec = []

            # 2. FTS Search
            if mode in ("fts", "hybrid") and query_text:
                try:
                    results_fts = (
                        table.search(query_text)
                        .where(
                            f"session_id IN ('{safe_session_id}', 'system', 'default', 'global')"
                        )
                        .limit(limit * 2 if mode == "hybrid" else limit)
                        .to_list()
                    )
                except Exception as fe:
                    # Tantivy missing or index corrupted: log and fall back
                    logger.warning(f"SemanticStore: FTS search failed or tantivy missing ({fe})")
                    results_fts = []

            # 3. Merge / Hybrid logic
            if mode == "hybrid":
                if results_slm:
                    # Merge SLM + LanceDB vector + LanceDB FTS via 3-way RRF
                    lists_to_merge = [results_slm]
                    if results_vec:
                        lists_to_merge.append(results_vec)
                    if results_fts:
                        lists_to_merge.append(results_fts)
                    results = self._rrf_merge(*lists_to_merge, limit=limit)
                elif not results_fts:
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
                    agent_id=safe_session_id[:12],
                )
            except Exception as e:
                logger.warning(f"SemanticStore: Operational event recording failed ({e})")

            return results
        except Exception as e:
            logger.error(
                f"SemanticStore (Axis {self.AXIS_ID}): search failed for session {session_id} ({e})",
                exc_info=True,
            )
            return []

    def _rrf_merge(self, *result_lists, limit: int, k: int = 60) -> list[dict]:
        """Merges N result lists (each with a "text" key) using Reciprocal Rank Fusion (RRF)."""
        scores = {}
        seen_docs = {}

        for results in result_lists:
            for i, doc in enumerate(results):
                text = doc.get("text", "") or doc.get("prevention_rule", "")
                if not text:
                    continue
                scores[text] = scores.get(text, 0) + 1.0 / (k + i + 1)
                if text not in seen_docs:
                    seen_docs[text] = doc

        sorted_texts = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [seen_docs[t] for t in sorted_texts[:limit]]

    def optimize(self) -> None:
        """Performs table optimization and cleans up old versions (D7)."""
        try:
            table = self.db.open_table(self.table_name)
            table.optimize()
            # cleanup_old_versions is a critical storage hardening step in Phase 11.9
            table.cleanup_old_versions()
            logger.info(
                f"SemanticStore: Table '{self.table_name}' optimized and old versions cleaned."
            )
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
            session_id="default",
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

    def _is_slm_active(self) -> bool:
        if os.getenv("SLM_ENABLED", "true").lower() != "true":
            return False
        try:
            from src.architrave.mcp import get_slm_client

            return get_slm_client().health()
        except Exception:
            return False

    def __init__(self, db_path: str = "data/lancedb") -> None:
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.table_name = "failure_memory"
        self._ensure_table()
        try:
            from src.utils.service_locator import get_matryoshka

            self.matryoshka = get_matryoshka()
        except Exception:
            self.matryoshka = None

    def _ensure_table(self) -> None:
        try:
            table_list = self.db.table_names()
            if self.table_name not in table_list:
                data = [
                    {
                        "vector": np.zeros(256).tolist(),
                        "prevention_rule": "System Initialized",
                        "error_type": "init",
                        "context_hash": "0000000000000000",
                        "metadata": "{}",
                        "timestamp": 0.0,
                        "session_id": "default",
                    }
                ]
                self.db.create_table(self.table_name, data=data)
                logger.info(f"LanceDB Failure Table '{self.table_name}' created.")
            else:
                self.table = self.db.open_table(self.table_name)
        except Exception as e:
            logger.error(f"FailureMemoryStore: _ensure_table failed ({e})")

    def add_failure_vector(
        self,
        prevention_rule: str,
        vector: np.ndarray,
        error_type: str,
        context_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Adds a failure rule vector for semantic retrieval."""
        if self.matryoshka:
            vector = self.matryoshka._slice_and_normalize(vector, 256)
        else:
            sliced = vector[:256]
            norm = np.linalg.norm(sliced)
            vector = sliced / norm if norm > 1e-10 else sliced

        if self._is_slm_active():
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                record = {
                    "vector": vector.tolist() if hasattr(vector, "tolist") else list(vector),
                    "prevention_rule": prevention_rule,
                    "error_type": error_type,
                    "context_hash": context_hash,
                    "metadata": metadata or {},
                    "timestamp": metadata.get("timestamp", 0.0) if metadata else 0.0,
                    "session_id": (metadata or {}).get("session_id") or "default",
                }
                agent_id = (metadata or {}).get("agent_id") or "system"
                slm.remember(record, table_name=self.table_name, agent_id=agent_id, axis_id=6)
                logger.info(f"SLM: Indexed failure memory lesson. Hash: {context_hash}")
            except Exception as e:
                logger.error(f"FailureMemoryStore: SLM add_failure_vector failed ({e})")

        try:
            table = self.db.open_table(self.table_name)

            vec_list = vector.tolist() if hasattr(vector, "tolist") else list(vector)
            record = {
                "vector": vec_list,
                "prevention_rule": prevention_rule,
                "error_type": error_type,
                "context_hash": context_hash,
                "metadata": json.dumps(metadata or {}),
                "timestamp": metadata.get("timestamp", 0.0) if metadata else 0.0,
                "session_id": (metadata or {}).get("session_id") or "default",
            }
            # Note: Deduplication is handled primarily in SQLite (Axis 8).
            # We add to LanceDB to ensure the rule is searchable.
            table.add([record])
            logger.info(f"FailureMemoryStore: Semantic lesson indexed. Hash: {context_hash}")
        except Exception as e:
            logger.error(f"FailureMemoryStore: add_failure_vector failed ({e})")

    def search_similar_failures(
        self, query_vector: np.ndarray, limit: int = 3, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Finds prevention rules related to the current task context."""
        session_id = session_id or "default"
        if self.matryoshka:
            query_vector = self.matryoshka._slice_and_normalize(query_vector, 256)
        else:
            sliced = query_vector[:256]
            norm = np.linalg.norm(sliced)
            query_vector = sliced / norm if norm > 1e-10 else sliced

        if self._is_slm_active():
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                query_str = (
                    str(query_vector.tolist())
                    if hasattr(query_vector, "tolist")
                    else str(query_vector)
                )
                results = slm.search(
                    query=query_str, limit=limit, table_name=self.table_name, session_id=session_id
                )
                if results:
                    return results
            except Exception as e:
                logger.error(
                    f"FailureMemoryStore: SLM search failed ({e}). Falling back to LanceDB."
                )

        try:
            table = self.db.open_table(self.table_name)
            vec_list = (
                query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            )

            schema = table.schema
            has_session_id = "session_id" in schema.names

            q = table.search(vec_list)
            if has_session_id and session_id:
                safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
                q = q.where(f"session_id IN ('{safe_session_id}', 'system', 'default', 'global')")
            return q.limit(limit).to_list()
        except Exception as e:
            logger.error(f"FailureMemoryStore: search_similar_failures failed ({e})")
            return []
