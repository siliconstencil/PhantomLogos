import asyncio
import time
from typing import Any, Dict, Optional, List
from src.utils.logging_config import setup_logger
from cognition.mnemosyne.session_log import SessionLog
from src.clotho.activity import ActivityMonitor

logger = setup_logger(__name__)

class ToolBridge:
    """
    Managed Agents 'Hands' abstraction.
    [SRC:axis_2] Implements the Bridge pattern for tool orchestration.
    Decouples the brain (Sophia/Clotho) from tool execution (Muscle).
    """
    LOCAL_MODEL_MAP = {
        "qwen-7b": "qwen2-5-coder-7b-instruct-q4_k_m:latest",
        "ministral-3b": "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest",
        "phi-4-mini": "phi-4-mini-reasoning-ud-q5_k_xl:latest",
        "jina-reranker": "jina-reranker-v3-q8_0:latest",
        "nomic-embed": "nomic-embed-text-v2-moe-q8:latest",
        "qwen-math": "qwen2.5-math-7b:latest",
    }

    def __init__(self, session_id: str, log: Optional[SessionLog] = None, agent_id: str = "system"):
        self.session_id = session_id
        self.log = log or SessionLog(session_id)
        self.agent_id = agent_id

    async def execute(self, tool_name: str, input_data: Any, is_anchor: bool = False, precedence: int = 100, agent_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.monotonic()
        target_agent = agent_id or self.agent_id
        logger.info(f"ToolBridge: Executing {tool_name} for session {self.session_id} (agent: {target_agent})")

        if tool_name in ("vision", "code", "semantic"):
            try:
                from src.clotho.bootstrap import get_loader
                get_loader().flush()
                logger.info(f"ToolBridge: VRAM flushed for heavy tool '{tool_name}'")
            except Exception as e:
                logger.warning(f"ToolBridge: VRAM flush failed ({e})")

        self.log.append("tool.request", {"tool": tool_name, "input": input_data, "is_anchor": is_anchor})

        try:
            ActivityMonitor().increment()
            result = await asyncio.wait_for(self._dispatch(tool_name, input_data), timeout=30.0)
            ActivityMonitor().decrement()
            output = str(result)
            latency = time.monotonic() - start_time

            anchor_metadata = {"is_anchor": True, "precedence": precedence, "tool": tool_name} if is_anchor else {}

            self.log.append("tool.response", {
                "tool": tool_name, "status": "success", "output_len": len(output),
                "latency_sec": round(latency, 3), **anchor_metadata
            })

            self._record_operational(tool_name, "INFO", f"success ({len(output)} bytes, {latency:.2f}s)", agent_id=target_agent)

            try:
                from cognition.mnemosyne.procedural_store import ProceduralStore
                ProceduralStore().record_usage(tool_name=tool_name, task_type="execution", success=True, latency_ms=int(latency * 1000))
            except Exception as pe:
                logger.debug(f"ToolBridge: Procedural record failed ({pe})")

            return {"output": output, "anchor": anchor_metadata, "latency": latency}
        except Exception as e:
            logger.error(f"ToolBridge: Execution failed for {tool_name} ({e})")
            self.log.append("tool.response", {"tool": tool_name, "status": "error", "error": str(e)})
            self._record_operational(tool_name, "ERROR", str(e), agent_id=target_agent)
            
            try:
                from cognition.mnemosyne.procedural_store import ProceduralStore
                ProceduralStore().record_usage(tool_name=tool_name, task_type="execution", success=False)
            except: pass

            ActivityMonitor().decrement()
            return {"output": f"Error: {str(e)}", "anchor": {}}

    def _resolve_model(self, name: str) -> str:
        """Resolves model name via registry SSOT with local fallback."""
        try:
            from src.architrave.model_registry import resolve_local_model
            # Priority 1: Registry (SSOT)
            resolved = resolve_local_model(name)
            if resolved != name:
                return resolved
        except ImportError:
            pass
        # Priority 2: Local Map
        return self.LOCAL_MODEL_MAP.get(name, name)

    def _record_operational(self, tool_name: str, level: str, message: str, agent_id: str = "system"):
        try:
            from cognition.mnemosyne.operational_store import OperationalStore
            OperationalStore().record_event(
                name=f"tool_bridge.{tool_name}", level=level, message=message,
                agent_id=agent_id, tool_name=tool_name, session_id=self.session_id
            )
        except Exception as e:
            logger.warning(f"ToolBridge: Operational event recording failed ({e})")

    async def _vram(self, input_data: Any) -> Any:
        try:
            from src.clotho.bootstrap import quick_vram_check
            actual_vram = await asyncio.to_thread(quick_vram_check)
            if isinstance(input_data, dict) and "claimed_free_gb" in input_data:
                await self._shadow_verify_claim("vram", input_data["claimed_free_gb"], context={"actual": actual_vram})
            return actual_vram
        except Exception as e:
            return f"VRAM check error: {str(e)}"

    async def _report(self, input_data: Any) -> Any:
        try:
            from cognition.mnemosyne.operational_store import OperationalStore
            return await asyncio.to_thread(OperationalStore().get_usage_report)
        except Exception as e:
            return f"Report error: {str(e)}"

    async def _shadow_verify_claim(self, claim_type: str, claimed_val: Any, context: Optional[dict] = None):
        is_valid = True
        detail = ""
        if claim_type == "vram":
            actual_gb = context.get("actual", 0.0)
            if abs(float(claimed_val) - actual_gb) > 0.5:
                is_valid = False
                detail = f"Claimed {claimed_val} GB free VRAM, but actual is {actual_gb} GB"
        elif claim_type == "ngl":
            from src.architrave.model_registry import get_vram_requirement
            model_name = context.get("model", "unknown")
            if int(claimed_val) > 100 or int(claimed_val) < 0:
                is_valid = False
                detail = f"Claimed impossible NGL layers: {claimed_val}"
        
        if not is_valid:
            logger.error(f"ToolBridge: SHADOW VERIFICATION FAILED ({claim_type}) - {detail}")
            try:
                from src.lachesis import get_output_guard
                from cognition.mnemosyne.meta_cognition import MetaCognitionStore
                get_output_guard().record_shadow_violation(self.agent_id, detail, session_id=self.session_id)
                MetaCognitionStore().record_inconsistency(
                    agent_id=self.agent_id, session_id=self.session_id, claim=claim_type,
                    reasoning_val=claimed_val, reality_val=context.get("actual", "NGL_MISMATCH")
                )
                from src.clotho.bootstrap import get_loader
                get_loader().flush()
            except Exception as e:
                logger.warning(f"ToolBridge: Verification recording failed ({e})")

    async def _dispatch(self, tool_name: str, input_data: Any) -> Any:
        from .vision import _vision
        from .retrieval import _semantic, _skill, _mapper, _prune
        from .verify import _verify
        from .fs import _ls, _run_code

        handlers = {
            "ls": _ls, "vision": _vision, "mapper": _mapper,
            "semantic": _semantic, "prune": _prune, "vram": self._vram,
            "skill": _skill, "verify": _verify, "report": self._report,
            "run_code": _run_code,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return f"Unknown tool: {tool_name}. Available: {', '.join(handlers)}"
        
        if asyncio.iscoroutinefunction(handler):
            result = await handler(self, input_data)
        else:
            result = await handler(input_data)
            
        if tool_name == "run_code" and isinstance(result, dict) and result.get("status") == "error":
            try:
                from src.lachesis import get_output_guard
                get_output_guard().record_shadow_violation(agent_id=self.agent_id, detail=f"Tool {tool_name} failed: {result.get('stderr', 'Unknown error')}")
            except: pass
        return result
