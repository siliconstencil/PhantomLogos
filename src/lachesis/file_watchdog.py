import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime

from src.utils.logging_config import setup_logger

from .snapshot_manager import (
    IGNORE_DIRS,
    WATCH_DIRS,
    WATCH_PATTERNS,
    WHITELIST_FILES,
    SnapshotManager,
)

logger = setup_logger(__name__)


class PollingGuardian:
    """
    Sovereign Shield: Cryptographic File Integrity Watchdog (SHA-256).
    [SRC:axis_11] Enforces absolute L0 authorization for all system mutations. [HH:MM AM/PM PT]
    """

    def __init__(self, project_root: str | None = None) -> None:
        from src.utils.project_path import get_project_root

        self.project_root = (
            str(get_project_root()) if project_root is None else os.path.abspath(project_root)
        )
        self.manager = SnapshotManager(self.project_root)
        self._last_mtimes = {}  # Cache for mtime optimization
        self._db_path = self.manager._db_path
        self._token_path = self.manager._token_path

    def _is_l0_authorized(self) -> bool:
        if os.path.exists(self._token_path):
            st = os.stat(self._token_path)
            # 60s authorization window
            if time.time() - st.st_mtime < 60:
                return True
        return False

    def _update_system_status(self, status: str, details: dict | None = None) -> None:
        """Atomic update of the system status flag for agent awareness."""
        status_path = os.path.join(self.project_root, "data/system_status.json")
        os.makedirs(os.path.dirname(status_path), exist_ok=True)
        ts = datetime.now().strftime("%I:%M %p PT")
        data = {"status": status, "time": ts}
        if details:
            data.update(details)

        temp_path = f"{status_path}.tmp"
        for attempt in range(3):
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                os.replace(temp_path, status_path)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.1)
                    continue
                logger.error(f"Guardian: Status update failed ({e})")

    def _log_violation(self, rel_path: str, reason: str) -> None:
        """Log sovereign violations to both file and Mnemosyne axes."""
        log_path = os.path.join(self.project_root, "logs/system/watchdog/integrity_violations.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] VIOLATION: {rel_path} | {reason} | Rollback executed.\n")

        try:
            from src.utils.logging_config import log_system_event

            log_system_event(
                "ERROR", f"SOVEREIGN VIOLATION: {rel_path} | {reason} | ROLLBACK executed."
            )

            from cognition.mnemosyne.episodic_store import EpisodicStore
            from cognition.mnemosyne.temporal_store import TemporalStore

            es = EpisodicStore()
            es.log(
                session_id="system",
                agent_id="SovereignShield",
                action="rollback",
                detail=f"File: {rel_path} | {reason}",
                outcome="restored",
            )
            ts_store = TemporalStore()
            ts_store.record(
                session_id="system",
                event_type="sovereign_block",
                model_name="Guardian",
                vram_gb=0,
                extra={"rel_path": rel_path, "reason": reason, "rollback": True},
            )
            try:
                from src.utils.service_locator import get_meta_store

                get_meta_store().adjust_reliability("sophia", -0.15, "watchdog_rollback")
            except Exception as exc:
                logger.warning("MetaCognitionStore reliability update failed: %s", exc)
        except Exception as e:
            logger.error(f"Sovereign Shield: Mnemosyne sync failed ({e})")

    def get_file_hash(self, full_path: str) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(full_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def _check_file(self, rel_path: str) -> bool:
        full_path = os.path.join(self.project_root, rel_path)
        path_key = rel_path.lower().replace("\\", "/")

        if not os.path.exists(full_path):
            if rel_path in WHITELIST_FILES:
                return False
            if not self._is_l0_authorized() and self.manager.restore_file(rel_path):
                self._log_violation(rel_path, "Unauthorized deletion")
                return True
            return False

        try:
            st = os.stat(full_path)
            new_mtime = st.st_mtime
            if rel_path in self._last_mtimes and self._last_mtimes[rel_path] == new_mtime:
                return False

            self._last_mtimes[rel_path] = new_mtime
            current_hash = self.get_file_hash(full_path)
            if not current_hash:
                return False

            with sqlite3.connect(self._db_path, timeout=30) as conn:
                row = conn.execute(
                    "SELECT hash FROM snapshots WHERE path = ? ORDER BY timestamp DESC LIMIT 1",
                    (path_key,),
                ).fetchone()

                if row and current_hash != row[0] and not self._is_l0_authorized():
                    if rel_path in WHITELIST_FILES:
                        self.manager.take_snapshot(rel_path)
                        return False
                    logger.error(f"[SOVEREIGN VIOLATION] {rel_path}: Mutation detected. ROLLBACK!")
                    self.manager.restore_file(rel_path)
                    self._log_violation(rel_path, "Unauthorized mutation (Hash mismatch)")
                    return True

                self.manager.take_snapshot(rel_path)
                return False
        except Exception as e:
            logger.error(f"Guardian check error [{rel_path}]: {e}")
            return False

    def run(self) -> None:
        logger.info(f"Polling Integrity Guardian (SHA-256) active on: {self.project_root}")
        cycle_count = 0
        while True:
            had_violation = False
            try:
                cycle_count += 1
                for root_dir in WATCH_DIRS:
                    full_root = os.path.join(self.project_root, root_dir)
                    if not os.path.isdir(full_root):
                        continue
                    for root, dirs, files in os.walk(full_root):
                        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                        for file in files:
                            if file.endswith(WATCH_PATTERNS):
                                full_file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(
                                    full_file_path, self.project_root
                                ).replace("\\", "/")
                                if self._check_file(rel_path):
                                    had_violation = True
            except Exception as e:
                logger.error(f"Guardian cycle error: {e}")

            self._update_system_status("ERROR" if had_violation else "OK")
            time.sleep(10)


if __name__ == "__main__":
    from src.utils.project_path import get_project_root

    guardian = PollingGuardian(str(get_project_root()))
    guardian.run()
