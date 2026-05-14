"""
Phantom Logos Model Registry (SSOT)
Centralized source of truth for all model mappings, VRAM requirements, and role assignments.
"""

from ..utils.logging_config import setup_logger
from .base_models import (
    CAPABILITY_MAP,
    LOCAL_REASONING_MODEL,
    MODEL_ALIASES,
    ROLE_TO_MODEL,
    VISION_ROUTING,
    VRAM_CATALOG_GB,
)

logger = setup_logger(__name__)


def resolve_model(alias: str) -> str:
    return MODEL_ALIASES.get(alias, alias)


def resolve_capability(capability: str) -> str | None:
    """Resolve a capability profile to a model name. Returns None for deterministic/external."""
    return CAPABILITY_MAP.get(capability)


def resolve_local_model(role: str, variant: str = "primary") -> str:
    return ROLE_TO_MODEL.get(role, {}).get(variant, role)


def get_embedding_model(variant: str = "primary") -> str:
    """Returns the Ollama name for the embedding model (SSOT)."""
    return ROLE_TO_MODEL.get("embedding", {}).get(variant, "nomic-embed-text-v2-moe-q8:latest")


def get_qwed_models() -> dict:
    """Returns the primary and fallback models for QWED verification. [HH:MM AM/PM PT]"""
    return {"primary": "qwen3-5-2b-ud-q6_k_xl:latest", "fallback": "qwen3-5-4b-ud-q4_k_xl:latest"}


def get_vision_routing(variant: str = "primary") -> dict:
    """Returns the routing information for a vision variant (Ollama vs Local)."""
    return VISION_ROUTING.get(variant, VISION_ROUTING["primary"])


def get_vram_requirement(model_name: str) -> float:
    return VRAM_CATALOG_GB.get(model_name, 2.0)


def find_fitting_model(role: str, available_vram_gb: float) -> str:
    # Consult SelfTuner for Axis 8 performance-based selection
    try:
        from ..lachesis.self_tuner import SelfTuner

        tuner = SelfTuner()
        best_model = tuner.get_best_model_for_role(role)
        if best_model and get_vram_requirement(best_model) <= available_vram_gb:
            return best_model
    except ImportError:
        logger.warning(f"ModelRegistry: SelfTuner not available for role '{role}'")
    except Exception as e:
        logger.warning(f"ModelRegistry: SelfTuner lookup failed for role '{role}': {e}")

    variants = ROLE_TO_MODEL.get(role, {})
    # [Phase 1.0.24] Sort variants by VRAM requirement (descending) to find the best model that fits
    sorted_variants = sorted(
        variants.items(), key=lambda kv: get_vram_requirement(kv[1]), reverse=True
    )
    for variant_name, model in sorted_variants:
        if model and get_vram_requirement(model) <= available_vram_gb:
            return model
    return variants.get("light", variants.get("primary", LOCAL_REASONING_MODEL))
