import os
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from qwed_sdk.qwed_local import QWEDLocal

    HAS_QWED = True
except ImportError:
    HAS_QWED = False


class QWEDEngine:
    """
    QWED SDK v5.0 implementation for multi-stage verification.
    Enforces Fail-Closed security policy. [HH:MM AM/PM PT]
    """

    def __init__(self, model: str | None = None):
        self.qwed = None
        self.qwed_fallback = None
        if HAS_QWED:
            try:
                from src.architrave.model_registry import get_qwed_models

                qwed_config = get_qwed_models()
                ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
                model_name = model or os.getenv("QWED_LOCAL_MODEL", qwed_config["primary"])
                self.qwed = QWEDLocal(
                    base_url=f"{ollama_host}/v1", model=model_name, api_key="not-needed", cache=True
                )
                if not model:
                    fallback_model = os.getenv("QWED_FALLBACK_MODEL", qwed_config["fallback"])
                    self.qwed_fallback = QWEDLocal(
                        base_url=f"{ollama_host}/v1",
                        model=fallback_model,
                        api_key="not-needed",
                        cache=True,
                    )
            except Exception as e:
                logger.error(f"QWEDEngine: Initialization failed ({e})")

    def audit_code_logic(self, code: str) -> dict[str, Any]:
        """Formal code security audit using QWED verify_code."""
        result = self._safe_qwed_call("verify_code", code)
        if result:
            return result
        # Fail-closed fallback if SDK fails completely
        return {
            "is_valid": False,
            "has_qwed": False,
            "logic_score": 0.0,
            "status": "SDK_FAILURE",
            "axis": 11,
        }

    def verify_math(self, expression: str) -> dict[str, Any]:
        """Verify mathematical validity via QWED SDK."""
        result = self._safe_qwed_call("verify_math", expression)
        if result:
            return result
        return {"is_valid": False, "has_qwed": False, "status": "SDK_FAILURE", "axis": 11}

    def verify_logic(self, premise: str) -> dict[str, Any]:
        """Verify logical consistency via QWED SDK."""
        result = self._safe_qwed_call("verify_logic", premise)
        if result:
            return result
        return {"is_valid": False, "has_qwed": False, "status": "SDK_FAILURE", "axis": 11}

    def verify_shell(self, command: str) -> dict[str, Any]:
        """Audit shell command for sovereign violations."""
        result = self._safe_qwed_call("verify_shell_command", command)
        if result:
            return result
        return {"is_valid": False, "has_qwed": False, "status": "SDK_FAILURE", "axis": 11}

    def _safe_qwed_call(self, method: str, content: str) -> dict[str, Any] | None:
        result = self._call_qwed_method(self.qwed, method, content)
        if result is not None:
            return result
        if self.qwed_fallback:
            logger.warning(f"QWEDEngine: Primary QWED failed on {method}, trying fallback")
            return self._call_qwed_method(self.qwed_fallback, method, content)
        return None

    def _call_qwed_method(self, qwed_instance, method: str, content: str) -> dict[str, Any] | None:
        if not qwed_instance:
            return None
        try:
            func = getattr(qwed_instance, method, None)
            if not func:
                logger.error(f"QWEDEngine: Method {method} not found in SDK.")
                return None

            result = func(content)
            if isinstance(result, dict):
                # Standardize keys
                return {
                    "is_valid": result.get("verified", result.get("valid", False)),
                    "logic_score": result.get("logic_score", result.get("confidence", 0.5)),
                    "status": result.get("status", "OK"),
                    "has_qwed": True,
                    "axis": 11,
                }

            return {
                "is_valid": getattr(result, "verified", getattr(result, "valid", False)),
                "logic_score": getattr(result, "logic_score", getattr(result, "confidence", 0.5)),
                "status": getattr(result, "status", "OK"),
                "has_qwed": True,
                "axis": 11,
            }
        except Exception as e:
            logger.debug(f"QWEDEngine: {method} failed ({e})")
            return None
