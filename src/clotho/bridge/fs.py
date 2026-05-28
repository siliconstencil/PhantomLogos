import asyncio
import os
import pathlib
import shutil
import time
from datetime import datetime
from typing import Any

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root
from src.utils.sandbox import LightSandbox
from src.lachesis.snapshot_manager import SnapshotManager

logger = setup_logger(__name__)

_l0_cache: dict = {"ts": 0.0, "result": False}

_BASE = pathlib.Path(".").resolve()
PROTECTED_PATHS = {
    (_BASE / "data" / "snapshots" / "L0_AUTH_TOKEN").resolve(),
    (_BASE / "data" / "snapshots").resolve(),
}


def _is_protected(target: str) -> bool:
    try:
        resolved = pathlib.Path(target).resolve()
    except Exception:
        return True
    return resolved in PROTECTED_PATHS or any(resolved.is_relative_to(p) for p in PROTECTED_PATHS)


def _is_l0_authorized() -> bool:
    now = time.time()
    if now - _l0_cache["ts"] < 5.0:
        return _l0_cache["result"]
    token_path = pathlib.Path("data/snapshots/L0_AUTH_TOKEN")
    try:
        result = (now - token_path.stat().st_mtime) < 300
    except FileNotFoundError:
        result = False
    _l0_cache["ts"] = now
    _l0_cache["result"] = result
    return result


def _pre_write_audit(content: str, rel_path: str) -> bool:
    if not rel_path.endswith(".py"):
        return True
    try:
        import ast

        ast.parse(content)
    except SyntaxError as e:
        logger.error(f"Pre-write audit: AST syntax error in {rel_path}: {e}")
        return False
    dangerous = ["eval(", "exec(", "os.system(", "subprocess.", "__import__("]
    for pattern in dangerous:
        if pattern in content:
            logger.error(f"Pre-write audit: Blocked dangerous pattern '{pattern}' in {rel_path}")
            return False
    try:
        from src.lachesis.verifiers.output_guard import OutputGuard

        guard = OutputGuard()
        if not guard._verify_output(content):
            logger.error(f"Pre-write audit: OutputGuard rejected {rel_path}")
            return False
    except Exception as e:
        logger.debug(f"Pre-write audit: OutputGuard check skipped ({e})")
    return True


def _backup_file(rel_path: str, project_root: str) -> None:
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


def _update_snapshot(rel_path: str, project_root: str) -> None:
    try:
        sm = SnapshotManager(project_root)
        sm.take_snapshot(rel_path)
    except Exception as e:
        logger.error(f"ToolBridge: Snapshot update failed for {rel_path} ({e})")


async def _ls(_bridge, input_data):
    input_path = input_data[0] if isinstance(input_data, list) else input_data
    base_dir = str(get_project_root())
    requested_path = await asyncio.to_thread(os.path.abspath, input_path)
    base_dir_safe = await asyncio.to_thread(os.path.commonpath, [base_dir, requested_path])
    if base_dir_safe != base_dir:
        logger.warning(f"ToolBridge: Path traversal blocked for {input_path}")
        return f"Error: Access denied to {input_path}. Stay within project root."
    return await asyncio.to_thread(os.listdir, requested_path)


async def _write_file(_bridge, input_data: dict[str, Any]) -> str | None:
    try:
        rel_path = input_data.get("path")
        content = input_data.get("content", "")
        if not rel_path:
            return "Error: Missing path"
        if _is_protected(rel_path):
            return "Error: Protected system path. Direct write to L0_AUTH_TOKEN is forbidden."
        if not _is_l0_authorized():
            return "Error: L0_AUTH_TOKEN missing or expired. Run: python scripts/create_l0_token.py"

        project_root = str(get_project_root())
        full_path = os.path.join(project_root, rel_path)

        if not _pre_write_audit(content, rel_path):
            return f"Error: Pre-write audit failed for {rel_path}"

        _backup_file(rel_path, project_root)

        temp_path = full_path + ".tmp"

        def write_sync() -> None:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            if os.path.exists(full_path):
                os.remove(full_path)
            os.rename(temp_path, full_path)

        await asyncio.to_thread(write_sync)

        _update_snapshot(rel_path, project_root)
        logger.info(f"ToolBridge: Successfully wrote {rel_path} (atomic + snapshot)")
        return f"Success: Wrote to {rel_path}"
    except Exception as e:
        logger.error(f"ToolBridge: write_file failed ({e})")
        return f"Error: {e!s}"


async def _replace_content(_bridge, input_data: dict[str, Any]):
    try:
        rel_path = input_data.get("path")
        target = input_data.get("target")
        replacement = input_data.get("replacement")
        if not rel_path or target is None or replacement is None:
            return "Error: Missing parameters"
        if _is_protected(rel_path):
            return "Error: Protected system path. Direct write to L0_AUTH_TOKEN is forbidden."
        if not _is_l0_authorized():
            return "Error: L0_AUTH_TOKEN missing or expired. Run: python scripts/create_l0_token.py"

        project_root = str(get_project_root())
        full_path = os.path.join(project_root, rel_path)

        def replace_sync() -> str:
            if not os.path.exists(full_path):
                return f"Error: File {rel_path} not found"
            with open(full_path, encoding="utf-8") as f:
                data = f.read()
            if target not in data:
                return f"Error: Target content not found in {rel_path}"
            new_data = data.replace(target, replacement)
            if not _pre_write_audit(new_data, rel_path):
                return f"Error: Pre-write audit failed for {rel_path}"
            _backup_file(rel_path, project_root)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_data)
            _update_snapshot(rel_path, project_root)
            return "Success"

        result = await asyncio.to_thread(replace_sync)
        return result
    except Exception as e:
        logger.error(f"ToolBridge: replace_content failed ({e})")
        return f"Error: {e!s}"


async def _run_code(_bridge, input_data):
    try:
        code = input_data.get("code") if isinstance(input_data, list) else str(input_data)
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
