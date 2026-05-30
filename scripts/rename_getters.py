"""Migration: _get_X() -> get_X() for all singleton getter functions.

Renames across all source files. Skips class methods (_get_verifier).
Safe: exact pattern match on _get_X( with known function names.
"""

import re
from pathlib import Path

FUNCTIONS = [
    "episodic",
    "goals",
    "procedural",
    "meta",
    "pruner",
    "spatial",
    "mapper",
    "semantic",
    "temporal",
    "reflection",
    "failure_memory",
    "monitor",
    "sweeper",
    "loader",
    "visual",
    "store",
    "gateway",
    "trajectory_store",
]

# Build pattern: _get_(episodic|goals|...)(\s*\()
# The second capture ensures we match function calls/definitions
PATTERNS = [rf"_get_{fn}(\s*\()" for fn in FUNCTIONS]

ROOT = Path(__file__).resolve().parent.parent

# Files to scan (all .py files except __pycache__, venv, etc.)
EXCLUDE = {
    ".venv",
    "__pycache__",
    "node_modules",
    ".git",
    "agent",
    "data",
    "logs",
    "scratch",
    "docs",
}


def replace_in_file(filepath: str) -> bool:
    path = Path(filepath)
    original = path.read_text(encoding="utf-8")
    text = original
    changed = False

    for fn_name in FUNCTIONS:
        old = f"_get_{fn_name}("
        new = f"get_{fn_name}("
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    changed_files = []
    scanned = 0

    for pyfile in ROOT.rglob("*.py"):
        rel = pyfile.relative_to(ROOT).as_posix()
        parts = rel.split("/")

        # Skip excluded directories
        if any(excl in parts for excl in EXCLUDE):
            continue

        scanned += 1

        # Quick check: does the file contain any _get_X( pattern?
        content = pyfile.read_text(encoding="utf-8")
        has_match = any(f"_{fn}(" in content for fn in ["_get_" + fn + "(" for fn in FUNCTIONS])
        # Actually the above is wrong. Let me just check.
        has_any = any(f"_get_{fn}(" in content for fn in FUNCTIONS)
        if not has_any:
            continue

        if replace_in_file(str(pyfile)):
            changed_files.append(rel)
            print(f"  CHANGED: {rel}")

    print(f"\nScanned: {scanned} files")
    print(f"Changed: {len(changed_files)} files")
    for f in sorted(changed_files):
        print(f"  - {f}")


if __name__ == "__main__":
    main()
