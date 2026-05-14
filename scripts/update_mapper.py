import sys
from pathlib import Path

# Ensure src/cognition are in path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.hephaestus import _get_mapper, _get_spatial


def update_mapper():
    print("[MAPPER] Initializing CodebaseMapper (Axis 5)...")
    store = _get_spatial()
    mapper = _get_mapper()

    print("[MAPPER] Starting deep scan of codebase...")
    success = mapper.map_codebase(deep=True)

    if success:
        count = store.get_module_count()
        print(f"[MAPPER] SUCCESS: Indexed {count} modules in spatial.db.")

        # Detect circular dependencies as a bonus check
        print("[MAPPER] Checking for circular dependencies...")
        circles = mapper.detect_circular()
        if circles:
            print(f"[ALERT] Found {len(circles)} circular dependency chains!")
            for c in circles[:3]:
                print(f"  -> {' -> '.join(c)}")
        else:
            print("[MAPPER] No circular dependencies detected. Clean architecture.")
    else:
        print("[ERROR] Mapper failed to initialize or scan.")


if __name__ == "__main__":
    update_mapper()
