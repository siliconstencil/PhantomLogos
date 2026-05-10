"""
Phantom Logos Model Registry (SSOT)
Centralized source of truth for all model mappings, VRAM requirements, and role assignments.
"""
import os
from typing import Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Sovereign/Gateway Model Aliases
# Note: Capability-based routing (Model-Agnostic refactor) is the goal.
# Currently YAML files reference these aliases; capability will replace in Phase 0.
MODEL_ALIASES = {
    "antigravity-strategic-gateway": "models/antigravity-strategic-gateway",
    "antigravity-execution-gateway": "models/antigravity-execution-gateway",
}

# Local Model Role Assignments (Ollama/Muscle)
LOCAL_REASONING_MODEL = "phi-4-mini-reasoning-ud-q5_k_xl:latest"
LOCAL_VISION_MODEL = "mimo-vl:latest"
ROLE_TO_MODEL = {
    "draft": {
        "primary": "qwen2-5-coder-7b-instruct-q4_k_m:latest",
        "fallback": "granite-4.1-8b:latest",
        "light": "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest",
    },
    "critique": {
        "primary": "phi-4-mini-reasoning-ud-q5_k_xl:latest",
        "fallback": "qwen2-5-coder-7b-instruct-q4_k_m:latest",
        "light": "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest",
    },
    "code": {
        "primary": "qwen2-5-coder-7b-instruct-q4_k_m:latest",
        "light": "qwen2-5-coder-3b-instruct-q6_k:latest",
    },
    "vision": {
        "primary": "mimo-vl:latest",
        "ocr": "qwen2-vl-ocr:latest",
        "thinking": "mimo-vl:latest",
        "creative": "mimo-vl:latest",
        "light": "mimo-vl:latest",
    },
    "math": {
        "primary": "qwen2.5-math-7b:latest",
        "light": "deepscaler-1-5b-preview-q4_k_m:latest",
        "fallback": "deepseek-math:7b",
    },
    "tool_calling": {
        "primary": "functiongemma-270m-it-q8_0:latest",
    },
    "ultra_light": {
        "primary": "deepscaler-1-5b-preview-q4_k_m:latest",
        "fallback": "deepseek-r1-distill-qwen-1-5b-q8_0:latest",
    },
    "router": {
        "primary": "granite-3-0-2b-instruct-q4_k_m:latest",
    },
    "embedding": {
        "primary": "nomic-embed-text-v2-moe-q8:latest",
        "quality": "nomic-embed-text-v2-moe-q16:latest",
    },
    "reranker": {
        "primary": "jina-reranker-v3-q8_0:latest",
    },
}

# Vision Routing (Runtime Classification - SSOT)
# Maps vision variants to their specific execution backends and paths.
VISION_ROUTING = {
    "ocr": {"model": "qwen2-vl-ocr:latest", "runtime": "ollama"},
    "thinking": {"model": "mimo-vl:latest", "runtime": "ollama"},
    "creative": {"model": "mimo-vl:latest", "runtime": "ollama"},
    "primary": {"model": "mimo-vl:latest", "runtime": "ollama"}
}

# VRAM Requirements (GB) -- synced with ollama list
VRAM_CATALOG_GB = {
    "granite-3-0-2b-instruct-q4_k_m:latest": 1.6,
    "nomic-embed-text-v2-moe-q8:latest": 0.5,
    "nomic-embed-text-v2-moe-q16:latest": 1.0,
    "jina-reranker-v3-q8_0:latest": 0.6,
    "jina-embeddings-v3-q8_0:latest": 0.6,
    "phi-4-mini-reasoning-ud-q5_k_xl:latest": 2.8,
    "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest": 2.2,
    "qwen3-4b-ud-q6_k_xl:latest": 3.7,
    "granite-4.1-8b:latest": 5.5,
    "qwen2-5-coder-3b-instruct-q6_k:latest": 2.5,
    "qwen2-5-coder-7b-instruct-q4_k_m:latest": 4.7,
    "llama-3-2-3b-instruct-ud-q4_k_xl:latest": 2.1,
    "llama-3-2-1b-instruct-ud-q5_k_xl:latest": 0.9,
    "qwen2.5-vl:latest": 2.5,
    "qwen2-vl-ocr:latest": 1.1,
    "nemotron-3-nano-4b-ud-q6_k_xl:latest": 4.6,
    "hermes-3-llama-3-1-8b-q4_k_m:latest": 4.9,
    "qwen2.5-math-7b:latest": 4.7,
    "deepscaler-1-5b-preview-q4_k_m:latest": 1.1,
    "functiongemma-270m-it-q8_0:latest": 0.3,
    "smollm2-1.7b:latest": 1.2,
    "qwen2.5-coder-0.5b:latest": 0.5,
    "deepseek-r1-distill-qwen-1-5b-q8_0:latest": 1.1,
    "qwen3-5-9b-ud-q4_k_xl:latest": 5.8,
    "mimo-vl:latest": 5.7,
    "deepseek-r1:7b": 4.7,
    "deepseek-math:7b": 4.7,
    "tinyllama:latest": 0.7,
    "qwen3-5-0-8b-ud-q8_k_xl:latest": 1.2,
    "qwen3-5-2b-ud-q6_k_xl:latest": 1.9,
    "qwen3-5-4b-ud-q4_k_xl:latest": 2.9,
    "meta-llama-3-1-8b-instruct-q4_k_m:latest": 4.9,
    "qwen2-5-coder-3b-instruct-q4_k_m:latest": 2.1,
    "qwen2.5-coder-0.5b-q5_k_m:latest": 0.5,
}

