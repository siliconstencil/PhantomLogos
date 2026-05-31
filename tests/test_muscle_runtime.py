import os
import sys
from unittest.mock import patch

from src.muscle.local_runtime import LocalRuntime
from src.utils.project_path import get_project_root


def test_local_runtime_binary_logic():
    with patch.object(LocalRuntime, "_validate_path"):
        rt = LocalRuntime(binary_dir=os.path.join(str(get_project_root()), "bin"))
        binary = rt._get_binary("generic")
        ext = ".exe" if sys.platform == "win32" else ""
        assert binary.endswith(f"llama-cli{ext}")


def test_local_runtime_binary_mismatch():
    with patch.object(LocalRuntime, "_validate_path"):
        rt = LocalRuntime(binary_dir=os.path.join(str(get_project_root()), "bin"))
        binary = rt._get_binary("gemma4")
        ext = ".exe" if sys.platform == "win32" else ""
        assert "llama-mtmd-cli" in binary


if __name__ == "__main__":
    print("Running Muscle runtime tests...")
    test_local_runtime_binary_logic()
    test_local_runtime_binary_mismatch()
    print("Muscle runtime tests passed.")
