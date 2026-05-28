"""
Architrave Context Cache Store.
Manages Sovereign Gateway explicit caching for 1-hour TTL context anchors.
"""

import hashlib
import os
import sqlite3
import threading
import time

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

logger = setup_logger(__name__)


class ContextCacheStore:
    """
    Persistent context cache using mnemosyne.db (Axis 12).
    """

    AXIS_ID = 12
    MAX_TOTAL_SIZE_BYTES = 50 * 1024 * 1024

    def __init__(
        self, db_path: str | None = None, start_sweep: bool = True, sweep_interval: float = 60.0
    ) -> None:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = db_path or os.path.join(base, "data", "mnemosyne.db")
        self._lock = threading.Lock()
        self._ensure_table()

        # Background sweeper thread
        self._stop_sweep = threading.Event()
        self._sweep_thread = None
        if start_sweep:
            self._start_background_sweep(sweep_interval)

    def _start_background_sweep(self, sweep_interval: float) -> None:
        def sweep_loop() -> None:
            while not self._stop_sweep.is_set():
                try:
                    self.purge_expired()
                except Exception as e:
                    logger.error(f"ContextCacheStore: Background sweep error ({e})")

                # Check stop event every 1 second to allow fast shutdown
                slept = 0.0
                while slept < sweep_interval and not self._stop_sweep.is_set():
                    time.sleep(min(1.0, sweep_interval - slept))
                    slept += 1.0

        self._sweep_thread = threading.Thread(target=sweep_loop, daemon=True)
        self._sweep_thread.start()

    def close(self) -> None:
        """Stops the background sweeper thread."""
        self._stop_sweep.set()
        if self._sweep_thread and self._sweep_thread.is_alive():
            self._sweep_thread.join(timeout=2.0)

    def _ensure_table(self) -> None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS context_cache (
                        key TEXT PRIMARY KEY,
                        content TEXT,
                        expires_at FLOAT,
                        created_at FLOAT,
                        size_bytes INTEGER
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    def _hash_key(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, content: str) -> str | None:
        key = self._hash_key(content)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content, expires_at FROM context_cache WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
            finally:
                conn.close()

        if row:
            return row[0]
        return None

    def get_by_key(self, key: str) -> str | None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content, expires_at FROM context_cache WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
            finally:
                conn.close()

        if row and row[1] > time.time():
            return row[0]
        return None

    def set_by_key(self, key: str, content: str, ttl_seconds: int = 3600) -> bool:
        now = time.time()
        entry_size = len(content.encode("utf-8"))
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM context_cache")
                total_size = cursor.fetchone()[0]
                while total_size + entry_size > self.MAX_TOTAL_SIZE_BYTES:
                    cursor.execute(
                        "SELECT key, size_bytes FROM context_cache ORDER BY created_at ASC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    if not row:
                        break
                    cursor.execute("DELETE FROM context_cache WHERE key = ?", (row[0],))
                    total_size -= row[1]
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO context_cache (key, content, expires_at, created_at, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (key, content, now + ttl_seconds, now, entry_size),
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"ContextCacheStore: Failed to write cache by key ({e})")
                return False
            finally:
                conn.close()

    def set(self, content: str, ttl_seconds: int = 3600) -> bool:
        key = self._hash_key(content)
        now = time.time()
        entry_size = len(content.encode("utf-8"))
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM context_cache")
                total_size = cursor.fetchone()[0]
                while total_size + entry_size > self.MAX_TOTAL_SIZE_BYTES:
                    cursor.execute(
                        "SELECT key, size_bytes FROM context_cache ORDER BY created_at ASC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    if not row:
                        break
                    cursor.execute("DELETE FROM context_cache WHERE key = ?", (row[0],))
                    total_size -= row[1]
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO context_cache (key, content, expires_at, created_at, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (key, content, now + ttl_seconds, now, entry_size),
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"ContextCacheStore: Failed to write cache ({e})")
                return False
            finally:
                conn.close()

    def _delete_key(self, key: str) -> None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("DELETE FROM context_cache WHERE key = ?", (key,))
                conn.commit()
            finally:
                conn.close()

    def purge_expired(self) -> int:
        now = time.time()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM context_cache WHERE expires_at < ?", (now,))
                purged = cursor.rowcount
                conn.commit()
            finally:
                conn.close()
        return purged

    def count_active(self) -> int:
        now = time.time()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM context_cache WHERE expires_at > ?", (now,))
                return cursor.fetchone()[0]
            finally:
                conn.close()


class AnchorContextBuilder:
    """
    Builds atomic context anchors by aggregating fragmented metadata.
    Managed Agents Pattern: Supports pinning via XML tags.
    """

    def __init__(self, project_root: str | None = None) -> None:
        self.project_root = project_root or str(get_project_root())
        self.fragments = []

    def add_fragment(
        self, fragment_id: str, content: str, axis: int = 12, precedence: int = 100
    ) -> None:
        """Adds an atomic anchor fragment."""
        self.fragments.append(
            {
                "id": fragment_id,
                "content": content,
                "axis": axis,
                "precedence": precedence,
                "timestamp": time.time(),
            }
        )

    def build_anchors_xml(self) -> str:
        """Generates XML-formatted anchors for prompt injection."""
        if not self.fragments:
            return ""

        # Sort by precedence (highest first)
        sorted_frags = sorted(self.fragments, key=lambda x: x["precedence"], reverse=True)

        xml_blocks = [
            f'<anchor id="{frag["id"]}" axis="{frag["axis"]}">\n{frag["content"]}\n</anchor>'
            for frag in sorted_frags
        ]

        return "\n".join(xml_blocks)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("=== Architrave Context Cache: Firmitas Test ===")
        cache = ContextCacheStore()
        cache.set("test_anchor_content_v1", ttl_seconds=3600)
        cached = cache.get("test_anchor_content_v1")
        logger.info(f"Cache hit: {'yes' if cached else 'no'}")
        purged = cache.purge_expired()
        logger.info(f"Expired entries purged: {purged}")

        builder = AnchorContextBuilder()
        builder.add_fragment("test_cache", "Integration test fragment", axis=12, precedence=100)
        xml = builder.build_anchors_xml()
        logger.info(f"Anchor built with {len(builder.fragments)} fragments")
    else:
        logger.info("Usage: python context_cache.py --test")
