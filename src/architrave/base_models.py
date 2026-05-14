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
LOCAL_REASONING_MODEL = "phi-4-mini-reasoning-ud-q5_k_xl:latest"
LOCAL_VISION_MODEL = "qwen2.5-vl:latest"
FALLBACK_MODEL = "tinyllama:latest"

ROLE_TO_MODEL = {
    "draft": {
        "primary": "qwen3-5-4b-ud-q4_k_xl:latest",
        "expert": "qwen3.5-9b-ud:latest",
        "fallback": "qwen3-5-2b-ud-q6_k_xl:latest",
        "light": "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest",
    },
    "critique": {
        "primary": "phi-4-mini-reasoning-ud-q5_k_xl:latest",
        "fallback": "qwen3-5-4b-ud-q4_k_xl:latest",
        "light": "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest",
    },
    "code": {
        "primary": "qwen3-5-4b-ud-q4_k_xl:latest",
        "light": "qwen3-5-2b-ud-q6_k_xl:latest",
    },
    "vision": {
        "primary": "qwen2.5-vl:latest",
        "ocr": "qwen2-vl-ocr:latest",
        "thinking": "mimo-vl:latest",
        "creative": "mimo-vl:latest",
        "light": "qwen2.5-vl:latest",
    },
    "math": {
        "primary": "deepseek-r1-8b:latest",
        "expert": "deepseek-r1-8b:latest",
        "high": "qwen2.5-math-7b:latest",
        "medium": "smollm3-3b:latest",
        "light": "qwen2.5-math-1.5b:latest",
        "light_alt": "open-xi-math:latest",
        "ultra_light": "math-mini-0.6b:latest",
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
    "ner": {
        "primary": "fastino/gliner2-base-v1",
    },
}

# Vision Routing (Runtime Classification - SSOT)
VISION_ROUTING = {
    "ocr": {"model": "qwen2-vl-ocr:latest", "runtime": "ollama"},
    "thinking": {"model": "mimo-vl:latest", "runtime": "ollama"},
    "creative": {"model": "mimo-vl:latest", "runtime": "ollama"},
    "primary": {"model": "qwen2.5-vl:latest", "runtime": "ollama"},
}

# VRAM Requirements (GB)
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
    "math-mini-0.6b:latest": 0.45,
    "smollm3-3b:latest": 1.9,
    "qwen2.5-math-1.5b:latest": 1.1,
    "open-xi-math:latest": 1.1,
    "deepseek-r1-8b:latest": 5.1,
    "qwen3.5-9b-ud:latest": 6.0,
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
    "execution": "qwen3-5-4b-ud-q4_k_xl:latest",
    "audit": "phi-4-mini-reasoning-ud-q5_k_xl:latest",
    "math": "deepseek-r1-8b:latest",
    "tool_calling": "functiongemma-270m-it-q8_0:latest",
    "ultra_light": "deepscaler-1-5b-preview-q4_k_m:latest",
    "vision_deep": "qwen2.5-vl:latest",
    "ner": "fastino/gliner2-base-v1",
    "prune": None,
    "vram_manager": None,
    "external": None,
}
