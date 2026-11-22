import os
from pathlib import Path

DATA_DIR_ENV = "PHANTOM_DATA_DIR"


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


def get_data_dir() -> Path:
    """Returns the runtime data directory.

    Defaults to <project_root>/data. Set PHANTOM_DATA_DIR to relocate every
    database, LanceDB table and hypergraph store; the test suite uses this to
    keep the real data/ directory untouched.
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override)
    return get_project_root() / "data"


def to_absolute_path(relative_path: str) -> str:
    """Converts a project-relative path to an absolute path.

    Paths under "data/" resolve inside get_data_dir(); every other path keeps
    resolving against the project root.
    """
    candidate = Path(relative_path)
    if candidate.parts and candidate.parts[0] == "data":
        return str(get_data_dir() / Path(*candidate.parts[1:]))
    return str(get_project_root() / relative_path)


if __name__ == "__main__":
    import sys

    sys.stdout.write(f"Project Root Detected: {get_project_root()}\n")
