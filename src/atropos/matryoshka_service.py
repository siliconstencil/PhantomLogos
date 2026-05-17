import asyncio
import numpy as np
from typing import List, Union, Optional
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client
from src.architrave.base_models import ROLE_TO_MODEL

logger = setup_logger(__name__)

class MatryoshkaService:
    """
    Sovereign Matryoshka Representation Service (Axis 4).
    Enforces local Nomic MOE embeddings with dimension slicing.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MatryoshkaService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = get_ollama_client()
        self.models = ROLE_TO_MODEL.get("embedding", {})
        self.q8_model = self.models.get("primary", "nomic-embed-text-v2-moe-q8:latest")
        self.q16_model = self.models.get("quality", "nomic-embed-text-v2-moe-q16:latest")
        self._initialized = True
        logger.info("MatryoshkaService: Initialized (Axis 4).")

    async def _get_embedding(self, text: str, model: str) -> np.ndarray:
        """Internal helper for single embedding with hard_fail."""
        try:
            resp = await self.client.embeddings(model=model, prompt=text, options={"num_ctx": 8192})
            if "embedding" not in resp:
                raise RuntimeError(f"MatryoshkaService: No embedding in response for {model}")
            return np.array(resp["embedding"], dtype=np.float32)
        except Exception as e:
            logger.error(f"MatryoshkaService: Failed to get embedding from {model} ({e})")
            raise RuntimeError(f"MatryoshkaService: Model {model} is non-responsive or missing.")

    @staticmethod
    def _slice_and_normalize(vector: np.ndarray, target_dim: int) -> np.ndarray:
        """Applies Matryoshka slicing and L2 normalization."""
        sliced = vector[:target_dim].copy()
        norm = np.linalg.norm(sliced)
        if norm > 1e-10:
            return sliced / norm
        return sliced

    async def embed(self, texts: Union[str, List[str]], mode: str = "q8", target_dim: int = 256, prefix: Optional[str] = None) -> np.ndarray:
        """
        Embeds one or more texts using the specified mode and dimension.
        mode: 'q8' (Fast/Write), 'q16' (Quality/Read)
        """
        model = self.q16_model if mode == "q16" else self.q8_model
        
        def apply_prefix(t: str) -> str:
            # Phase 1.0.30: Prefix injection for Nomic MOE (SSOT)
            if not prefix: return t
            if t.startswith(prefix): return t
            return f"{prefix}{t}"

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

    async def embed_documents(self, texts: List[str], target_dim: int = 256) -> np.ndarray:
        """Convenience method for document batch embedding (adds search_document: prefix)."""
        return await self.embed(texts, mode="q16", target_dim=target_dim, prefix="search_document: ")


class MatryoshkaEmbedding:
    """
    Client-side Matryoshka Embedding Wrapper.
    Wraps any standard embedding function to perform dynamic dimension slicing and L2 normalization.
    """
    def __init__(self, embed_fn):
        self.embed_fn = embed_fn

    def embed_query(self, text: str, target_dim: int = 256) -> np.ndarray:
        vecs = self.embed_fn([text])
        vec = vecs[0]
        return MatryoshkaService._slice_and_normalize(vec, target_dim)

