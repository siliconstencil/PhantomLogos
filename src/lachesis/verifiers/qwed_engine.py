import os
import re
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from qwed_sdk.qwed_local import QWEDLocal
    HAS_QWED = True
except ImportError:
    HAS_QWED = False

class QWEDEngine:
    def __init__(self, model: Optional[str] = None):
        self.qwed = None
        self.qwed_fallback = None
        if HAS_QWED:
            try:
                from src.architrave.model_registry import get_qwed_models
                qwed_config = get_qwed_models()
                ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
                model_name = model or os.getenv("QWED_LOCAL_MODEL", qwed_config["primary"])
                self.qwed = QWEDLocal(base_url=f"{ollama_host}/v1", model=model_name, api_key="not-needed", cache=True)
                if not model:
                    fallback_model = os.getenv("QWED_FALLBACK_MODEL", qwed_config["fallback"])
                    self.qwed_fallback = QWEDLocal(base_url=f"{ollama_host}/v1", model=fallback_model, api_key="not-needed", cache=True)
            except Exception as e:
                logger.error(f"QWEDEngine: Initialization failed ({e})")

    def audit_code_logic(self, code: str) -> Dict[str, Any]:
        """Formal code security audit using QWED verify_code."""
        _code_trigger = re.compile(r'^\s*if\s+True\s*:', re.MULTILINE)
        has_contradiction = bool(_code_trigger.search(code)) and "else:" in code
        if has_contradiction:
            return {"is_valid": False, "has_contradiction": True, "logic_score": 0.2, "axis": 11}

        result = self._safe_qwed_verify_code(code)
        if result is not None:
            return result
        return {
            "is_valid": not has_contradiction, "has_contradiction": has_contradiction,
            "logic_score": 0.9 if not has_contradiction else 0.2, "axis": 11
        }

    def _safe_qwed_verify_code(self, code: str) -> Optional[Dict[str, Any]]:
        result = self._call_qwed(self.qwed, code)
        if result is not None: return result
        if self.qwed_fallback:
            logger.warning("QWEDEngine: Primary QWED failed, trying fallback model")
            return self._call_qwed(self.qwed_fallback, code)
        return None

    def _call_qwed(self, qwed_instance, code: str) -> Optional[Dict[str, Any]]:
        if not qwed_instance: return None
        try:
            result = qwed_instance.verify_code(code)
            if isinstance(result, dict): return result
            return {
                "is_valid": getattr(result, "verified", False),
                "status": getattr(result, "status", "UNKNOWN"),
                "confidence": getattr(result, "confidence", 0.5),
                "axis": 11,
            }
        except Exception as e:
            logger.debug(f"QWEDEngine: QWED verify_code failed ({e})")
            return None
