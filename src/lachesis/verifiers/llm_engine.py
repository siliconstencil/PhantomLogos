import asyncio
import re
from typing import Any

from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


class LLMMathEngine:
    """
    High-performance LLM-based math verification engine (Qwen Math / DeepSeek Math).
    Standardized to use 'is_valid' for consistency. [HH:MM AM/PM PT]
    """

    def __init__(self):
        self._models_checked = False
        self.deepseek_available = False
        self.qwen_math_available = False

    async def _check_models_lazy(self):
        if self._models_checked:
            return
        try:
            client = get_ollama_client()
            from src.architrave.model_registry import resolve_local_model

            models_info = await client.list()
            model_names = []
            if hasattr(models_info, "models"):
                model_names = [getattr(m, "model", "") for m in models_info.models]
            elif isinstance(models_info, list):
                for m in models_info:
                    if isinstance(m, dict):
                        model_names.append(m.get("name", m.get("model", "")))
                    else:
                        model_names.append(getattr(m, "model", getattr(m, "name", str(m))))

            ds_math = resolve_local_model("math", "fallback")
            qw_math = resolve_local_model("math", "primary")
            self.deepseek_available = any(ds_math in n for n in model_names)
            self.qwen_math_available = any(qw_math in n for n in model_names)
            self._models_checked = True
        except Exception as e:
            logger.warning(f"LLMMathEngine: Lazy model check failed ({e})")

    async def verify_math_llm(self, problem: str, light: bool = False) -> dict[str, Any]:
        await self._check_models_lazy()
        from src.architrave.model_registry import resolve_local_model

        if light:
            light_model = resolve_local_model("math", "light")
            return await self._call_math_ollama(problem, light_model)

        if self.deepseek_available:
            res = await self._call_deepseek_math(problem)
            if res.get("is_valid"):
                return res

        if self.qwen_math_available:
            # Morpheus flush in async context [Phase 1.0.24]
            try:
                from src.clotho.bootstrap import get_loader

                loader = get_loader()
                if loader:
                    await asyncio.to_thread(loader.flush)
            except Exception:
                pass

            qw_math = resolve_local_model("math", "primary")
            res = await self._call_math_ollama(problem, qw_math)
            if res.get("is_valid"):
                return res

        fallback_model = resolve_local_model("math", "light")
        return await self._call_math_ollama(problem, fallback_model)

    async def _call_math_ollama(self, problem: str, model: str) -> dict[str, Any]:
        try:
            client = get_ollama_client()
            prompt = f"Verify this math problem step by step. Return only VALID or INVALID in your final conclusion.\nProblem: {problem}"
            resp = await client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0},
            )
            content = resp.get("message", {}).get("content", "").upper()
            is_valid = "VALID" in content and "INVALID" not in content
            return {
                "is_valid": is_valid,
                "valid": is_valid,  # Alias
                "result": content,
                "logic_score": 0.85,
                "axis": 11,
            }
        except Exception as e:
            logger.error(f"LLMMathEngine: Math Ollama call failed ({e})")
            return {
                "is_valid": False,
                "valid": False,
                "error": str(e),
                "logic_score": 0.0,
                "axis": 11,
            }

    async def _call_deepseek_math(self, problem: str) -> dict[str, Any]:
        try:
            client = get_ollama_client()
            from src.architrave.model_registry import resolve_local_model

            ds_math = resolve_local_model("math", "fallback")
            if len(problem) > 12000:
                problem = problem[:12000]
            prompt = f"Please solve the following problem and put the final answer in \\boxed{{}}. Problem: \\boxed{{{problem}}}"
            resp = await client.chat(
                model=ds_math,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0},
            )
            content = resp.get("message", {}).get("content", "")
            match = re.search(r"\\boxed\{([^{}]*)\}", content)
            is_valid = bool(match)
            return {
                "is_valid": is_valid,
                "valid": is_valid,  # Alias
                "result": match.group(1) if match else content,
                "raw_content": content,
                "logic_score": 0.85,
                "axis": 11,
            }
        except Exception as e:
            logger.error(f"LLMMathEngine: DeepSeek Math call failed ({e})")
            return {
                "is_valid": False,
                "valid": False,
                "error": str(e),
                "logic_score": 0.0,
                "axis": 11,
            }
