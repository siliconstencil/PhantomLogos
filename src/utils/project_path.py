from pathlib import Path


def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Uses __file__ of this module as a stable anchor.
    This module is expected to be at src/utils/project_path.py.
    """
    # [SRC:axis_10] Stable path anchoring
    current_file = Path(__file__).resolve()
    # current_file is .../src/utils/project_path.py
    # parent is .../src/utils
    # parent.parent is .../src
    # parent.parent.parent is .../
    return current_file.parent.parent.parent


def to_absolute_path(relative_path: str) -> str:
    """Converts a project-relative path to an absolute path."""
    root = get_project_root()
    return str(root / relative_path)


if __name__ == "__main__":
    import sys

    sys.stdout.write(f"Project Root Detected: {get_project_root()}\n")
