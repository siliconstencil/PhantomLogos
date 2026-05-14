import os
import sys

# Ensure src and cognition are in path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from cognition.morpheus.loader import ModelLoader


def main():
    print("[MORPHEUS] Triggering VRAM Flush (Sequential Loading Protocol)...")
    loader = ModelLoader()
    loader.flush()
    print("[SUCCESS] VRAM Cleared. Ready for heavy model transition.")


if __name__ == "__main__":
    main()
