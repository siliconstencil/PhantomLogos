"""
Phantom Logos Base Models (SSOT)
Centralized source of truth for all constants, VRAM requirements, and role assignments.
Extracted from model_registry.py to prevent circular dependencies.
"""

import os

# Sovereign/Gateway Model Aliases
MODEL_ALIASES = {
    "antigravity-strategic-gateway": "models/antigravity-strategic-gateway",
    "antigravity-execution-gateway": "models/antigravity-execution-gateway",
}

# Local Model Role Assignments (Ollama/Muscle)
LOCAL_REASONING_MODEL = "qwen3.5-4b-ud:latest"
LOCAL_VISION_MODEL = "qwen2.5-vl-3b:latest"
FALLBACK_MODEL = "tinyllama:latest"

ROLE_TO_MODEL = {
    "draft": {
        "primary": "qwen3.5-4b-ud:latest",
        "expert": "qwen3.5-9b-ud:latest",
        "fallback": "qwen3.5-2b-ud:latest",
        "light": "ministral-3b-ud:latest",
    },
    "critique": {
        "primary": "qwen3.5-4b-ud:latest",
        "expert": "qwen3.5-9b-ud:latest",
        "fallback": "phi-4-mini-ud:latest",
        "light": "ministral-3b-ud:latest",
    },
    "code": {
        "primary": "qwen3.5-4b-ud:latest",
        "light": "qwen3.5-2b-ud:latest",
    },
    "vision": {
        "primary": "qwen2.5-vl-3b:latest",
        "ocr": "qwen2-vl-ocr-2b:latest",
        "thinking": "mimo-7b-vl-ud:latest",
        "creative": "mimo-7b-vl-ud:latest",
        "light": "qwen2.5-vl-3b:latest",
    },
    "math": {
        "primary": "deepseek-r1-8b:latest",
        "expert": "deepseek-r1-8b:latest",
        "expert_alt": "deepseek-r1-qwen3-8b:latest",
        "high": "qwen2.5-math-7b-q4:latest",
        "medium": "smollm3-3b:latest",
        "light": "qwen2.5-math-1.5b:latest",
        "light_alt": "open-xi-math:latest",
        "ultra_light": "math-mini-0.6b:latest",
        "fallback": "deepseek-math-7b:latest",
    },
    "tool_calling": {
        "primary": "functiongemma-270m:latest",
    },
    "ultra_light": {
        "primary": "deepscaler-1.5b:latest",
        "fallback": "deepseek-r1-1.5b:latest",
    },
    "router": {
        "primary": "granite-3-2b:latest",
    },
    "embedding": {
        "primary": "nomic-embed-text-v2-moe-q8:latest",
        "quality": "nomic-embed-text-v2-moe-q16:latest",
    },
    "reranker": {
        "primary": "jina-reranker-v3:latest",
    },
    "ner": {
        "primary": "fastino/gliner2-base-v1",
    },
}

# Vision Routing (Runtime Classification - SSOT)
VISION_ROUTING = {
    "ocr": {"model": "qwen2-vl-ocr-2b:latest", "runtime": "ollama"},
    "thinking": {"model": "mimo-7b-vl-ud:latest", "runtime": "ollama"},
    "creative": {"model": "mimo-7b-vl-ud:latest", "runtime": "ollama"},
    "primary": {"model": "qwen2.5-vl-3b:latest", "runtime": "ollama"},
}

# VRAM Requirements (GB)
VRAM_CATALOG_GB = {
    "granite-3-2b:latest": 1.6,
    "nomic-embed-text-v2-moe-q8:latest": 0.5,
    "nomic-embed-text-v2-moe-q16:latest": 1.0,
    "jina-reranker-v3:latest": 0.6,
    "jina-embeddings-v3:latest": 0.6,
    "phi-4-mini-ud:latest": 2.8,
    "ministral-3b-ud:latest": 2.2,
    "granite-4.1-8b-ud:latest": 5.5,
    "qwen2.5-coder-3b:latest": 2.5,
    "qwen2.5-coder-3b-ud:latest": 2.5,
    "qwen2.5-coder-7b:latest": 4.7,
    "qwen2.5-coder-0.5b:latest": 0.5,
    "llama-3.2-3b-ud:latest": 2.1,
    "llama-3.2-1b-ud:latest": 0.9,
    "qwen2.5-vl-3b:latest": 2.5,
    "qwen2-vl-ocr-2b:latest": 1.1,
    "nemotron-3-nano-4b-ud:latest": 4.6,
    "hermes-3-llama-3.1-8b:latest": 4.9,
    "qwen2.5-math-7b-q4:latest": 4.7,
    "deepscaler-1.5b:latest": 1.1,
    "functiongemma-270m:latest": 0.3,
    "smollm2-1.7b-q5:latest": 1.2,
    "deepseek-r1-1.5b:latest": 1.1,
    "mimo-7b-vl-ud:latest": 5.7,
    "mimo-7b-txt-ud:latest": 5.7,
    "deepseek-math-7b:latest": 4.7,
    "tinyllama:latest": 0.7,
    "qwen3.5-0.8b-ud:latest": 1.2,
    "qwen3.5-2b-ud:latest": 1.9,
    "qwen3.5-4b-ud:latest": 2.9,
    "qwen3.5-9b-ud:latest": 6.0,
    "meta-llama-3.1-8b:latest": 4.9,
    "math-mini-0.6b:latest": 0.45,
    "smollm3-3b:latest": 1.9,
    "qwen2.5-math-1.5b:latest": 1.1,
    "open-xi-math:latest": 1.1,
    "deepseek-r1-8b:latest": 5.1,
    "deepseek-r1-qwen3-8b:latest": 5.1,
    "qwq-math-io-500m:latest": 0.4,
    "fastino/gliner2-base-v1": 0.8,
}

# GPU Constants
GPU_TOTAL_VRAM_GB = float(os.getenv("GPU_TOTAL_VRAM_GB", 7.0))
GPU_SAFETY_MARGIN_GB = 1.0
GPU_USABLE_VRAM_GB = GPU_TOTAL_VRAM_GB - GPU_SAFETY_MARGIN_GB

# Capability Profiles
CAPABILITY_MAP = {
    "strategic": "models/antigravity-strategic-gateway",
    "execution": "qwen3.5-4b-ud:latest",
    "audit": "qwen3.5-4b-ud:latest",
    "math": "deepseek-r1-8b:latest",
    "tool_calling": "functiongemma-270m:latest",
    "ultra_light": "deepscaler-1.5b:latest",
    "vision_deep": "qwen2.5-vl-3b:latest",
    "ner": "fastino/gliner2-base-v1",
    "prune": None,
    "vram_manager": None,
    "external": None,
}
