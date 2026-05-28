import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import record_step

logger = setup_logger(__name__)


async def vision_node(state: Any) -> dict[str, Any]:
    """Pre-processing node: run vision analysis before draft for image tasks."""
    image_path = state.get("image_path")
    if not image_path:
        return {"vision_analysis": "", "memory_sync": True}
    try:
        from src.clotho.bridge import ToolBridge

        bridge = ToolBridge(state["session_id"], agent_id="clotho")

        # [SRC:axis_14] Task-aware Prompting
        task = state["task"].lower()
        if any(kw in task for kw in ["read", "ocr", "text", "document"]):
            prompt = "OCR Mode: Extract all text from this image precisely. Maintain layout structure if possible."
        elif any(
            kw in task for kw in ["diagram", "circuit", "logic", "reason", "math", "structure"]
        ):
            prompt = "Thinking Mode: Analyze the structural logic and components of this diagram/circuit. Explain the relationships."
        elif any(kw in task for kw in ["scene", "art", "creative", "style", "describe"]):
            prompt = "Creative Mode: Describe the scene, artistic style, and emotional tone of this image in detail."
        else:
            prompt = "Primary Mode: Analyze this image in detail. Describe what you see."

        res = await bridge.execute("vision", {"image_path": image_path, "prompt": prompt})

        analysis = res.get("output", "")
        await asyncio.to_thread(record_step, state, "vision")
        logger.info(f"ergon: Vision analysis completed (mode={prompt.split(':')[0]})")
        return {"vision_analysis": analysis, "memory_sync": True}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: vision_node failed ({e})", exc_info=True)
        return {"vision_analysis": f"[Vision Error: {e}]", "memory_sync": False}
