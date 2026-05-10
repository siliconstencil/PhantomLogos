# [SRC:axis_1] Morpheus VRAM Configuration & Strategy

# Phase 11.18.15: Morpheus 8GB Dynamic Config
MODEL_SETS = {
    "default": {
        "models": ["qwen2-5-coder-7b-instruct-q4_k_m:latest", "phi-4-mini-reasoning-ud-q5_k_xl:latest"],
        "strategy": "need_based"
    },
    "vision_ocr": {
        "models": ["qwen2-vl-ocr:latest"],
        "strategy": "all_at_once"
    },
    "vision_full": {
        "models": ["mimo-vl:latest"],
        "strategy": "all_at_once"
    },
    "fast": {
        "models": ["deepscaler-1-5b-preview-q4_k_m:latest", "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest"],
        "strategy": "all_at_once"
    },
    "verification": {
        "models": ["qwen2-5-coder-7b-instruct-q4_k_m:latest", "qwen2-5-coder-3b-instruct-q6_k:latest"],
        "strategy": "all_at_once"
    }
}

# Phase 11.21.x: Core models that must never be auto-evicted (keeps IDE responsive)
CORE_MODELS = [
    "qwen2-5-coder-7b-instruct-q4_k_m:latest",  # L2 Primary — always resident for IDE
    "tinyllama:latest",                         # OOM recovery — always available
]

EVICTION_ORDER = [
    "phi-4-mini-reasoning-ud-q5_k_xl:latest",       # L3 (en once bosalt)
    "mimo-vl:latest",                              # Vision flagship (5.7GB w/ mmproj)
    "qwen2-5-coder-3b-instruct-q6_k:latest",       # Verification
    "qwen2-vl-ocr:latest",                         # Vision OCR
    "deepseek-math:7b",                            # Math verify (Phase 11.20)
    "ministral-3-3b-reasoning-2512-ud-q4_k_xl:latest", # L2 Light
    "deepseek-r1:7b",                              # R1 reasoning (Phase 11.20, larger, daha gec bosalt)
    "deepscaler-1-5b-preview-q4_k_m:latest",       # L0
    "qwen2-5-coder-7b-instruct-q4_k_m:latest",     # L2 Primary (en son)
    "tinyllama:latest",                            # OOM recovery (en kucuk, en son)
    "qwen2.5-vl:latest",                           # Vision light (yedek)
]
