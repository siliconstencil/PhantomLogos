# [SRC:axis_1] Morpheus VRAM Configuration & Strategy

# Phase 11.18.15: Morpheus 8GB Dynamic Config
MODEL_SETS = {
    "math_expert": {"models": ["deepseek-r1-8b:latest"], "strategy": "all_at_once"},
    "math_light": {
        "models": ["smollm3-3b:latest", "qwq-math-io-500m:latest"],
        "strategy": "all_at_once",
    },
    "expert_reasoning": {"models": ["qwen3.5-4b-ud:latest"], "strategy": "all_at_once"},
}

# [Phase 1.0.24] Updated Eviction Order (Heavy to Light)
EVICTION_ORDER = [
    "deepseek-r1-8b:latest",  # Heavy expert (5.1 GB)
    "deepseek-r1-qwen3-8b:latest",  # Heavy expert (5.1 GB)
    "qwen2.5-math-7b-q4:latest",  # Math high (4.7 GB)
    "deepseek-math-7b:latest",  # Math fallback (4.7 GB)
    "phi-4-mini-ud:latest",  # L3 Auditor (2.8 GB)
    "mimo-7b-vl-ud:latest",  # Flagship Vision (5.7 GB)
    "qwen2.5-vl-3b:latest",  # Standard Vision (2.5 GB)
    "smollm3-3b:latest",  # Math medium (1.9 GB)
    "qwen3.5-4b-ud:latest",  # L2 Primary (2.9 GB)
    "ministral-3b-ud:latest",  # L2 Light (2.2 GB)
    "open-xi-math:latest",  # Math light (1.1 GB)
    "qwen2.5-math-1.5b:latest",  # Math light (1.1 GB)
    "deepscaler-1.5b:latest",  # L2 Ultra-light (1.1 GB)
    "math-mini-0.6b:latest",  # Math ultra-light (0.45 GB)
    "qwq-math-io-500m:latest",  # Math bridge (0.4 GB)
    "nomic-embed-text-v2-moe-q8:latest",  # Embeddings (0.5 GB)
    "tinyllama:latest",  # OOM Recovery (0.7 GB)
]

CORE_MODELS = [
    "tinyllama:latest",
]
