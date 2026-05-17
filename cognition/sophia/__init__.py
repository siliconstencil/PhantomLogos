# Bridge to Lachesis (Axis 11 Consolidation)
from src.lachesis.verifiers import SympyVerifier

from .gnosis import get_dynamic_context
from .eidos import CritiqueResult, ReasoningState
from .hephaestus import extract_tool_calls, strip_thinking_block
from .router import TaskRouter
from .sophia import run_critique, run_draft, run_refine
from src.architrave.model_registry import resolve_model
from .state_bus import StateBus, get_state_bus
from .temperature_control import get_temperature
from .tool_validator import ToolValidator

_v = SympyVerifier()
verify_math = _v.verify_math
verify_logic = _v.verify_logic
validate_algebraic_solution = _v.validate_algebraic_solution

__all__ = [
    "CritiqueResult",
    "ReasoningState",
    "StateBus",
    "TaskRouter",
    "ToolValidator",
    "extract_tool_calls",
    "get_dynamic_context",
    "get_state_bus",
    "get_temperature",
    "resolve_model",
    "run_critique",
    "run_draft",
    "run_refine",
    "strip_thinking_block",
    "validate_algebraic_solution",
    "verify_logic",
    "verify_math",
]
