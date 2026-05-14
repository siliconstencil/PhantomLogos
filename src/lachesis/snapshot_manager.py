import hashlib
import os
import sqlite3
import time

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


class SnapshotManager:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self._db_path = os.path.join(self.project_root, "data/snapshots.db")
        self._token_path = os.path.join(self.project_root, "data/snapshots/L0_AUTH_TOKEN")
        self._init_db()

    def _init_db(self):
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

    def take_snapshot(self, rel_path: str):
        """Kritik: Bu metod artik L0 kontrolu yapmaz. Sorumluluk Guardian'dadir."""
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
        except Exception:
            pass

    def scan_all(self):
        """Sadece baslangic baseline taramasi icin kullanilir."""
        for root_dir in WATCH_DIRS:
            full_root = os.path.join(self.project_root, root_dir)
            if not os.path.isdir(full_root):
                continue

            # Root dizin taranirken alt dizinleri manuel filtrelememiz gerekebilir
            # os.walk zaten bunu dirs[:] ile yapacak
            for root, dirs, files in os.walk(full_root):
                # Filter IGNORE_DIRS
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

                for file in files:
                    if file.endswith(WATCH_PATTERNS):
                        full_file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_file_path, self.project_root)
                        rel_path = rel_path.replace("\\", "/")
                        self.take_snapshot(rel_path)

    def restore_file(self, rel_path: str) -> bool:
        """Restores the latest safe snapshot. rel_path must be lowercase."""
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
