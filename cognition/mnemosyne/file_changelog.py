import os
import time
import sqlite3
import hashlib
import threading
from typing import List, Dict, Any, Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class FileChangelogStore:
    """
    Append-only file change audit log.
    Independent of any agent — tracks every byte change on monitored files.
    """
    AXIS_ID = 7

    def __init__(self, db_path: Optional[str] = None, project_root: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "data", "file_changelog.db")
        self.db_path = db_path
        self.project_root = project_root or os.getcwd()
        self._lock = threading.Lock()
        self._ensure_table()

    def _resolve_path(self, file_path: str) -> str:
        if os.path.isabs(file_path):
            return file_path
        return os.path.join(self.project_root, file_path)

    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_changelog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    file_path TEXT NOT NULL,
                    pre_hash TEXT,
                    pre_size INTEGER,
                    post_hash TEXT,
                    post_size INTEGER,
                    delta_bytes INTEGER,
                    event_type TEXT DEFAULT 'modified'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_changelog_path
                ON file_changelog(file_path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_changelog_time
                ON file_changelog(timestamp)
            """)
            conn.commit()
        finally:
            conn.close()

    def _hash_file(self, file_path: str) -> str:
        try:
            with open(self._resolve_path(file_path), "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _file_size(self, file_path: str) -> int:
        try:
            return os.path.getsize(self._resolve_path(file_path))
        except Exception:
            return 0

    def record_change(self, file_path: str, event_type: str = "modified"):
        with self._lock:
            post_hash = self._hash_file(file_path)
            post_size = self._file_size(file_path)

            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT post_hash, post_size FROM file_changelog WHERE file_path = ? ORDER BY id DESC LIMIT 1",
                    (file_path,)
                )
                row = cursor.fetchone()
                pre_hash = row[0] if row else ""
                pre_size = row[1] if row else 0
            finally:
                conn.close()

            delta = post_size - pre_size if pre_size > 0 else 0

            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    "INSERT INTO file_changelog (timestamp, file_path, pre_hash, pre_size, post_hash, post_size, delta_bytes, event_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (time.time(), file_path, pre_hash, pre_size, post_hash, post_size, delta, event_type)
                )
                conn.commit()
            finally:
                conn.close()

            if pre_size > 0 and delta < 0 and abs(delta) > pre_size * 0.5:
                logger.warning(
                    f"FILE INTEGRITY ALERT: {file_path} shrunk {abs(delta)} bytes "
                    f"({abs(delta)/pre_size*100:.0f}% reduction) "
                    f"via {event_type}"
                )
            elif delta != 0:
                logger.info(
                    f"File change: {file_path} {pre_size} -> {post_size} bytes "
                    f"(delta: {delta:+d})"
                )

    def latest(self, file_path: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, file_path, pre_hash, pre_size, post_hash, post_size, delta_bytes, event_type FROM file_changelog WHERE file_path = ? ORDER BY id DESC LIMIT 1",
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "timestamp": row[0], "file_path": row[1],
                    "pre_hash": row[2], "pre_size": row[3],
                    "post_hash": row[4], "post_size": row[5],
                    "delta_bytes": row[6], "event_type": row[7],
                }
        finally:
            conn.close()
        return None

    def history(self, file_path: str, limit: int = 20) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, pre_size, post_size, delta_bytes, event_type FROM file_changelog WHERE file_path = ? ORDER BY id DESC LIMIT ?",
                (file_path, limit)
            )
            return [
                {"timestamp": r[0], "pre_size": r[1], "post_size": r[2],
                 "delta": r[3], "event": r[4]} for r in cursor.fetchall()
            ]
        finally:
            conn.close()

    def integrity_report(self, min_delta_pct: float = 30.0) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, pre_size, post_size, delta_bytes, timestamp
                FROM file_changelog
                WHERE pre_size > 0 AND delta_bytes < 0
                AND CAST(ABS(delta_bytes) AS REAL) / pre_size >= ?
                ORDER BY timestamp DESC LIMIT 50
            """, (min_delta_pct / 100.0,))
            return [
                {"file": r[0], "before": r[1], "after": r[2],
                 "delta": r[3], "time": r[4]} for r in cursor.fetchall()
            ]
        finally:
            conn.close()
