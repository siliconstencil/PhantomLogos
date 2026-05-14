import asyncio
import os
import shutil
from datetime import datetime
from typing import Any

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root
from src.utils.sandbox import LightSandbox

logger = setup_logger(__name__)

# Note: Layer 3 provides protection for INTERNAL tool calls.
# Direct writes via OpenCode (IDE) are protected by Layer 2 (Watchdog).


def _backup_file(rel_path: str, project_root: str):
    """Creates a timestamped backup in .antigravity/backup/."""
    try:
        full_path = os.path.join(project_root, rel_path)
        if not os.path.exists(full_path):
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(project_root, ".antigravity", "backup", ts)
        os.makedirs(backup_dir, exist_ok=True)

        dest_path = os.path.join(backup_dir, os.path.basename(rel_path))
        shutil.copy2(full_path, dest_path)
        logger.info(f"ToolBridge: Backup created for {rel_path} at {dest_path}")
    except Exception as e:
        logger.error(f"ToolBridge: Backup failed for {rel_path} ({e})")


async def _ls(bridge, input_data):
    input_path = input_data[0] if isinstance(input_data, list) else input_data
    base_dir = str(get_project_root())
    requested_path = os.path.abspath(input_path)
    if os.path.commonpath([base_dir, requested_path]) != base_dir:
        logger.warning(f"ToolBridge: Path traversal blocked for {input_path}")
        return f"Error: Access denied to {input_path}. Stay within project root."
    return await asyncio.to_thread(os.listdir, requested_path)


async def _write_file(bridge, input_data: dict[str, Any]):
    """
    Atomic write with pre-write backup.
    Input: {"path": "...", "content": "..."}
    """
    try:
        rel_path = input_data.get("path")
        content = input_data.get("content", "")
        if not rel_path:
            return "Error: Missing path"

        project_root = str(get_project_root())
        full_path = os.path.join(project_root, rel_path)

        # 1. Pre-write backup
        _backup_file(rel_path, project_root)

        # 2. Atomic Write (temp + rename)
        temp_path = full_path + ".tmp"

        def write_sync():
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            if os.path.exists(full_path):
                os.remove(full_path)
            os.rename(temp_path, full_path)

        await asyncio.to_thread(write_sync)

        # 3. Audit (Manual trigger of changelog if needed, but Guardian will pick it up)
        logger.info(f"ToolBridge: Successfully wrote {rel_path} (atomic)")
        return f"Success: Wrote to {rel_path}"
    except Exception as e:
        logger.error(f"ToolBridge: write_file failed ({e})")
        return f"Error: {e!s}"


async def _replace_content(bridge, input_data: dict[str, Any]):
    """
    Replaces TargetContent with ReplacementContent with pre-write backup.
    Input: {"path": "...", "target": "...", "replacement": "..."}
    """
    try:
        rel_path = input_data.get("path")
        target = input_data.get("target")
        replacement = input_data.get("replacement")
        if not rel_path or target is None or replacement is None:
            return "Error: Missing parameters"

        project_root = str(get_project_root())
        full_path = os.path.join(project_root, rel_path)

        def replace_sync():
            if not os.path.exists(full_path):
                return f"Error: File {rel_path} not found"

            with open(full_path, encoding="utf-8") as f:
                data = f.read()

            if target not in data:
                return f"Error: Target content not found in {rel_path}"

            _backup_file(rel_path, project_root)
            new_data = data.replace(target, replacement)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_data)
            return "Success"

        result = await asyncio.to_thread(replace_sync)
        return result
    except Exception as e:
        logger.error(f"ToolBridge: replace_content failed ({e})")
        return f"Error: {e!s}"


async def _run_code(bridge, input_data):
    try:
        code = input_data.get("code") if isinstance(input_data, dict) else str(input_data)
        timeout = input_data.get("timeout", 10) if isinstance(input_data, dict) else 10
        sandbox = LightSandbox()
        try:
            stdout, stderr = await asyncio.to_thread(sandbox.run, code, timeout)
            if stderr:
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "status": "warning" if stdout else "error",
                }
            return {"stdout": stdout, "status": "success"}
        finally:
            sandbox.cleanup()
    except Exception as e:
        logger.error(f"ToolBridge: run_code failed ({e})")
        return f"Code execution error: {e!s}"
