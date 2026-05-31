# Contributing to Phantom Logos

Phantom Logos is an open-source, sovereign, local-first agentic OS built on Python 3.12+.
Contributions are welcome.

---

## 1. Getting Started

### Prerequisites

- Python 3.12+
- Git
- [Ollama](https://ollama.ai) v0.5+ (for local model execution)
- NVIDIA GPU with 6+ GB VRAM (recommended) or CPU-only mode

### Setup

```powershell
# Clone
git clone https://github.com/siliconstencil/PhantomLogos
cd PhantomLogos

# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install (development mode)
pip install -e ".[dev]"

# Configure environment
copy .env.example .env  # Edit LLM_MODEL_DIR and other required vars

# Generate local MCP config
python scripts/setup_mcp_config.py

# Seed memory axes (first time)
python scripts/seed_14_axes.py

# Verify setup
PYTHONPATH=. pytest tests/ -m smoke -v
```

---

## 2. Architecture Overview

### Agent Tiers (RuFlow)

| Tier | Agent | Role |
|------|-------|------|
| L1 | Sophia | Strategic gateway, 14-axis memory |
| L2 | Clotho | Executor, LangGraph orchestrator |
| L3 | Lachesis | Auditor, formal verification (Z3) |

### Key Modules

- `src/architrave/` - Gateway client, model registry, MCP layer
- `src/clotho/` - LangGraph orchestrator, task execution
- `src/atropos/` - Context pruning, observability
- `src/muscle/` - Local runtime bridge (Ollama/llama.cpp)
- `cognition/mnemosyne/` - 14-axis persistent memory (SQLite + LanceDB)
- `agent/` - Declarative YAML agent definitions

---

## 3. Adding a New Memory Axis (Mnemosyne)

1. Define schema: add table to `cognition/mnemosyne/`
2. Create store class inheriting from base store pattern
3. Register axis ID in `src/utils/config.py` AXIS_MAP
4. Wire into `cognition/gnosis/` for context injection
5. Add tests in `tests/`

---

## 4. Adding a New Tool

1. Implement handler in `src/tools/` or `src/clotho/bridge/`
2. Register in tool dispatch map
3. Add tool name to relevant agent YAML in `agent/`
4. Document in `.antigravity/tools.md`

---

## 5. Coding Standards

- **Language:** English for all code, comments, logs, config (ASCII-only)
- **Type hints:** Required for all function signatures
- **Linting:** `ruff check src/` must pass with 0 errors
- **Type checking:** `python -m pyright src/` (pyright only, not mypy)
- **Logging:** Use `src.utils.logging_config.setup_logger`, never `print()`
- **Thread safety:** Any singleton accessed by multiple threads must use `threading.Lock`
- **No emojis** in any file

---

## 6. Running Tests

```powershell
# Smoke tests (fast, no external deps)
PYTHONPATH=. pytest tests/ -m smoke -v

# All unit tests
PYTHONPATH=. pytest tests/ -v -m "not integration"

# With coverage
PYTHONPATH=. pytest tests/ --cov=src --cov-report=term
```

---

## 7. Submitting a Pull Request

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes following the coding standards above
4. Ensure all smoke tests pass
5. Run `ruff check src/` - must be clean
6. Submit PR against `master` branch

For bug reports and feature requests, use [GitHub Issues](https://github.com/siliconstencil/PhantomLogos/issues).
