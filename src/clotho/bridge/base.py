import asyncio
import threading
import time
from typing import Any, ClassVar

from cognition.mnemosyne.session_log import SessionLog

from ...utils.logging_config import setup_logger
from ..activity import ActivityMonitor

logger = setup_logger(__name__)


class ToolBridge:
    """
    Managed Agents 'Hands' abstraction.
    [SRC:axis_2] Implements the Bridge pattern for tool orchestration.
    Decouples the brain (Sophia/Clotho) from tool execution (Muscle).
    """

    LOCAL_MODEL_MAP: ClassVar[dict] = {
        "qwen-7b": "qwen3.5-4b-ud:latest",
        "ministral-3b": "ministral-3b-ud:latest",
        "phi-4-mini": "phi-4-mini-ud:latest",
        "jina-reranker": "jina-reranker-v3:latest",
        "nomic-embed": "nomic-embed-text-v2-moe-q8:latest",
        "qwen-math": "qwen2.5-math-7b-q4:latest",
        "slm": "slm-mcp:latest",
    }

    _mcp_handlers: ClassVar[dict] = {}
    _warning_counter = 0
    _warning_counter_lock = threading.Lock()

    @classmethod
    def register_mcp_tool(cls, server_name: str, tool_name: str, handler: Any) -> None:
        ns_name = f"{server_name}_{tool_name}"
        cls._mcp_handlers[ns_name] = handler
        logger.info(f"ToolBridge: Dynamic MCP tool '{ns_name}' registered successfully.")

    def __init__(
        self, session_id: str, log: SessionLog | None = None, agent_id: str = "system"
    ) -> None:
        self.session_id = session_id
        self.log = log or SessionLog(session_id)
        self.agent_id = agent_id

    async def execute(
        self,
        tool_name: str,
        input_data: Any,
        is_anchor: bool = False,
        precedence: int = 100,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        start_time = time.monotonic()
        target_agent = agent_id or self.agent_id
        logger.info(
            f"ToolBridge: Executing {tool_name} for session {self.session_id} (agent: {target_agent})"
        )

        if tool_name in ("vision", "code"):
            try:
                from ..bootstrap import get_loader

                get_loader().flush()
                logger.info(f"ToolBridge: VRAM flushed for heavy tool '{tool_name}'")
            except Exception as e:
                logger.warning(f"ToolBridge: VRAM flush failed ({e})")

        # RBAC Check (Phase 11.20.1)
        try:
            from ..skill_loader import get_skill_loader

            loader = get_skill_loader()
            allowed = loader.get_allowed_tools_for_agent(target_agent)
            if allowed and tool_name not in allowed:
                logger.warning(
                    f"ToolBridge: RBAC WARNING - Agent '{target_agent}' calling UNAUTHORIZED tool '{tool_name}'. Allowed: {allowed}"
                )
                self._record_operational(
                    tool_name,
                    "WARNING",
                    f"RBAC violation: tool not in {allowed}",
                    agent_id=target_agent,
                )
        except Exception as e:
            logger.debug(f"ToolBridge: RBAC check skipped due to error ({e})")

        self.log.append(
            "tool.request", {"tool": tool_name, "input": input_data, "is_anchor": is_anchor}
        )

        try:
            ActivityMonitor().increment()
            result = await asyncio.wait_for(self._dispatch(tool_name, input_data), timeout=30.0)
            ActivityMonitor().decrement()
            output = str(result)
            latency = time.monotonic() - start_time

            anchor_metadata = (
                {"is_anchor": True, "precedence": precedence, "tool": tool_name}
                if is_anchor
                else {}
            )

            self.log.append(
                "tool.response",
                {
                    "tool": tool_name,
                    "status": "success",
                    "output_len": len(output),
                    "latency_sec": round(latency, 3),
                    **anchor_metadata,
                },
            )

            self._record_operational(
                tool_name,
                "INFO",
                f"success ({len(output)} bytes, {latency:.2f}s)",
                agent_id=target_agent,
            )

            try:
                from cognition.mnemosyne.procedural_store import ProceduralStore

                ProceduralStore().record_usage(
                    tool_name=tool_name,
                    task_type="execution",
                    success=True,
                    latency_ms=int(latency * 1000),
                )
            except Exception as pe:
                logger.debug(f"ToolBridge: Procedural record failed ({pe})")

            return {"output": output, "anchor": anchor_metadata, "latency": latency}
        except Exception as e:
            logger.error(f"ToolBridge: Execution failed for {tool_name} ({e})")
            self.log.append(
                "tool.response", {"tool": tool_name, "status": "error", "error": str(e)}
            )
            self._record_operational(tool_name, "ERROR", str(e), agent_id=target_agent)

            try:
                from cognition.mnemosyne.procedural_store import ProceduralStore

                ProceduralStore().record_usage(
                    tool_name=tool_name, task_type="execution", success=False
                )
            except Exception as e:
                logger.debug(f"ToolBridge: procedural record skipped ({e})")

            ActivityMonitor().decrement()
            return {"output": f"Error: {e!s}", "anchor": {}}

    def _resolve_model(self, name: str) -> str:
        """Resolves model name via registry SSOT with local fallback."""
        try:
            from ...architrave.model_registry import resolve_local_model

            # Priority 1: Registry (SSOT)
            resolved = resolve_local_model(name)
            if resolved != name:
                return resolved
        except ImportError:
            pass
        # Priority 2: Local Map
        return self.LOCAL_MODEL_MAP.get(name, name)

    def _record_operational(
        self, tool_name: str, level: str, message: str, agent_id: str = "system"
    ) -> None:
        try:
            from cognition.mnemosyne.operational_store import OperationalStore

            OperationalStore().record_event(
                name=f"tool_bridge.{tool_name}",
                level=level,
                message=message,
                agent_id=agent_id,
                tool_name=tool_name,
                session_id=self.session_id,
            )
        except Exception as e:
            logger.warning(f"ToolBridge: Operational event recording failed ({e})")

        # SLM Observe Integration (ERROR always, WARNING every 5th event, INFO ignored)
        should_observe = False
        upper_level = level.upper()
        if upper_level == "ERROR":
            should_observe = True
        elif upper_level == "WARNING":
            with ToolBridge._warning_counter_lock:
                ToolBridge._warning_counter += 1
                if ToolBridge._warning_counter % 5 == 0:
                    should_observe = True

        if should_observe:
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                if not slm.health():
                    return
                content = f"ToolBridge event: {tool_name} [{level}] {message}"
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(slm.aobserve(content=content, agent_id=agent_id))  # noqa: RUF006
                except RuntimeError:
                    # Fallback to sync observe if no running loop
                    slm.observe(content=content, agent_id=agent_id)
            except Exception as se:
                logger.debug(f"ToolBridge: SLM observe logging failed ({se})")

    async def _vram(self, input_data: Any) -> Any:
        try:
            from ..bootstrap import get_loader, quick_vram_check

            if isinstance(input_data, dict) and input_data.get("flush"):
                get_loader().flush()
                logger.info("ToolBridge: Manual VRAM flush triggered via tool.")

            actual_vram = await asyncio.to_thread(quick_vram_check)
            if isinstance(input_data, dict) and "claimed_free_gb" in input_data:
                await self._shadow_verify_claim(
                    "vram", input_data["claimed_free_gb"], context={"actual": actual_vram}
                )
            return actual_vram
        except Exception as e:
            return f"VRAM check error: {e!s}"

    async def _report(self, _input_data: Any) -> Any:
        try:
            from cognition.mnemosyne.operational_store import OperationalStore

            return await asyncio.to_thread(OperationalStore().get_usage_report)
        except Exception as e:
            return f"Report error: {e!s}"

    async def _shadow_verify_claim(
        self, claim_type: str, claimed_val: Any, context: dict | None = None
    ) -> None:
        is_valid = True
        detail = ""
        context = context or {}
        if claim_type == "vram":
            actual_gb = context.get("actual", 0.0)
            if abs(float(claimed_val) - actual_gb) > 0.5:
                is_valid = False
                detail = f"Claimed {claimed_val} GB free VRAM, but actual is {actual_gb} GB"
        elif claim_type == "ngl":
            context.get("model", "unknown")
            if int(claimed_val) > 100 or int(claimed_val) < 0:
                is_valid = False
                detail = f"Claimed impossible NGL layers: {claimed_val}"

        if not is_valid:
            logger.error(f"ToolBridge: SHADOW VERIFICATION FAILED ({claim_type}) - {detail}")
            try:
                from cognition.mnemosyne.meta_cognition import MetaCognitionStore

                from ...lachesis import get_output_guard

                get_output_guard().record_shadow_violation(
                    self.agent_id, detail, session_id=self.session_id
                )
                MetaCognitionStore().record_inconsistency(
                    agent_id=self.agent_id,
                    session_id=self.session_id,
                    claim=claim_type,
                    reasoning_val=claimed_val,
                    reality_val=context.get("actual", "NGL_MISMATCH"),
                )
                from ..bootstrap import get_loader

                get_loader().flush()
            except Exception as e:
                logger.warning(f"ToolBridge: Verification recording failed ({e})")

    async def _dispatch(self, tool_name: str, input_data: Any) -> Any:
        from .fs import _ls, _replace_content, _run_code, _write_file
        from .retrieval import _mapper, _prune, _semantic, _skill
        from .verify import _verify
        from .vision import _vision

        handlers = {
            "ls": _ls,
            "vision": _vision,
            "mapper": _mapper,
            "semantic": _semantic,
            "prune": _prune,
            "vram": self._vram,
            "skill": _skill,
            "verify": _verify,
            "report": self._report,
            "run_code": _run_code,
            "write_file": _write_file,
            "replace_content": _replace_content,
        }
        handler = handlers.get(tool_name) or self._mcp_handlers.get(tool_name)
        if handler is None:
            available = list(handlers.keys()) + list(self._mcp_handlers.keys())
            return f"Unknown tool: {tool_name}. Available: {', '.join(available)}"

        import inspect

        if inspect.iscoroutinefunction(handler):
            # If it's a bound method (like self._vram), 'self' is already included.
            if hasattr(handler, "__self__"):
                result = await handler(input_data)
            else:
                result = await handler(self, input_data)
        else:
            # Fallback for non-async or wrapped handlers
            if hasattr(handler, "__self__"):
                result = handler(input_data)
            else:
                result = handler(self, input_data)

        if tool_name == "run_code" and isinstance(result, dict) and result.get("status") == "error":
            try:
                from ...lachesis import get_output_guard

                get_output_guard().record_shadow_violation(
                    agent_id=self.agent_id,
                    detail=f"Tool {tool_name} failed: {result.get('stderr', 'Unknown error')}",
                )
            except Exception as e:
                logger.debug(f"ToolBridge: shadow violation record skipped ({e})")
        return result
