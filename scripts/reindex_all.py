import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.hephaestus import get_mapper, get_spatial


def reindex():
    print("=== Phase 10.4: Full Codebase Re-indexing ===")

    mapper = get_mapper()
    spatial = get_spatial()

    print(f"Project Path: {mapper.project_path}")
    print("Starting deep mapping (including scripts, tests, agent)...")

    success = mapper.map_codebase(deep=True)

    if success:
        count = spatial.get_module_count()
        print(f"SUCCESS: Codebase re-indexed. Total modules in Spatial DB: {count}")
    else:
        print("FAILURE: Mapping failed.")


if __name__ == "__main__":
    reindex()
