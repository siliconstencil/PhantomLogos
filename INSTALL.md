# Phantom Logos: Installation Guide

**Target:** Windows 11 with NVIDIA GPU (6+ GB VRAM recommended)
**Tested on:** RTX 4070 Laptop 8GB | 32 GB RAM | Python 3.12

---

## 1. Prerequisites

- Python 3.12+
- Git
- [Ollama](https://ollama.ai) v0.5+
- NVIDIA Driver 545+ (CUDA 12.3+) - for GPU acceleration
- Docker Desktop + NVIDIA Container Toolkit (optional)

## 2. Clone & Setup

```powershell
git clone https://github.com/siliconstencil/phantom-logos
cd phantom-logos

# Set project root in user environment (required for path resolution)
[System.Environment]::SetEnvironmentVariable("ANTIGRAVITY_ROOT", $PWD.Path, "User")

python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 3. Configure Environment

```powershell
copy .env.example .env
# Edit .env:
#   LLM_MODEL_DIR = absolute path to your .gguf model files
#   GEMINI_API_KEY = your key (optional)
#   GPU_TOTAL_VRAM_GB = your GPU VRAM
```

## 4. Generate Local Config

```powershell
python scripts/setup_mcp_config.py
```

## 5. Required Models

### Tier 0 - Essential

| Model | Type | VRAM | How |
|-------|------|------|-----|
| phi-4-mini-ud:latest | Reasoning (L3) | 2.8 GB | Download GGUF, ollama create |
| nomic-embed-text:latest | Embedding | 0.5 GB | `ollama pull nomic-embed-text` |
| functiongemma-270m-it-Q8_0 | Router | 0.3 GB | Download GGUF, ollama create |
| jina-reranker-v3-Q8_0 | Reranker | 0.6 GB | Download GGUF, ollama create |

Download GGUF files from HuggingFace to your `LLM_MODEL_DIR`, then:

```powershell
# Example for phi-4-mini
echo "FROM $env:LLM_MODEL_DIR\phi-4-mini-ud-UD-Q5_K_XL.gguf" > Modelfile
ollama create phi-4-mini-ud -f Modelfile
```

### Tier 1 - Recommended

| Model | VRAM | How |
|-------|------|-----|
| qwen2-vl-ocr | 2.1 GB | `ollama pull qwen2-vl-ocr` |
| qwen2.5-coder-7b-instruct-q4_k_m | 4.7 GB | Download GGUF, ollama create |

## 6. Seed Memory & Verify

```powershell
python scripts/seed_14_axes.py
python scripts/health_check_14_axes.py
PYTHONPATH=. pytest tests/ -m smoke -v
```

## 7. Running the System

```powershell
# Start Morpheus VRAM manager
python src/clotho/bootstrap.py --daemon

# CLI interface
python scripts/hermes_cli.py
```

---

## VRAM Budget Reference (RTX 4070 8GB)

```
Total:          8.0 GB
OS reserve:    -1.5 GB
Usable:        ~6.5 GB

phi-4 resident:    2.8 GB
nomic (swap):      0.5 GB
router:            0.3 GB
reranker (demand): 0.6 GB
                  -------
Peak:            ~4.2 GB
Headroom:        ~2.3 GB
```

---

*Last Updated: 2026-05-30*
