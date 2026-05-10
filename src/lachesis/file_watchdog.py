import os
import sys
import time
import sqlite3
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import importlib.util
_sm_path = os.path.join(os.path.dirname(__file__), "snapshot_manager.py")
_sm_spec = importlib.util.spec_from_file_location("_snapshot_manager", _sm_path)
_sm_mod = importlib.util.module_from_spec(_sm_spec)
_sm_spec.loader.exec_module(_sm_mod)
SnapshotManager = _sm_mod.SnapshotManager
DB_PATH = _sm_mod.DB_PATH

WATCH_DIRS = ["src", "cognition", ".antigravity", "agent"]
WATCH_PATTERNS = (".py", ".md", ".yaml", ".yml", ".json")
IGNORE_DIRS = {".venv", "__pycache__", "data", "logs", "scratch", ".git", ".pytest_cache", "opencode"}

SIZE_THRESHOLD_PERCENT = 0.9
L0_TOKEN_PATH = os.path.join(BASE_DIR, "data/snapshots/L0_AUTH_TOKEN")

class PollingGuardian:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.manager = SnapshotManager(self.project_root)
        self._last_mtimes = {} # Cache for mtime optimization

    def _is_l0_authorized(self) -> bool:
        if os.path.exists(L0_TOKEN_PATH):
            st = os.stat(L0_TOKEN_PATH)
            if time.time() - st.st_mtime < 60:
                return True
        return False

    def _log_violation(self, rel_path: str, old_size: int, new_size: int):
        log_path = os.path.join(self.project_root, "logs/system/watchdog/integrity_violations.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] VIOLATION: {rel_path} | Size dropped from {old_size} to {new_size}. Rollback executed.\n")

    def _check_file(self, rel_path: str):
        full_path = os.path.join(self.project_root, rel_path)
        if not os.path.exists(full_path): return

        try:
            st = os.stat(full_path)
            new_mtime = st.st_mtime
            
            # Optimization: Skip if mtime hasn't changed since last check
            if rel_path in self._last_mtimes and self._last_mtimes[rel_path] == new_mtime:
                return
            
            self._last_mtimes[rel_path] = new_mtime
            new_size = st.st_size
            
            with sqlite3.connect(os.path.join(self.project_root, DB_PATH)) as conn:
                row = conn.execute(
                    "SELECT size FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1",
                    (rel_path.lower(),)
                ).fetchone()
                
                if row:
                    old_size = row[0]
                    if new_size < (old_size * SIZE_THRESHOLD_PERCENT):
                        if not self._is_l0_authorized():
                            print(f"[SOVEREIGN VIOLATION] {rel_path}: {old_size} -> {new_size}. ROLLBACK!", flush=True)
                            self.manager.restore_file(rel_path)
                            self._log_violation(rel_path, old_size, new_size)
                            # Reset mtime after restore to ensure next check sees the restored file
                            self._last_mtimes[rel_path] = os.path.getsize(full_path) 
        except Exception:
            pass

    def run(self):
        print(f"[INIT] Polling Integrity Guardian active on: {self.project_root}", flush=True)
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                if cycle_count % 100 == 0:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts}] [HEARTBEAT] Guardian cycle {cycle_count} completed. System secure.", flush=True)

                for root_dir in WATCH_DIRS:
                    full_root = os.path.join(self.project_root, root_dir)
                    if not os.path.isdir(full_root): continue
                    
                    for root, dirs, files in os.walk(full_root):
                        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                        for file in files:
                            if file.endswith(WATCH_PATTERNS):
                                rel_path = os.path.relpath(os.path.join(root, file), self.project_root).replace("\\", "/")
                                self._check_file(rel_path)
            except Exception as e:
                print(f"[ERROR] Cycle error: {e}", flush=True)
            
            time.sleep(30)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getcwd())
    args = parser.parse_args()
    guardian = PollingGuardian(args.root)
    guardian.run()