# GPU Constants
GPU_TOTAL_VRAM_GB = float(os.getenv("GPU_TOTAL_VRAM_GB", 8.0))
GPU_SAFETY_MARGIN_GB = 1.0  # Phase 11.18.3: 1GB reserved for Windows/System
GPU_USABLE_VRAM_GB = GPU_TOTAL_VRAM_GB - GPU_SAFETY_MARGIN_GB

# Capability Profiles (Model-Agnostic)
# Maps agent roles to actual model resolution.
# This is the primary lookup; MODEL_ALIASES is backward compat.
CAPABILITY_MAP = {
    "strategic": "models/antigravity-strategic-gateway",
    "execution": "qwen2-5-coder-7b-instruct-q4_k_m:latest",
    "audit": "phi-4-mini-reasoning-ud-q5_k_xl:latest",
    "math": "qwen2.5-math-7b:latest",
    "tool_calling": "functiongemma-270m-it-q8_0:latest",
    "ultra_light": "deepscaler-1-5b-preview-q4_k_m:latest",
    "vision_deep": "mimo-vl:latest",
    "prune": None,
    "vram_manager": None,
    "external": None,
}

def resolve_model(alias: str) -> str:
    return MODEL_ALIASES.get(alias, alias)

def resolve_capability(capability: str) -> Optional[str]:
    """Resolve a capability profile to a model name. Returns None for deterministic/external."""
    return CAPABILITY_MAP.get(capability)

def resolve_local_model(role: str, variant: str = "primary") -> str:
    return ROLE_TO_MODEL.get(role, {}).get(variant, role)

def get_embedding_model(variant: str = "primary") -> str:
    """Returns the Ollama name for the embedding model (SSOT)."""
    return ROLE_TO_MODEL.get("embedding", {}).get(variant, "nomic-embed-text-v2-moe-q8:latest")

def get_qwed_models() -> dict:
    """Returns the primary and fallback models for QWED verification."""
    return {
        "primary": ROLE_TO_MODEL.get("code", {}).get("light", "qwen2-5-coder-3b-instruct-q6_k:latest"),
        "fallback": ROLE_TO_MODEL.get("tool_calling", {}).get("primary", "functiongemma-270m-it-q8_0:latest")
    }

def get_vision_routing(variant: str = "primary") -> dict:
    """Returns the routing information for a vision variant (Ollama vs Local)."""
    return VISION_ROUTING.get(variant, VISION_ROUTING["primary"])

def get_vram_requirement(model_name: str) -> float:
    return VRAM_CATALOG_GB.get(model_name, 2.0)

def find_fitting_model(role: str, available_vram_gb: float) -> str:
    # Sprint B: Consult SelfTuner for Axis 8 performance-based selection
    try:
        from src.lachesis.self_tuner import SelfTuner
        tuner = SelfTuner()
        best_model = tuner.get_best_model_for_role(role)
        if best_model and get_vram_requirement(best_model) <= available_vram_gb:
            return best_model
    except ImportError:
        logger.warning(f"ModelRegistry: SelfTuner not available for role '{role}'")
    except Exception as e:
        logger.warning(f"ModelRegistry: SelfTuner lookup failed for role '{role}': {e}")

    variants = ROLE_TO_MODEL.get(role, {})
    for variant in ("primary", "light", "fallback"):
        model = variants.get(variant)
        if model and get_vram_requirement(model) <= available_vram_gb:
            return model
    return variants.get("light", variants.get("primary", LOCAL_REASONING_MODEL))
