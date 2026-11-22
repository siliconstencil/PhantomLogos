"""
Generate mcp_config.json from mcp_config.template.json.
Replaces ${PHANTOM_ROOT} with the absolute path of this project and adapts the
virtualenv and launcher paths to the current platform.
Run once after cloning: python scripts/setup_mcp_config.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
template_path = ROOT / "mcp_config.template.json"
output_path = ROOT / "mcp_config.json"

if not template_path.exists():
    print(f"[ERROR] Template not found: {template_path}")
    sys.exit(1)

content = template_path.read_text(encoding="utf-8")

if os.name == "nt":  # Windows
    escaped_root = str(ROOT).replace("\\", "\\\\")
    content = content.replace("${PHANTOM_ROOT}", escaped_root)
    content = content.replace("/.venv/bin/python", "\\\\.venv\\\\Scripts\\\\python.exe")
    content = content.replace("run_github_mcp.sh", "run_github_mcp.bat")
else:  # Linux/macOS
    escaped_root = str(ROOT).replace("\\", "/")
    content = content.replace("${PHANTOM_ROOT}", escaped_root)
    content = content.replace("run_github_mcp.bat", "run_github_mcp.sh")

output_path.write_text(content, encoding="utf-8")
print(f"[OK] mcp_config.json generated dynamically: {output_path}")
