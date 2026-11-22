# Phantom Logos: Installation Guide

**Target:** Linux or Windows with an NVIDIA GPU (6+ GB VRAM recommended)
**Tested on:** RTX 4070 Laptop 8GB | 32 GB RAM | Python 3.12 | Ubuntu 26.04

The core is pure Python 3.12 and runs on Linux and Windows. GitHub Actions runs
the test suite on `ubuntu-latest`. Ollama provides the local models.

---

## 1. Prerequisites

- Python 3.12+
- Git
- [Ollama](https://ollama.ai) v0.5+
- NVIDIA Driver 545+ (CUDA 12.3+) for GPU acceleration
- Docker Desktop + NVIDIA Container Toolkit (optional)

## 2. Clone & Setup

The bootstrap script creates the virtual environment, installs the dependencies,
pulls the models, runs the Alembic migrations and seeds the memory stores:

```bash
git clone https://github.com/siliconstencil/PhantomLogos
cd PhantomLogos
python scripts/bootstrap.py
```

Manual alternative:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

`requirements.txt` is a hardware-specific superset (CUDA torch, optional
extras) and is not what the installer or CI uses.

## 3. Configure Environment

```bash
cp .env.example .env             # Windows: copy .env.example .env
```

Edit `.env` if your setup differs from the defaults:

- `OLLAMA_HOST` / `OLLAMA_BASE_URL`: the Ollama endpoint (default `127.0.0.1:11434`)
- `GPU_TOTAL_VRAM_GB`: usable VRAM (default `7.0`)
- `SLM_ENABLED`: the optional SuperLocalMemory daemon (default `false`)
- `PHANTOM_DATA_DIR`: relocate the runtime data directory (default `data/`)

On Windows, set the project root for path resolution:

```powershell
[System.Environment]::SetEnvironmentVariable("ANTIGRAVITY_ROOT", $PWD.Path, "User")
```

## 4. Generate Local Config

```bash
python scripts/setup_mcp_config.py
```

This writes `mcp_config.json` from `mcp_config.template.json` with the project
root substituted. The template lists the external MCP servers (sequential-thinking,
fetch, kg-mem, github, playwright, filesystem); each one is optional and needs
its own credentials or `npx` availability.

## 5. Required Models

`scripts/bootstrap.py` pulls these tags:

| Model | Type | VRAM | How |
|-------|------|------|-----|
| qwen3.5-4b-ud:latest | Main LLM (L1/L2) | 2.8 GB | `ollama pull` via the installer |
| ministral-3b-ud:latest | Light LLM (tier 1) | 2.2 GB | `ollama pull` via the installer |
| phi-4-mini-ud:latest | Reasoning (L3) | 2.8 GB | `ollama pull` via the installer |
| nomic-embed-text-v2-moe-q8:latest | Embedding | 0.5 GB | `ollama pull` via the installer |

The tags are custom aliases: `ollama cp <base-model> <tag>` creates them from the
upstream Ollama models. The base model behind `qwen3.5-4b-ud` is `qwen3.5:4b`,
behind `ministral-3b-ud` is `ministral-3:3b`, behind `phi-4-mini-ud` is
`phi4-mini:3.8b` and behind `nomic-embed-text-v2-moe-q8` is
`nomic-embed-text-v2-moe`.

## 6. Seed Memory & Verify

```bash
python scripts/seed_14_axes.py
python scripts/seed_semantic.py
python scripts/health_check_14_axes.py
pytest tests/ -m smoke -v
```

The health check prints the state of all 14 axes and one line for the optional
SuperLocalMemory daemon. An absent SLM daemon is reported as INFO, not BROKEN.

## 7. Running the System

```bash
# Start the Morpheus VRAM manager and the optional SLM daemon
python src/clotho/bootstrap.py --daemon

# CLI interface
python scripts/hermes_cli.py

# Operator dashboard (http://127.0.0.1:8080, override with PORT)
python scripts/dashboard.py
```

## 8. Optional: SuperLocalMemory (full memory mode)

SuperLocalMemory pins a newer torch and transformers than the project venv, so
it is installed into its own venv and runs as its own process:

```bash
python scripts/bootstrap.py --with-slm   # creates .venv-slm and installs superlocalmemory
.venv-slm/bin/slm serve start           # serves HTTP on 127.0.0.1:8765
```

Then set `SLM_ENABLED=true` in `.env`. Without it the system uses
LanceDB + Ollama, which is the supported default.

---

## VRAM Budget Reference (RTX 4070 8GB)

```
Total:          8.0 GB
OS reserve:    -1.0 GB
Usable:        ~7.0 GB

qwen3.5-4b-ud:       2.8 GB
phi-4-mini-ud:      2.8 GB
nomic (embedding):  0.5 GB
                    -------
Peak (one heavy):  ~2.8 GB
Headroom:          ~4.2 GB
```

Only one model heavier than 3 GB may be resident at a time; the Morpheus
scheduler flushes between transitions.

---

*Last Updated: 2026-07-22*
