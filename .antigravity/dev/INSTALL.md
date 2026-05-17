# Phantom Logos: Installation Guide

**Target:** ASUS ROG Zephyrus G16 (2023)
**GPU:** NVIDIA GeForce RTX 4070 Laptop (8GB VRAM, 128-bit, AD106)
**RAM:** 32 GB | **SSD:** 2 TB | **CPU:** Intel i7 | **OS:** Windows 11

---

## 1. Prerequisites

- Python 3.12+
- Git
- [Ollama](https://ollama.ai) v0.5+
- NVIDIA Driver 545+ (CUDA 12.3+)
- Docker Desktop + NVIDIA Container Toolkit (optional)

## 2. Clone & Virtual Environment

```powershell
git clone <repo-url> D:\Hank
cd D:\Hank
# Set root environment variable (Required for path resolution)
[System.Environment]::SetEnvironmentVariable("ANTIGRAVITY_ROOT", "D:\Hank", "User")

python -m venv .venv
.venv\Scripts\activate
```

Install core dependencies (Minimal set for local operation):

```powershell
pip install langgraph langchain-community ollama pydantic pydantic-ai google-genai
pip install lancedb tantivy numpy pandas tiktoken sympy z3-solver Pillow
pip install pyyaml requests httpx keyring nvidia-ml-py
```

## 3. Required Models

### Tier 0 -- Essential (System Cannot Function Without)

| # | Model | Type | VRAM | Disk | Download |
|---|---|---|---|---|---|
| 1 | **phi-4-mini-ud:latest** | Reasoning (Lachesis) | 2.8 GB | 2.5 GB | [unsloth/Phi-4-mini-reasoning-GGUF](https://huggingface.co/unsloth/Phi-4-mini-reasoning-GGUF) |
| 2 | **nomic-embed-text:latest** | Embedding (Axis 6) | 0.5 GB | 0.5 GB | `ollama pull nomic-embed-text` |
| 3 | **functiongemma-270m-it-Q8_0** | Router | 0.3 GB | 0.3 GB | [functiongemma/functiongemma-270m-it-Q8_0.gguf](https://huggingface.co/functiongemma/functiongemma-270m-it-Q8_0.gguf) |
| 4 | **jina-reranker-v3-Q8_0** | Reranker | 0.6 GB | 0.6 GB | [jinaai/jina-reranker-v3-Q8_0.gguf](https://huggingface.co/jinaai/jina-reranker-v3-Q8_0.gguf) |

**Total disk: ~3.9 GB | Concurrent VRAM: ~2.8 GB (phi-4) + swap**

### Tier 1 -- Recommended (Drop-in When Needed)

| # | Model | VRAM | Download |
|---|---|---|---|
| 5 | **qwen2-vl-ocr** (Vision OCR) | 2.1 GB | `ollama pull qwen2-vl-ocr` |
| 6 | **qwen2.5-coder-7b-instruct-q4_k_m** (Tier-2 Coding) | 4.7 GB | [Qwen/Qwen2.5-Coder-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) |

## 4. Ollama Import

After downloading GGUF files to your models directory (default: `D:\Google\AntiGravity\General Tools\`):

```powershell
# Create a Modelfile for each model:
echo "FROM D:\Google\AntiGravity\General Tools\phi-4-mini-ud-UD-Q5_K_XL.gguf" > Modelfile
ollama create phi-4-mini-ud -f Modelfile

# Repeat for each GGUF model
```

Ollama models (pull directly):

```powershell
ollama pull nomic-embed-text
ollama pull qwen2-vl-ocr
```

## 5. Environment Configuration

```powershell
copy .env.example .env
# Edit .env with your API keys:
#   GEMINI_API_KEY=your-key
#   DEEPSEEK_API_KEY=your-key

# Migrate to Windows Credential Manager (Mandatory for BA-01 compliance):
python scripts/migrate_keys.py
```

## 6. Verification

```powershell
# All tests pass:
pytest tests/ -v

# Models visible:
ollama list

# Runtime check (boots Morpheus daemon):
python src/clotho/bootstrap.py --check
```

## 7. Running the System

### Native Mode

```powershell
# Starts Morpheus VRAM Manager and Telemetry
python src/clotho/bootstrap.py --daemon
```

Scheduler will automatically load/unload models based on VRAM pressure. Idle timeout: 3 minutes (`idle_cooldown_s=180` -- tuned for 128-bit bus swap cost).

### Docker Mode (Production)

```powershell
docker compose build
docker compose up -d
```

See `docker-compose.yml` and `Dockerfile` for container topology.

---

## VRAM Budget (RTX 4070 Laptop 8GB)

```
Total:          8.0 GB
OS + Drivers:  -1.5 GB (Windows + Chromium + nvidia-smi)
Usable:        ~6.5 GB

phi-4 (resident):        2.8 GB
nomic (swappable):       0.5 GB
functiongemma (routing): 0.3 GB
jina (rerank on-demand): 0.6 GB
OS + buffers:            1.0 GB
                       --------
Peak:                   ~5.2 GB
Headroom:               ~1.3 GB
```

Models larger than available VRAM (e.g. qwen2.5-coder-7b at 4.7 GB) are swapped in via MorpheusScheduler on demand, unloading phi-4 first.

---

*Last Updated: 2026-05-05 [01:21 PM PT]*
