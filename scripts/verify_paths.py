import sys
from pathlib import Path

# Add project root to path [SRC:axis_10]
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.muscle.local_runtime import LocalRuntime
from src.utils.project_path import get_project_root


def test_paths():
    print("=== Testing Path Hardening ===")
    root = get_project_root()
    print(f"Detected Project Root: {root}")

    expected_root = "D:\\Hank"
    if str(root).lower() != expected_root.lower():
        print(f"FAILED: Root mismatch. Expected {expected_root}, got {root}")
        return False

    print("SUCCESS: Root helper verified.")

    # Test LocalRuntime path resolution
    runtime = LocalRuntime()
    print(f"LocalRuntime Binary Dir: {runtime.binary_dir}")
    if expected_root.lower() not in runtime.binary_dir.lower():
        print("FAILED: LocalRuntime binary_dir not anchored to root.")
        return False

    print("SUCCESS: LocalRuntime paths are anchored.")
    return True


if __name__ == "__main__":
    success = test_paths()
    sys.exit(0 if success else 1)
