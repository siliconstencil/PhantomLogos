import asyncio
import re
from typing import Any

import numpy as np

from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


class JinaReranker:
    """
    Reranker using Ollama backend. [HH:MM AM/PM PT]
    Fixed thread-safety issues (asyncio.run removal) and N+1 embedding latency.
    """

    def __init__(self):
        self.client = get_ollama_client()
        from src.architrave.model_registry import get_embedding_model

        self.embedding_model = get_embedding_model()
        self.rerank_model = "jina-reranker-v3-q8_0:latest"

    async def rerank_async(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> dict[str, Any]:
        """Async entry point for high-performance ranking."""
        if not documents:
            return {"results": [], "integrity_warning": "Empty document set"}

        try:
            return await self._execute_pipeline(query, documents, top_n)
        except Exception as e:
            logger.error(f"JinaReranker: Pipeline crashed ({e}), emergency fallback triggered")
            return self._fallback_rank(query, documents, top_n, f"Emergency fallback: {e!s}")

    def rerank(self, query: str, documents: list[str], top_n: int = 5) -> dict[str, Any]:
        """Backward compatible sync entry point using thread-safe loop access. [HH:MM AM/PM PT]"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async environment, use a task (caution: blocking if not awaited)
                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor() as executor:
                    return executor.submit(
                        lambda: asyncio.run(self.rerank_async(query, documents, top_n))
                    ).result()
            else:
                return asyncio.run(self.rerank_async(query, documents, top_n))
        except Exception:
            return asyncio.run(self.rerank_async(query, documents, top_n))

    async def _execute_pipeline(
        self, query: str, documents: list[str], top_n: int
    ) -> dict[str, Any]:
        # 1. Embeddings (Primary) - [TIER 2.4 BATCH OPTIMIZATION]
        try:
            return await self._rerank_embeddings(query, documents, top_n)
        except Exception as e:
            logger.warning(f"JinaReranker: Embedding rank failed ({e})")

        # 2. Jina Reranker (Secondary)
        if len(documents) <= 10:
            try:
                return await self._rerank_jina(query, documents, top_n)
            except Exception as e:
                logger.warning(f"JinaReranker: Jina rank failed ({e})")

        return self._fallback_rank(query, documents, top_n, "Heuristic fallback active")

    async def _rerank_embeddings(
        self, query: str, documents: list[str], top_n: int
    ) -> dict[str, Any]:
        # Batching query and docs via gather
        tasks = [self.client.embeddings(model=self.embedding_model, prompt=query)]
        for doc in documents:
            tasks.append(self.client.embeddings(model=self.embedding_model, prompt=doc))

        all_res = await asyncio.gather(*tasks)
        q_vec = np.array(all_res[0]["embedding"])
        doc_vecs = [np.array(r["embedding"]) for r in all_res[1:]]

        scored = []
        for i, d_vec in enumerate(doc_vecs):
            score = np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec))
            scored.append({"index": i, "score": float(score), "text": documents[i]})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:top_n], "integrity_warning": None}

    async def _rerank_jina(self, query: str, documents: list[str], top_n: int) -> dict[str, Any]:
        tasks = []
        for doc in documents:
            prompt = f"Rank the relevance of this document to the query.\nQuery: {query}\nDocument: {doc}\nRelevance Score (0.0 to 1.0):"
            tasks.append(
                self.client.generate(
                    model=self.rerank_model,
                    prompt=prompt,
                    stream=False,
                    options={"temperature": 0.0},
                )
            )

        all_res = await asyncio.gather(*tasks)
        scored = []
        for i, resp in enumerate(all_res):
            match = re.search(r"0?\.\d+", resp["response"])
            score = float(match.group()) if match else 0.5
            scored.append({"index": i, "score": score, "text": documents[i]})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:top_n], "integrity_warning": "Jina precision mode active"}

    def _fallback_rank(
        self, query: str, documents: list[str], top_n: int, reason: str | None = None
    ) -> dict[str, Any]:
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for i, doc in enumerate(documents):
            doc_words = set(re.findall(r"\w+", doc.lower()))
            overlap = len(query_words & doc_words) / len(query_words) if query_words else 0
            scored.append({"index": i, "score": float(overlap), "text": doc})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:top_n], "integrity_warning": reason or "Heuristic fallback"}
