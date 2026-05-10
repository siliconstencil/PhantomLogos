import os
import sqlite3
import hashlib
import time
import threading
from datetime import datetime

DB_PATH = "data/snapshots.db"
WATCH_DIRS = ["src", "cognition", ".antigravity", "agent"]
IGNORE_DIRS = {".venv", "__pycache__", "data", "logs", "scratch", ".git", "opencode"}
WATCH_PATTERNS = (".py", ".md", ".yaml", ".yml", ".json")
L0_TOKEN_PATH = "data/snapshots/L0_AUTH_TOKEN"

class SnapshotManager:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path_ts ON snapshots (path, timestamp DESC)")

    def _get_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def take_snapshot(self, rel_path: str):
        full_path = os.path.join(self.project_root, rel_path)
        if not os.path.exists(full_path):
            return

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            
            h = self._get_hash(content)
            size = len(content)
            ts = time.time()

            # Sadece içerik değiştiyse yeni snapshot al
            with sqlite3.connect(DB_PATH) as conn:
                last_hash = conn.execute(
                    "SELECT hash FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1", 
                    (rel_path,)
                ).fetchone()
                
                if not last_hash or last_hash[0] != h:
                    # Sadece L0 onaylıyken veya ilk kez snapshot alınırken izin ver
                    # (Veya çok küçük dosyaları kaydetme)
                    if os.path.exists(L0_TOKEN_PATH) or not last_hash:
                        conn.execute(
                            "INSERT INTO snapshots (path, hash, content, size, timestamp) VALUES (?, ?, ?, ?, ?)",
                            (rel_path, h, content, size, ts)
                        )
        except Exception:
            pass

    def scan_all(self):
        for root_dir in WATCH_DIRS:
            full_root = os.path.join(self.project_root, root_dir)
            if not os.path.isdir(full_root):
                continue
            
            for root, dirs, files in os.walk(full_root):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    if file.endswith(WATCH_PATTERNS):
                        rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                        rel_path = rel_path.replace("\\", "/").lower()  # Standartlaştırma
                        self.take_snapshot(rel_path)

    def restore_file(self, rel_path: str) -> bool:
        """En son güvenli snapshot'ı geri yükler."""
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT content FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1",
                (rel_path,)
            ).fetchone()
            
            if row:
                full_path = os.path.join(self.project_root, rel_path)
                with open(full_path, "wb") as f:
                    f.write(row[0])
                return True
        return False

def run_guardian(project_root: str):
    manager = SnapshotManager(project_root)
    while True:
        manager.scan_all()
        time.sleep(30)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getcwd())
    args = parser.parse_args()
    run_guardian(args.root)
