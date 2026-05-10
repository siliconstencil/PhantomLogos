import pytest
import sys
import os
from src.muscle.local_runtime import LocalRuntime

def test_local_runtime_binary_logic():
    rt = LocalRuntime(binary_dir="/tmp/bin")
    binary = rt._get_binary("generic")
    ext = ".exe" if sys.platform == "win32" else ""
    assert binary.endswith(f"llama-cli{ext}")

def test_local_runtime_binary_mismatch():
    rt = LocalRuntime(binary_dir="/tmp/bin")
    binary = rt._get_binary("gemma4")
    ext = ".exe" if sys.platform == "win32" else ""
    assert "llama-mtmd-cli" in binary

if __name__ == "__main__":
    print("Running Muscle runtime tests...")
    test_local_runtime_binary_logic()
    test_local_runtime_binary_mismatch()
    print("Muscle runtime tests passed.")
