# AGENTS.md

Phantom Logos is a **paused** (v1.2.1, July 2026) Python 3.12 local-first agentic OS
scaffold. Docs describe intent; the code is the source of truth. Read this before
changing anything.

## What this is

- A LangGraph orchestration stack: `src/clotho/orchestrator.py` builds the graph from
  `src/clotho/ergon/`; tier/loop routing lives in `src/clotho/krisis.py`.
- 14-axis persistent memory (SQLite + LanceDB under `data/`) in `cognition/mnemosyne/`;
  the strategic layer (Sophia, axis context assembly) is in `cognition/sophia/`.
- One LLM/MCP gateway: `src/architrave/gateway_client.py` (`GatewayArchitrave`). Local
  inference goes through Ollama (`OLLAMA_BASE_URL`, default `http://localhost:11434`);
  an optional local gateway proxy is read from `ANTIGRAVITY_GATEWAY_URL` (default
  `http://localhost:32553`). Model/VRAM lifecycle: `cognition/morpheus/`, `src/muscle/`.
- Formal verification chain (AST, QWED, SymPy, Z3) in `src/lachesis/verifiers/`, driven
  by `scripts/sovereign_audit.py`.
- MCP bridge in `src/architrave/mcp/`. The external SuperLocalMemory server is optional;
  `SLM_ENABLED=false` falls back to LanceDB + Ollama without raising.
- Scripts are the entrypoints; there is no installed console command.

## What this is not

- Not runnable out of the box. Flows need Ollama, the custom model tags in
  `scripts/bootstrap.py` (`qwen3.5-4b-ud`, `ministral-3b-ud`, `phi-4-mini-ud`,
  `nomic-embed-text-v2-moe-q8`), and the gitignored `data/`, `models/`, `bin/` dirs.
- Not a general-purpose library. There is no stable public API or package entrypoint.
- Not Windows-only despite the classifier and `.bat` files: POSIX `.sh` scripts, `bin/`
  paths, and a Linux CI exist.
- Not a git checkout in this working copy (no `.git`). Do not rely on branches,
  history, or `git diff`; `CONTRIBUTING.md` describes the upstream workflow.
- Not doc-consistent. Examples: `README.md` says the dashboard runs on `8765` but the
  code defaults to `8080`; `.env.example` is referenced but absent; some docs claim
  Turkish while checked-in docs are English.

## Setup

Python 3.12 is required. Preferred bootstrap:

```bash
python scripts/bootstrap.py              # creates .venv, installs -e ".[dev]", needs Ollama
python scripts/bootstrap.py --skip-models   # skip model pulls
python scripts/bootstrap.py --check-only    # verify an existing install
```

Bootstrap also creates `data/ logs/ models/ bin/`, runs Alembic (`mnemosyne`,
`reliability`, `spatial`), seeds memory, and runs the health check.

Manual alternative: create a venv and `pip install -e ".[dev]"`. `requirements.txt` is a
pinned, hardware-specific superset (CUDA torch, `superlocalmemory`, `logfire`) and is
not what CI installs. `.env` is optional; `.env.example` is not in the repo.

## Commands

```bash
pytest tests/ -v
pytest tests/ -m "not integration and not slow" --timeout=60   # CI unit baseline
pytest tests/ -m smoke -v
pytest tests/test_router.py::test_router_classification -v

python -m ruff check src/ cognition/ tests/
python -m ruff format src/ cognition/ scripts/ tests/
pyright src/

alembic -n mnemosyne upgrade head
alembic -n reliability upgrade head
alembic -n spatial upgrade head

python scripts/hermes_cli.py init|load|save|search|close|list
python scripts/health_check_14_axes.py
python scripts/dashboard.py      # http://127.0.0.1:8080, override with PORT
```

- CI (`.github/workflows/ci.yml`) runs the unit subset with **21 test files ignored** and a
  30% coverage gate. `mkdir -p data` is required before pytest in a clean checkout.
- Tests needing live Ollama or a gateway are marked `slow` / `integration`; skip rationale
  is in `tests/IGNORED_TESTS.md`.
- Root `pyrightconfig.json` overrides `[tool.pyright]` in `pyproject.toml`. It is `basic`
  and suppresses several reports, so a clean `pyright` is weak evidence.
- `alembic upgrade head` alone is wrong; this project uses named sections.

## Architecture map

| Path | Responsibility |
| :--- | :--- |
| `src/clotho/` | LangGraph graph, nodes, routing, bootstrap, control handoff, MCP bridge client |
| `cognition/mnemosyne/` | Per-axis stores and models; `cognition/sophia/` assembles axis context |
| `src/architrave/` | Gateway client, model registry, context cache, entity extraction, MCP |
| `src/lachesis/` | Verifiers, self-tuner, snapshot manager, file watchdog, codebase mapper |
| `src/muscle/` | Local runtime and reranker wrappers; `cognition/morpheus/` owns VRAM/scheduling |
| `src/atropos/` | Context pruning, token budget, compression, observability |
| `scripts/` | Bootstrap, CLI, dashboard, seeding, audits, health checks |
| `agent/` | Declarative agent YAML (sophia/clotho/lachesis/hermes/...) and agent skills |
| `dashboard/` | Operator SPA files served by `src/dashboard/api_server.py` |
| `.antigravity/` | Constitution, rules, tool inventory, generated topography |

Typical flow: script -> LangGraph node -> `GatewayArchitrave` -> local model / Ollama,
with memory reads/writes through `cognition/mnemosyne/` and verification through
`src/lachesis/verifiers/`.

## Conventions and gotchas

- Imports are absolute from the repo root (`from src...`, `from cognition...`). Run tools
  from the root; pytest sets `pythonpath = ["."]`, and scripts insert the root themselves.
- L0 token (`python scripts/create_l0_token.py`, 60s window) is enforced only by the
  runtime's own write bridge (`src/clotho/bridge/fs.py`). Editing repo files with an
  external agent does not require it.
- `opencode.template.json`, `mcp_config.template.json`, and `.mcp.template.json` are
  templates. Real `opencode.json` / `mcp_config.json` are gitignored; generate them with
  `scripts/setup_mcp_config.py` (substitutes `${PHANTOM_ROOT}`). Template edits do not
  change the local runtime.
- Gitignored, do not commit: `data/`, `logs/`, `scratch/`, `bin/`, `models/`, `projects/`,
  `.venv*`, `.env*`, `opencode/`, `.opencode/`, `opencode.json`, `mcp_config.json`.
- Code, comments, logs, and config are English ASCII-only. No emojis anywhere.
  User-facing chat follows `.antigravity/rules.json` (Turkish by default).
- Ruff: py312, line length 100, broad rule set including `S` and `ANN`.
- VRAM budget: 7.0 GB usable, 1.0 GB OS reserve; never load two >3 GB models at once and
  flush between transitions. Only relevant when touching `src/muscle/` or `cognition/morpheus/`.
- The project is paused. Make minimal, targeted changes; do not upgrade dependencies or
  refactor adjacent modules unless explicitly asked.

## References

- `README.md`, `docs/METHOD.md`, `docs/DASHBOARD.md`, `tests/IGNORED_TESTS.md`
- `.antigravity/CONSTITUTION.md`, `.antigravity/rules.json`, `.antigravity/tools.md`
- `opencode.template.json` already lists `AGENTS.md`, `.antigravity/topography.md`, and
  `.antigravity/tools.md` as instruction files.
