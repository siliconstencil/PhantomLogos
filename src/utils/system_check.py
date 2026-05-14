"""
Runtime environment validation for Phantom Logos.
Phase 1.0.18: Establishing Professional Diagnostics.
"""

import logging
import os
import shutil
import time
import urllib.request
from typing import NamedTuple

from src.utils.config import load_config

logger = logging.getLogger(__name__)


class SystemCheckResult(NamedTuple):
    """Container for diagnostic results."""

    warnings: list[str]
    passed: bool


class SystemCheck:
    """
    Validates runtime infrastructure readiness.
    All checks are warning-only and never block the startup process.
    """

    MIN_DISK_FREE_MB = 500
    OLLAMA_RETRY = 3
    OLLAMA_DELAY = 5
    OLLAMA_TIMEOUT = 2

    def __init__(self, project_root: str):
        self._root = project_root
        self._warnings: list[str] = []

    def run(self) -> SystemCheckResult:
        """
        Runs all diagnostic checks sequentially.
        Captures any unexpected exceptions within each check to prevent system crash.
        """
        checks = [
            ("data_dir", self._check_data_dir),
            ("disk_space", self._check_disk_space),
            ("ollama", self._check_ollama),
            ("env_names", self._check_env_names),
        ]

        for name, method in checks:
            try:
                method()
            except Exception as e:
                self._warnings.append(f"{name} check failed unexpectedly: {type(e).__name__}: {e}")

        return SystemCheckResult(warnings=self._warnings, passed=len(self._warnings) == 0)

    # --- Individual Check Methods ---

    def _check_data_dir(self) -> None:
        """Verifies that the data/ directory exists and is writable."""
        path = os.path.join(self._root, "data")
        os.makedirs(path, exist_ok=True)

        test_file = os.path.join(path, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
        except OSError as e:
            self._warnings.append(f"data/ directory is not writable: {e}")

    def _check_disk_space(self) -> None:
        """Verifies that there is sufficient disk space for operations."""
        try:
            usage = shutil.disk_usage(self._root)
            free_mb = usage.free // (1024 * 1024)
            if free_mb < self.MIN_DISK_FREE_MB:
                self._warnings.append(
                    f"Low disk space: {free_mb}MB free (Threshold: {self.MIN_DISK_FREE_MB}MB)"
                )
        except Exception as e:
            self._warnings.append(f"Disk space check failed: {e}")

    def _check_ollama(self) -> None:
        """
        Checks if Ollama API is reachable.
        Retries up to OLLAMA_RETRY times to handle late daemon startup.
        """
        cfg = load_config()
        host = cfg.ollama_host

        for attempt in range(1, self.OLLAMA_RETRY + 1):
            try:
                # Heartbeat check via /api/tags
                urllib.request.urlopen(
                    urllib.request.Request(f"{host}/api/tags"),
                    timeout=self.OLLAMA_TIMEOUT,
                )
                return  # Success
            except Exception:
                if attempt < self.OLLAMA_RETRY:
                    logger.info(
                        f"Ollama not ready at {host} ({attempt}/{self.OLLAMA_RETRY}), retrying in {self.OLLAMA_DELAY}s..."
                    )
                    time.sleep(self.OLLAMA_DELAY)

        self._warnings.append(f"Ollama unreachable at {host} after {self.OLLAMA_RETRY} attempts.")

    def _check_env_names(self) -> None:
        """Detects legacy or mismatched environment variable names (Findings E1, E2, E7)."""
        mismatches = {
            "RAG_CHUNK_SIZE": "MAPPER_CHUNK_SIZE",
            "RAG_CHUNK_OVERLAP": "MAPPER_CHUNK_OVERLAP",
            "OLLAMA_BASE_URL": "OLLAMA_HOST (Prefer host for SSOT)",
        }

        # E1: Name Mismatch Check
        for legacy, current in mismatches.items():
            if os.getenv(legacy) and not os.getenv(current.split()[0]):
                self._warnings.append(
                    f"Legacy env var detected: '{legacy}' is set but code expects '{current}'."
                )

        # E7: Dead Variables Check
        dead_vars = ["GEMINI_API_KEY", "DEEPSEEK_API_KEY"]
        for var in dead_vars:
            if os.getenv(var):
                self._warnings.append(
                    f"Dead env var detected: '{var}' is set in .env but is no longer used by the system."
                )
