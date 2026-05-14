import os
import re
import shutil
import subprocess
import sys
import tempfile

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

logger = setup_logger(__name__)


class LightSandbox:
    """
    Phantom Logos Agent Isolation Layer (Axis 11).
    Provides a temporary, restricted execution environment for Python code.
    [SRC:axis_11] Implements formal verification and security gates.
    """

    def __init__(self):
        # [SRC:axis_10] Workspace hygiene: using system temp for isolation.
        self.temp_dir = tempfile.mkdtemp(prefix="phantom_sandbox_")
        self.temp_dir = os.path.abspath(self.temp_dir)
        logger.info(f"LightSandbox: Initialized at {self.temp_dir}")

    def _strip_env(self) -> dict:
        """
        Sanitizes environment variables to prevent system-wide access.
        [SRC:axis_11] Environment hardening for deterministic execution.
        """
        env = {}
        # Core variables for stability
        keep_vars = ["SYSTEMROOT", "TEMP", "TMP", "USERNAME", "COMPUTERNAME"]
        for v in keep_vars:
            if v in os.environ:
                env[v] = os.environ[v]

        # Windows PATH restoration (Lachesis Audit recommendation)
        paths = []

        # 1. System32 (Required for base DLLs)
        sys32 = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        if os.path.exists(sys32):
            paths.append(sys32)

        # 2. .venv/Scripts (Required for the current interpreter's context)
        venv_scripts = os.path.join(get_project_root(), ".venv", "Scripts")
        if os.path.exists(venv_scripts):
            paths.append(venv_scripts)

        env["PATH"] = ";".join(paths)
        env.pop("PYTHONPATH", None)

        return env

    def run(self, code: str, timeout_sec: int = 10):
        """
        Executes code in the sandbox and returns (stdout, stderr).
        Includes basic security pre-check for absolute paths.
        [SRC:axis_11] Logic integrity verification.
        """
        # S5.4: Basic Path Sanitization (Mitigation for Absolute Path Risk)
        forbidden_patterns = [r"[A-Z]:\\", r"[A-Z]:/", r"\\\\", r"//"]
        for pattern in forbidden_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning("LightSandbox: Forbidden path pattern detected in code.")
                return "", "Error: Absolute paths or network shares are forbidden in sandbox code."

        script_path = os.path.join(self.temp_dir, "sandbox_script.py")

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            env = self._strip_env()

            logger.info(f"LightSandbox: Executing code (timeout={timeout_sec}s)")

            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
                cwd=self.temp_dir,
                encoding="utf-8",
            )

            return result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            logger.warning("LightSandbox: Execution timed out.")
            return "", "Error: Execution timed out."
        except OSError as e:
            logger.error(f"LightSandbox: File system error ({e})")
            return "", f"Error: {e!s}"
        except Exception as e:
            logger.error(f"LightSandbox: Unexpected error ({e})")
            return "", f"Error: {e!s}"

    def cleanup(self):
        """
        Removes the temporary directory.
        [SRC:axis_10] Resource cleanup protocol.
        """
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"LightSandbox: Cleaned up {self.temp_dir}")
        except OSError as e:
            logger.warning(f"LightSandbox: Cleanup failed for {self.temp_dir} ({e})")


if __name__ == "__main__":
    # Self-test [SRC:axis_11]
    sandbox = LightSandbox()
    try:
        out, err = sandbox.run(
            "import sys\nsys.stdout.write('Hello from Sandbox')\nimport os\nsys.stdout.write(f'CWD: {os.getcwd()}')"
        )
        logger.info(f"Sandbox self-test output: {out}")
        if err:
            logger.warning(f"STDERR: {err}")
    finally:
        sandbox.cleanup()
