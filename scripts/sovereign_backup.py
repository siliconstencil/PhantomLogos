import shutil
import sys
from datetime import datetime
from pathlib import Path


def backup(rel_path):
    root = Path(__file__).resolve().parent.parent
    src = root / rel_path
    if not src.exists():
        print(f"Error: {rel_path} not found.")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / ".antigravity" / "backup" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)

    dst = backup_dir / src.name
    shutil.copy2(src, dst)
    print(f"Success: Backup of {rel_path} created at {dst}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/sovereign_backup.py <rel_path>")
    else:
        backup(sys.argv[1])
