"""
Generate mcp_config.json from mcp_config.template.json.
Replaces ${PHANTOM_ROOT} with the absolute path of this project.
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
    # Ensure Windows path components and files are used
    content = content.replace("run_github_mcp.sh", "run_github_mcp.bat")
else:  # Linux/macOS
    escaped_root = str(ROOT).replace("\\", "/")
    content = content.replace("${PHANTOM_ROOT}", escaped_root)
    # Swap out Windows paths and files to unix paths
    content = content.replace(".venv\\\\Scripts\\\\slm.exe", ".venv/bin/slm")
    content = content.replace(".venv\\\\Scripts\\\\python.exe", ".venv/bin/python")
    content = content.replace("run_github_mcp.bat", "run_github_mcp.sh")
    content = content.replace("\\\\", "/")
    content = content.replace("\\", "/")

output_path.write_text(content, encoding="utf-8")
print(f"[OK] mcp_config.json generated dynamically: {output_path}")
