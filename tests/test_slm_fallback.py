import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np

# Set environment variables for test
os.environ["SLM_ENABLED"] = "true"
os.environ["SLM_ENDPOINT"] = "http://localhost:8081"
os.environ["RAG_MAX_CHUNKS"] = "20"

import contextlib

from cognition.mnemosyne.semantic_store import FailureMemoryStore, SemanticStore
from src.atropos.matryoshka_service import MatryoshkaService
from src.clotho.bridge.retrieval import _check_embedding_health, _rerank_results


class TestSLMFallback(unittest.IsolatedAsyncioTestCase):
    """
    Test suite verifying that client fallback to LanceDB, Jina, and local models
    works perfectly when SLM is enabled but down (unhealthy).
    """

    @patch("src.architrave.mcp.get_slm_client")
    async def test_semantic_store_fallback_on_unhealthy_slm(self, mock_get_client):
        # Mock SLM client to be unhealthy
        mock_slm = MagicMock()
        mock_slm.health.return_value = False
        mock_slm.ahealth = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_slm

        # Initialize SemanticStore
        store = SemanticStore(db_path="data/lancedb_test_fallback")

        # Since SLM is down, _is_slm_active() should return False
        self.assertFalse(store._is_slm_active())

        # Test add_memories falls back to LanceDB successfully
        test_vec = np.random.rand(256)
        try:
            store.add_memories(
                texts=["Test Fallback Memory"],
                vectors=[test_vec],
                metadata=[{"importance": 0.8, "timestamp": 100.0}],
                session_id="test_fallback_session",
            )
            # Verify it is stored in local LanceDB table
            results = store.search(
                test_vec, session_id="test_fallback_session", limit=1, mode="vector"
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["text"], "Test Fallback Memory")
        finally:
            # Cleanup local test DB table
            with contextlib.suppress(Exception):
                store.db.drop_table(store.table_name)

    @patch("src.architrave.mcp.get_slm_client")
    async def test_failure_memory_store_fallback_on_unhealthy_slm(self, mock_get_client):
        # Mock SLM client to be unhealthy
        mock_slm = MagicMock()
        mock_slm.health.return_value = False
        mock_slm.ahealth = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_slm

        # Initialize FailureMemoryStore
        fm_store = FailureMemoryStore(db_path="data/lancedb_test_fallback")

        # Since SLM is down, _is_slm_active() should return False
        self.assertFalse(fm_store._is_slm_active())

        test_vec = np.random.rand(256)
        try:
            fm_store.add_failure_vector(
                prevention_rule="Test Prevention Rule",
                vector=test_vec,
                error_type="test_error",
                context_hash="12345abcde",
                metadata={"timestamp": 200.0},
            )
            # Verify search falls back to LanceDB
            results = fm_store.search_similar_failures(test_vec, limit=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["prevention_rule"], "Test Prevention Rule")
        finally:
            with contextlib.suppress(Exception):
                fm_store.db.drop_table(fm_store.table_name)

    @patch("src.architrave.mcp.get_slm_client")
    @patch("src.utils.ollama_utils.get_ollama_client")
    async def test_matryoshka_service_fallback_on_unhealthy_slm(self, mock_ollama, mock_get_client):
        # Mock SLM client to be unhealthy
        mock_slm = MagicMock()
        mock_slm.health.return_value = False
        mock_slm.ahealth = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_slm

        # Mock Ollama embedding client returning dict for dict access compatibility
        mock_ollama_client = AsyncMock()
        mock_ollama_client.embeddings.return_value = {"embedding": np.random.rand(768).tolist()}
        mock_ollama.return_value = mock_ollama_client

        # Initialize MatryoshkaService and assign mocked client to singleton instance
        service = MatryoshkaService()
        service.client = mock_ollama_client

        # Verify active check returns False
        self.assertFalse(service._is_slm_active())

        # Test embed falls back to local Ollama
        vec = await service.embed("Test Text")
        self.assertEqual(vec.shape[0], 256)  # Matryoshka sliced to 256 dimensions
        mock_ollama_client.embeddings.assert_called_once()

    @patch("src.architrave.mcp.get_slm_client")
    @patch("src.clotho.bridge.retrieval.get_ollama_client")
    async def test_bridge_retrieval_fallback_on_unhealthy_slm(self, mock_ollama, mock_get_client):
        # Mock SLM client to be unhealthy
        mock_slm = MagicMock()
        mock_slm.health.return_value = False
        mock_slm.ahealth = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_slm

        # Mock Ollama embedding client
        mock_ollama_client = AsyncMock()
        mock_ollama_client.embeddings.return_value = {"embedding": np.random.rand(768).tolist()}
        mock_ollama.return_value = mock_ollama_client

        mock_bridge = MagicMock()
        mock_bridge._resolve_model.return_value = "nomic-embed-text"

        # Force _check_embedding_health to trigger by setting _embedding_healthy to False
        import src.clotho.bridge.retrieval as ret

        ret._embedding_healthy = False

        # Verify health check falls back to checking local Ollama health
        is_healthy = await _check_embedding_health(mock_bridge)
        self.assertTrue(is_healthy)
        mock_ollama_client.embeddings.assert_called_once_with(
            model="nomic-embed-text", prompt="health"
        )

        # Test rerank results falls back to Jina Reranker
        with patch("src.muscle.reranker.JinaReranker") as mock_jina_class:
            mock_jina_inst = MagicMock()
            mock_jina_inst.rerank.return_value = {
                "results": [{"index": 0, "score": 0.99}],
                "integrity_warning": None,
            }
            mock_jina_class.return_value = mock_jina_inst

            candidates = [{"text": "Candidate 1", "session_id": "session_1"}]
            rerank_res = _rerank_results("test query", candidates)

            self.assertEqual(len(rerank_res["results"]), 1)
            self.assertEqual(rerank_res["results"][0]["rerank_score"], 0.99)
            mock_jina_inst.rerank.assert_called_once()

    @patch("src.architrave.mcp.get_slm_client")
    async def test_bridge_retrieval_healthy_slm(self, mock_get_client):
        # Mock SLM client to be healthy and returning valid rerank result
        mock_slm = MagicMock()
        mock_slm.health.return_value = True
        mock_slm.ahealth = AsyncMock(return_value=True)
        mock_slm.rerank.return_value = {
            "results": [{"index": 0, "score": 0.95}],
            "integrity_warning": None,
        }
        mock_get_client.return_value = mock_slm

        candidates = [{"text": "Candidate 1", "session_id": "session_1"}]
        rerank_res = _rerank_results("test query", candidates)

        self.assertEqual(len(rerank_res["results"]), 1)
        self.assertEqual(rerank_res["results"][0]["rerank_score"], 0.95)
        mock_slm.rerank.assert_called_once()

    @patch("src.architrave.mcp.get_slm_client")
    async def test_bridge_retrieval_slm_rerank_fail_fallback(self, mock_get_client):
        # Mock SLM client to be healthy but rerank fails
        mock_slm = MagicMock()
        mock_slm.health.return_value = True
        mock_slm.ahealth = AsyncMock(return_value=True)
        mock_slm.rerank.side_effect = Exception("Rerank error")
        mock_get_client.return_value = mock_slm

        with patch("src.muscle.reranker.JinaReranker") as mock_jina_class:
            mock_jina_inst = MagicMock()
            mock_jina_inst.rerank.return_value = {
                "results": [{"index": 0, "score": 0.88}],
                "integrity_warning": None,
            }
            mock_jina_class.return_value = mock_jina_inst

            candidates = [{"text": "Candidate 1", "session_id": "session_1"}]
            rerank_res = _rerank_results("test query", candidates)

            self.assertEqual(len(rerank_res["results"]), 1)
            self.assertEqual(rerank_res["results"][0]["rerank_score"], 0.88)
            mock_slm.rerank.assert_called_once()
            mock_jina_inst.rerank.assert_called_once()

    @patch("src.architrave.mcp.get_slm_client")
    async def test_dual_write_semantic_store(self, mock_get_client):
        mock_slm = MagicMock()
        mock_slm.health.return_value = True
        mock_slm.ahealth = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_slm

        store = SemanticStore(db_path="data/lancedb_test_fallback")
        self.assertTrue(store._is_slm_active())

        test_vec = np.ones(256)
        try:
            store.add_memories(
                texts=["Dual Write Text"],
                vectors=[test_vec],
                metadata=[{"importance": 0.9, "timestamp": 123.0}],
                session_id="my-dual-session",
            )
            # Verify SLM remember was called
            mock_slm.remember.assert_called_once()

            # Verify LanceDB write also happened (dual-write)
            tbl = store.db.open_table(store.table_name)
            res = tbl.search(test_vec.tolist()).to_list()
            self.assertTrue(any(r["text"] == "Dual Write Text" for r in res))
        finally:
            with contextlib.suppress(Exception):
                store.db.drop_table(store.table_name)

    @patch("src.architrave.mcp.get_slm_client")
    async def test_dual_write_failure_store(self, mock_get_client):
        mock_slm = MagicMock()
        mock_slm.health.return_value = True
        mock_slm.ahealth = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_slm

        fm_store = FailureMemoryStore(db_path="data/lancedb_test_fallback")
        self.assertTrue(fm_store._is_slm_active())

        test_vec = np.ones(256)
        try:
            fm_store.add_failure_vector(
                prevention_rule="Dual Failure Rule",
                vector=test_vec,
                error_type="dual_error",
                context_hash="dualhash123",
                metadata={"timestamp": 321.0},
            )
            # Verify SLM remember was called
            mock_slm.remember.assert_called_once()

            # Verify LanceDB write also happened (dual-write)
            tbl = fm_store.db.open_table(fm_store.table_name)
            res = tbl.search(test_vec.tolist()).to_list()
            self.assertTrue(any(r["prevention_rule"] == "Dual Failure Rule" for r in res))
        finally:
            with contextlib.suppress(Exception):
                fm_store.db.drop_table(fm_store.table_name)

    @patch("src.architrave.mcp.get_slm_client")
    async def test_failure_search_session_isolation(self, mock_get_client):
        mock_slm = MagicMock()
        mock_slm.health.return_value = True
        mock_slm.ahealth = AsyncMock(return_value=True)
        mock_slm.search.return_value = [{"prevention_rule": "SLM rule"}]
        mock_get_client.return_value = mock_slm

        fm_store = FailureMemoryStore(db_path="data/lancedb_test_fallback")
        test_vec = np.ones(256)

        try:
            res = fm_store.search_similar_failures(
                test_vec, limit=5, session_id="my-special-session"
            )
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["prevention_rule"], "SLM rule")

            # Verify search was called on SLM with session_id
            mock_slm.search.assert_called_once()
            kwargs = mock_slm.search.call_args[1]
            self.assertEqual(kwargs.get("session_id"), "my-special-session")
        finally:
            with contextlib.suppress(Exception):
                fm_store.db.drop_table(fm_store.table_name)
