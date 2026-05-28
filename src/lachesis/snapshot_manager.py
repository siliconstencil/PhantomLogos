import hashlib
import logging
import os
import sqlite3
import time

logger = logging.getLogger(__name__)

WATCH_DIRS = [".", "src", "cognition", ".antigravity", "agent"]
IGNORE_DIRS = {
    ".venv",
    "__pycache__",
    "data",
    "logs",
    "scratch",
    ".git",
    "opencode",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}
WATCH_PATTERNS = (
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
    ".toml",
    ".cfg",
    ".sql",
    ".env",
    ".bat",
)

WHITELIST_FILES = {"agent/a2a_registry.json"}


class SnapshotManager:
    def __init__(self, project_root: str) -> None:
        self.project_root = os.path.abspath(project_root)
        self._db_path = os.path.join(self.project_root, "data/snapshots.db")
        self._token_path = os.path.join(self.project_root, "data/snapshots/L0_AUTH_TOKEN")
        self._init_db()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    path TEXT,
                    hash TEXT,
                    content BLOB,
                    size INTEGER,
                    timestamp REAL,
                    PRIMARY KEY (path, timestamp)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_path_ts ON snapshots (path, timestamp DESC)"
            )

    def _get_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def take_snapshot(self, rel_path: str) -> None:
        full_path = os.path.join(self.project_root, rel_path)
        if not os.path.exists(full_path):
            return
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            h = self._get_hash(content)
            size = len(content)
            ts = time.time()
            path_key = rel_path.lower().replace("\\", "/")
            with sqlite3.connect(self._db_path) as conn:
                last_hash = conn.execute(
                    "SELECT hash FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1",
                    (path_key,),
                ).fetchone()
                if not last_hash or last_hash[0] != h:
                    conn.execute(
                        "INSERT INTO snapshots (path, hash, content, size, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (path_key, h, content, size, ts),
                    )
        except Exception as e:
            logger.debug(f"SnapshotManager: file scan entry skipped ({e})")

    def scan_all(self) -> None:
        for root_dir in WATCH_DIRS:
            full_root = os.path.join(self.project_root, root_dir)
            if not os.path.isdir(full_root):
                continue
            for root, dirs, files in os.walk(full_root):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    if file.endswith(WATCH_PATTERNS):
                        full_file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_file_path, self.project_root)
                        rel_path = rel_path.replace("\\", "/")
                        self.take_snapshot(rel_path)

    def restore_file(self, rel_path: str) -> bool:
        path_key = rel_path.lower().replace("\\", "/")
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT content FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1",
                (path_key,),
            ).fetchone()
            if row:
                full_path = os.path.join(self.project_root, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(row[0])
                return True
        return False

    def purge_old(self, keep_per_path: int = 3) -> None:
        removed = 0
        with sqlite3.connect(self._db_path) as conn:
            paths = conn.execute("SELECT DISTINCT path FROM snapshots").fetchall()
            for (path_key,) in paths:
                rows = conn.execute(
                    "SELECT timestamp FROM snapshots WHERE path = ? ORDER BY timestamp DESC",
                    (path_key,),
                ).fetchall()
                if len(rows) > keep_per_path:
                    old_ts = rows[keep_per_path - 1][0]
                    deleted = conn.execute(
                        "DELETE FROM snapshots WHERE path = ? AND timestamp < ?",
                        (path_key, old_ts),
                    ).rowcount
                    removed += deleted
        if removed:
            conn2 = sqlite3.connect(self._db_path)
            try:
                conn2.execute("VACUUM")
            finally:
                conn2.close()
            logger.info(
                "SnapshotManager: Purged %d old snapshots, keeping last %d per file.",
                removed,
                keep_per_path,
            )
