import os
import shutil
from datetime import datetime

from src.utils.project_path import get_project_root


def backup():
    root = get_project_root()
    backup_dir = root / "data" / "backups" / "config"
    backup_dir.mkdir(parents=True, exist_ok=True)

    critical_files = [".env", "data/ankyra_anchor.md", ".antigravity/rules.json", "pyproject.toml"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"=== Phase 9.1: Critical Config Backup [{timestamp}] ===")

    for rel_path in critical_files:
        src = root / rel_path
        if src.exists():
            dst = backup_dir / f"{os.path.basename(rel_path)}.{timestamp}.bak"
            shutil.copy2(src, dst)
            print(f"Backed up: {rel_path} -> {dst.name}")
        else:
            print(f"Skipping (not found): {rel_path}")


if __name__ == "__main__":
    backup()
