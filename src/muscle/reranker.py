import asyncio
import re
from typing import Any

import numpy as np

from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client
from src.utils.run_async import run_async

logger = setup_logger(__name__)


class JinaReranker:
    """
    Reranker using Ollama backend. [HH:MM AM/PM PT]
    Fixed thread-safety issues (dedicated asyncio loop) and N+1 embedding latency.
    """

    def __init__(self) -> None:
        self.client = get_ollama_client()
        from src.architrave.model_registry import get_embedding_model

        self.embedding_model = get_embedding_model()
        self.rerank_model = "jina-reranker-v3:latest"

    async def rerank_async(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> dict[str, Any]:
        """Async entry point for high-performance ranking."""
        if not documents:
            return {"results": [], "integrity_warning": "Empty document set"}

        return await self._execute_pipeline(query, documents, top_n)

    def rerank(self, query: str, documents: list[str], top_n: int = 5) -> dict[str, Any]:
        """Backward compatible sync entry point using dedicated asyncio loop thread."""
        return run_async(self.rerank_async(query, documents, top_n), timeout=60.0)

    async def _execute_pipeline(
        self, query: str, documents: list[str], top_n: int
    ) -> dict[str, Any]:
        embed_err = None
        # 1. Embeddings (Primary) - [TIER 2.4 BATCH OPTIMIZATION]
        try:
            return await self._rerank_embeddings(query, documents, top_n)
        except Exception as e:
            embed_err = e
            logger.warning(f"JinaReranker: Embedding rank failed ({e})")
        # 2. Jina Reranker (Secondary)
        try:
            return await self._rerank_jina(query, documents, top_n)
        except Exception as jina_err:
            logger.error(f"JinaReranker: Jina rank failed ({jina_err})")
            raise RuntimeError(
                f"JinaReranker: All ranking methods failed. Embedding error: {embed_err}. Jina error: {jina_err}"
            ) from jina_err

    async def _rerank_embeddings(
        self, query: str, documents: list[str], top_n: int
    ) -> dict[str, Any]:
        # Batching query and docs via gather
        tasks = [self.client.embeddings(model=self.embedding_model, prompt=query)]
        tasks.extend(
            self.client.embeddings(model=self.embedding_model, prompt=doc) for doc in documents
        )

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
