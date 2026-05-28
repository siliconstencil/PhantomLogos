import asyncio
from collections.abc import Callable
from typing import Self

import numpy as np

from src.architrave.base_models import ROLE_TO_MODEL
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


class MatryoshkaService:
    """
    Sovereign Matryoshka Representation Service (Axis 4).
    Enforces local Nomic MOE embeddings with dimension slicing.
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.models = ROLE_TO_MODEL.get("embedding", {})
        self.q8_model = self.models.get("primary", "nomic-embed-text-v2-moe-q8:latest")
        self.q16_model = self.models.get("quality", "nomic-embed-text-v2-moe-q16:latest")
        self._initialized = True
        logger.info("MatryoshkaService: Initialized (Axis 4).")

    def _is_slm_active(self) -> bool:
        import os

        if os.getenv("SLM_ENABLED", "true").lower() != "true":
            return False
        try:
            from src.architrave.mcp import get_slm_client

            return get_slm_client().health()
        except Exception:
            return False

    async def _get_embedding(self, text: str, model: str) -> np.ndarray:
        """Internal helper for single embedding with hard_fail."""
        try:
            client = get_ollama_client()
            resp = await client.embeddings(model=model, prompt=text, options={"num_ctx": 8192})
            if "embedding" not in resp:
                raise RuntimeError(f"MatryoshkaService: No embedding in response for {model}")
            return np.array(resp["embedding"], dtype=np.float32)
        except Exception as e:
            logger.error(f"MatryoshkaService: Failed to get embedding from {model} ({e})")
            raise RuntimeError(
                f"MatryoshkaService: Model {model} is non-responsive or missing."
            ) from e

    @staticmethod
    def _slice_and_normalize(vector: np.ndarray, target_dim: int) -> np.ndarray:
        """Applies Matryoshka slicing and L2 normalization."""
        sliced = vector[:target_dim].copy()
        norm = np.linalg.norm(sliced)
        if norm > 1e-10:
            return sliced / norm
        return sliced

    async def embed(
        self,
        texts: str | list[str],
        mode: str = "q8",
        target_dim: int = 256,
        prefix: str | None = None,
    ) -> np.ndarray:
        """
        Embeds one or more texts using the specified mode and dimension.
        mode: 'q8' (Fast/Write), 'q16' (Quality/Read)
        """

        def apply_prefix(t: str) -> str:
            # Phase 1.0.30: Prefix injection for Nomic MOE (SSOT)
            if not prefix:
                return t
            if t.startswith(prefix):
                return t
            return f"{prefix}{t}"

        if self._is_slm_active():
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                if isinstance(texts, str):
                    text_to_embed = apply_prefix(texts)
                    vec = await slm.aembed(text_to_embed)
                    if vec:
                        return self._slice_and_normalize(
                            np.array(vec, dtype=np.float32), target_dim
                        )
                else:
                    prefixed_texts = [apply_prefix(t) for t in texts]
                    tasks = [slm.aembed(t) for t in prefixed_texts]
                    vectors = await asyncio.gather(*tasks)
                    if all(vectors):
                        processed = [
                            self._slice_and_normalize(np.array(v, dtype=np.float32), target_dim)
                            for v in vectors
                        ]
                        return np.stack(processed)
            except Exception as e:
                logger.error(
                    f"MatryoshkaService: SLM aembed failed ({e}). Falling back to local Ollama."
                )

        model = self.q16_model if mode == "q16" else self.q8_model

        if isinstance(texts, str):
            text_to_embed = apply_prefix(texts)
            vec = await self._get_embedding(text_to_embed, model)
            return self._slice_and_normalize(vec, target_dim)

        # Batch processing via gather
        prefixed_texts = [apply_prefix(t) for t in texts]
        tasks = [self._get_embedding(t, model) for t in prefixed_texts]
        vectors = await asyncio.gather(*tasks)

        processed = [self._slice_and_normalize(v, target_dim) for v in vectors]
        return np.stack(processed)

    async def embed_query(self, text: str, target_dim: int = 256) -> np.ndarray:
        """Convenience method for query embedding (adds search_query: prefix)."""
        return await self.embed(text, mode="q8", target_dim=target_dim, prefix="search_query: ")

    async def embed_document(self, text: str, target_dim: int = 256) -> np.ndarray:
        """Convenience method for document embedding (adds search_document: prefix)."""
        return await self.embed(text, mode="q16", target_dim=target_dim, prefix="search_document: ")

    async def embed_documents(self, texts: list[str], target_dim: int = 256) -> np.ndarray:
        """Convenience method for document batch embedding (adds search_document: prefix)."""
        return await self.embed(
            texts, mode="q16", target_dim=target_dim, prefix="search_document: "
        )


class MatryoshkaEmbedding:
    """
    Client-side Matryoshka Embedding Wrapper.
    Wraps any standard embedding function to perform dynamic dimension slicing and L2 normalization.
    """

    def __init__(self, embed_fn: Callable) -> None:
        self.embed_fn = embed_fn

    def embed_query(self, text: str, target_dim: int = 256) -> np.ndarray:
        vecs = self.embed_fn([text])
        vec = vecs[0]
        return MatryoshkaService._slice_and_normalize(vec, target_dim)
