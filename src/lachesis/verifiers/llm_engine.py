import re
import asyncio
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class LLMMathEngine:
    def __init__(self):
        self._models_checked = False
        self.deepseek_available = False
        self.qwen_math_available = False

    def _check_models_lazy(self):
        if self._models_checked: return
        try:
            import ollama
            from src.architrave.model_registry import resolve_local_model
            models_info = ollama.list()
            model_names = []
            if hasattr(models_info, "models"):
                model_names = [m.model for m in models_info.models]
            elif isinstance(models_info, list):
                model_names = [m.get("name", m.get("model", "")) for m in models_info]
            
            ds_math = resolve_local_model("math", "fallback")
            qw_math = resolve_local_model("math", "primary")
            self.deepseek_available = any(ds_math in n for n in model_names)
            self.qwen_math_available = any(qw_math in n for n in model_names)
            self._models_checked = True
        except Exception as e:
            logger.warning(f"LLMMathEngine: Lazy model check failed ({e})")

    def verify_math_llm(self, problem: str, light: bool = False) -> Dict[str, Any]:
        self._check_models_lazy()
        from src.architrave.model_registry import resolve_local_model
        
        if light:
            light_model = resolve_local_model("math", "light")
            return self._call_math_ollama(problem, light_model)

        if self.deepseek_available:
            res = self._call_deepseek_math(problem)
            if res.get("valid"): return res

        if self.qwen_math_available:
            try:
                from src.clotho.bootstrap import get_loader
                get_loader().flush()
            except: pass
            qw_math = resolve_local_model("math", "primary")
            res = self._call_math_ollama(problem, qw_math)
            if res.get("valid"): return res

        fallback_model = resolve_local_model("math", "light")
        return self._call_math_ollama(problem, fallback_model)

    def _call_math_ollama(self, problem: str, model: str) -> Dict[str, Any]:
        try:
            import ollama
            prompt = f"Verify this math problem step by step. Return only VALID or INVALID in your final conclusion.\nProblem: {problem}"
            resp = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.0})
            content = resp.get("message", {}).get("content", "").upper()
            return {"valid": "VALID" in content and "INVALID" not in content, "result": content, "confidence": 0.85, "axis": 11}
        except Exception as e:
            return {"valid": False, "error": str(e), "confidence": 0.0, "axis": 11}

    def _call_deepseek_math(self, problem: str) -> Dict[str, Any]:
        try:
            import ollama
            from src.architrave.model_registry import resolve_local_model
            ds_math = resolve_local_model("math", "fallback")
            if len(problem) > 12000: problem = problem[:12000]
            prompt = f"Please solve the following problem and put the final answer in \\boxed{{}}. Problem: \\boxed{{{problem}}}"
            resp = ollama.chat(model=ds_math, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.0})
            content = resp.get("message", {}).get("content", "")
            match = re.search(r"\\boxed\{([^{}]*)\}", content)
            return {"valid": bool(match), "result": match.group(1) if match else content, "raw_content": content, "confidence": 0.85, "axis": 11}
        except Exception as e:
            return {"valid": False, "error": str(e), "confidence": 0.0, "axis": 11}
