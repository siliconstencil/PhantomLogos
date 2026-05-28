import datetime
import hashlib
import json
import os

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.utils.logging_config import setup_logger

from .semantic_store import SemanticStore

# [SRC:axis_14] Mnemosyne Visual Memory Store
# Implements Option A: Nomic Text Embeddings for Zero-VRAM overhead.

logger = setup_logger(__name__)
from .models import MnemosyneBase, VisualMemory


class VisualStore:
    AXIS_ID = 14
    MAX_RECORDS = 50
    RETENTION_DAYS = 30

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}, poolclass=NullPool
        )
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._semantic_store = None  # Lazy init

    @property
    def semantic_store(self):
        if self._semantic_store is None:
            self._semantic_store = SemanticStore()
        return self._semantic_store

    async def store_vision(
        self,
        image_path: str,
        description: str,
        variant: str = "primary",
        metadata: dict = None,
        session_id: str = "default",
    ):
        """Stores a visual memory with its Nomic text embedding."""
        image_hash = self._get_image_hash(image_path)
        vector = await self._get_text_embedding(description, is_query=False)

        session = self.Session()
        try:
            # 1. Persist to SQLite
            memory = VisualMemory(
                image_hash=image_hash,
                description=description,
                vector=vector.tobytes() if vector is not None else None,
                source_path=image_path,
                variant=variant,
                metadata_json=json.dumps(metadata or {}),
                session_id=session_id,
            )
            session.add(memory)
            session.commit()

            # 2. Persist to SemanticStore for hybrid search
            if vector is not None:
                self.semantic_store.add_memories(
                    [description],
                    [vector],
                    [
                        {
                            "axis": 14,
                            "variant": variant,
                            "image_hash": image_hash,
                            "source": image_path,
                        }
                    ],
                    session_id=session_id,
                )

            # 3. Enforce Retention Policies (D7: Circular Buffer)
            self._enforce_retention(session)

            logger.info(f"VisualStore: Memory stored. Hash: {image_hash[:8]}, Variant: {variant}")
        except Exception as e:
            session.rollback()
            logger.error(f"VisualStore: Failed to store vision ({e})")
        finally:
            session.close()

    async def search_similar(self, query_text: str, session_id: str, limit: int = 5):
        """Searches visual memories using SemanticStore's hybrid search."""
        vector = await self._get_text_embedding(query_text, is_query=True)
        if vector is None:
            return []

        # Axis 14 uses Axis 6 (Semantic) for retrieval
        results = self.semantic_store.search(
            query_vector=vector,
            session_id=session_id,
            limit=limit,
            mode="hybrid",
            query_text=query_text,
        )

        # Filter for Axis 14 only
        visual_results = []
        for res in results:
            meta = json.loads(res.get("metadata", "{}"))
            if meta.get("axis") == 14:
                visual_results.append(res)

        return visual_results

    def get_recent(self, session_id: str, limit: int = 5):
        """Retrieves the most recent visual memories for the session."""
        session = self.Session()
        try:
            memories = (
                session.query(VisualMemory)
                .filter(VisualMemory.session_id == session_id)
                .order_by(VisualMemory.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "description": m.description,
                    "variant": m.variant,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": json.loads(m.metadata_json),
                }
                for m in memories
            ]
        finally:
            session.close()

    def _get_image_hash(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            return "0" * 64
        sha256_hash = hashlib.sha256()
        try:
            with open(image_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return "error_hashing"

    async def _get_text_embedding(self, text: str, is_query: bool = False) -> np.ndarray:
        """[Phase 1.0.30] Standardized embedding via MatryoshkaService with Prefixes."""
        try:
            from src.utils.service_locator import get_matryoshka

            matryoshka = get_matryoshka()
            if not matryoshka:
                raise RuntimeError("MatryoshkaService not available.")

            if is_query:
                return await matryoshka.embed_query(text)
            else:
                return await matryoshka.embed_document(text)
        except Exception as e:
            logger.warning(f"VisualStore: Embedding generation failed ({e})")
            return None

    def _enforce_retention(self, session):
        """Enforces MAX_RECORDS and RETENTION_DAYS."""
        # 1. Count limit (LRU-like)
        count = session.query(VisualMemory).count()
        if count > self.MAX_RECORDS:
            to_delete = (
                session.query(VisualMemory)
                .order_by(VisualMemory.timestamp.asc())
                .limit(count - self.MAX_RECORDS)
                .all()
            )
            for item in to_delete:
                session.delete(item)
            logger.info(
                f"VisualStore: Pruned {len(to_delete)} old records due to MAX_RECORDS limit."
            )

        # 2. Time limit
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=self.RETENTION_DAYS)
        session.query(VisualMemory).filter(VisualMemory.timestamp < cutoff).delete()

        session.commit()


if __name__ == "__main__":
    # Quick sanity check
    store = VisualStore()
    logger.info("VisualStore initialized and schema verified.")
