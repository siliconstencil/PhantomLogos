import pytest
import os
from src.muscle.local_runtime import LocalRuntime
from src.utils.project_path import get_project_root

def test_local_runtime_unsafe_path():
    """Ensure LocalRuntime raises ValueError when initialized with unsafe paths (B1)."""
    # 1. Test completely unsafe path on C:\
    with pytest.raises(ValueError) as excinfo:
        LocalRuntime(binary_dir="C:\\untrusted\\bin")
    assert "Unsafe path detected" in str(excinfo.value)

    # 2. Test relative path resolving to outside of D:\ (e.g., trying to escape root)
    # We can use os.path.abspath to ensure it resolves to C: if we pass it, but on windows,
    # let's test a non-D:\ drive
    with pytest.raises(ValueError) as excinfo2:
        LocalRuntime(binary_dir="E:\\temp\\llama")
    assert "Unsafe path detected" in str(excinfo2.value)

def test_local_runtime_safe_path():
    """Ensure LocalRuntime allows safe paths starting with D:\\ or project root."""
    root = get_project_root()
    safe_bin_dir = os.path.join(str(root), "bin", "llama_bin")
    
    # This should initialize fine without raising ValueError (even if the directory doesn't physically exist,
    # __init__ only logs warning for existence, but does not crash. It raises error only on unsafe path)
    runtime = LocalRuntime(binary_dir=safe_bin_dir)
    assert runtime.binary_dir == safe_bin_dir
