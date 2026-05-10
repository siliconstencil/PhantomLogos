import os
import asyncio
from typing import Any
from src.utils.logging_config import setup_logger
from src.utils.sandbox import LightSandbox

logger = setup_logger(__name__)

async def _ls(bridge, input_data):
    input_path = input_data[0] if isinstance(input_data, list) else input_data
    base_dir = os.path.abspath(os.getcwd())
    requested_path = os.path.abspath(input_path)
    if os.path.commonpath([base_dir, requested_path]) != base_dir:
        logger.warning(f"ToolBridge: Path traversal blocked for {input_path}")
        return f"Error: Access denied to {input_path}. Stay within project root."
    return await asyncio.to_thread(os.listdir, requested_path)

async def _run_code(bridge, input_data):
    try:
        code = input_data.get("code") if isinstance(input_data, dict) else str(input_data)
        timeout = input_data.get("timeout", 10) if isinstance(input_data, dict) else 10
        sandbox = LightSandbox()
        try:
            stdout, stderr = await asyncio.to_thread(sandbox.run, code, timeout)
            if stderr:
                return {"stdout": stdout, "stderr": stderr, "status": "warning" if stdout else "error"}
            return {"stdout": stdout, "status": "success"}
        finally:
            sandbox.cleanup()
    except Exception as e:
        logger.error(f"ToolBridge: run_code failed ({e})")
        return f"Code execution error: {str(e)}"
