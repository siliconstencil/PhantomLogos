"""
Morpheus VRAM Registry Wrapper.
Centralized in src/architrave/model_registry.py

This module provides a unified interface for model selection based on VRAM constraints.
It maps functional roles (e.g., 'router', 'critique') to specific Ollama model aliases.
"""
from src.architrave.base_models import (
    VRAM_CATALOG_GB,
    GPU_TOTAL_VRAM_GB,
    GPU_SAFETY_MARGIN_GB,
    GPU_USABLE_VRAM_GB,
    ROLE_TO_MODEL,
)
from src.architrave.model_registry import (
    get_vram_requirement,
    find_fitting_model,
)

def get_vram_gb(model_name: str) -> float:
    return get_vram_requirement(model_name)

def resolve_mode(mode: str) -> dict:
    from ..morpheus.sweeper import VRAMSweeper
    return VRAMSweeper.MODEL_SETS.get(mode, VRAMSweeper.MODEL_SETS["default"])

__all__ = [
    "VRAM_CATALOG_GB",
    "GPU_TOTAL_VRAM_GB",
    "GPU_SAFETY_MARGIN_GB",
    "GPU_USABLE_VRAM_GB",
    "ROLE_TO_MODEL",
    "get_vram_gb",
    "find_fitting_model"
]
