# Phantom Logos v1.2.1 (Sovereign Rebirth)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Governance: BA--01](https://img.shields.io/badge/Governance-BA--01-red.svg)](#7-operational-constitution-ba-01-governance)
[![Memory: 14--Axis](https://img.shields.io/badge/Memory-14--Axis-green.svg)](#5-the-armory-14-axis-mnemosyne)

Status: **v1.2.1 Sovereign Stable**

## 1. Executive Summary

**Phantom Logos** is a sovereign, local-first agentic OS built on Python 3.12+ implementing a 3-tier hierarchical agent architecture (RuFlow) with 14-axis persistent memory (Mnemosyne), formal verification, and provider-agnostic LLM routing.

Core principles:
- **Sovereign**: All data stays local. Zero external API calls for reasoning/memory.
- **RuFlow Architecture**: L0 (Human) → L1 (Strategic) → L2 (Execution) → L3 (Verification).
- **14-Axis Memory**: Persistent cognitive state across Episodic, Procedural, Goals, Temporal, Spatial, Semantic, Operational, Meta-Cognitive, Tone, Rational, Verification, Efficiency, Cross-Session, and Visual axes.
- **Local-First Routing**: All LLM calls route through `GatewayArchitrave` (unified local/hybrid gateway) with formal verification via Z3 SAT solver.

---

## 2. RuFlow: 3-Tier Hierarchical Architecture

Phantom Logos implements a 3-tier agent hierarchy with declarative YAML definitions (hot-loadable, skill-wired).

### Agent Tiers

| Layer | Agent | Role | Model(s) | Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **L0** | Hank | Human Authority | N/A | Consent, L0_AUTH_TOKEN governance, final approval |
| **L1** | Sophia | Strategic Gateway | `qwen3.5-4b-ud` | Planning, 14-axis memory integration, architectural decisions, citation |
| **L2** | Clotho | Execution Gateway | `qwen3.5-4b-ud` (coding), `ministral-3b-ud` (routine), `deepscaler-1.5b` (rapid) | Task execution, code generation, tool orchestration, skill orchestration via LangGraph |
| **L3** | Lachesis | Auditor | `phi-4-mini-ud` (logic), `qwen2.5-coder-3b` (code/math) | Formal verification, adversarial auditing, Z3 SAT solving |

**Declaration**: Agent YAML files in `agent/` (sophia.yaml, clotho.yaml, lachesis.yaml). Skills defined in `agent/skills/`.

**See also:** [CLAUDE.md](CLAUDE.md#agent-tiers-ruflow-v110) for execution protocols.

---

## 3. Core Modules (`src/`)

| Module | Purpose |
| :--- | :--- |
| **architrave** | Central gateway client, model registry, context cache, entity extraction, OTL engine. Unified routing layer for all LLM calls. |
| **clotho** | LangGraph orchestrator, task execution, skill loading, agent bootstrap, execution coordination. |
| **atropos** | Context pruning, observability, matryoshka compression service. Manages token budget and memory compression. |
| **lachesis** | Self-tuner, snapshot manager, file watchdog. Triggers formal verification and auditing. |
| **ankyra** | Anchor/embedding generation. Semantic indexing for 14-axis memory. |
| **muscle** | Local runtime bridge (Ollama/llama.cpp), binary management, reranker integration. VRAM budget enforcement. |
| **tools** | MCP tool implementations (34 tools total). Device drivers for external systems. |
| **utils** | Config, logging, rate limiting, security, token budget management, project path resolution. |

---

## 5. The Armory: 14-Axis Mnemosyne

Persistent cognitive state across 14 dimensions stored in SQLite + LanceDB (`.data/`):

1. **Episodic**: Session/interaction history
2. **Procedural**: Learned task workflows and skills
3. **Goals**: Strategic objectives and constraints
4. **Temporal**: Time-aware event ordering and scheduling
5. **Spatial/Graph**: Entity relationships and system topology
6. **Semantic**: Vector embeddings and concept networks
7. **Operational**: Execution logs and observability
8. **Meta-Cognitive**: Self-reflection and strategy adaptation
9. **Tone**: Communication style and user preferences
10. **Rational**: Logical reasoning chains and proofs
11. **Verification**: Formal audit trails and Z3 SAT constraints
12. **Efficiency**: Performance metrics and optimization vectors
13. **Cross-Session Patterns**: Behavioral assertions and learned heuristics
14. **Visual**: Visual context and image embeddings

All strategic claims in outputs must cite the relevant axis as `[SRC:axis_N]`.

---

## 6. Sovereign Knowledge Base (.antigravity/)

Core governance and execution history centralized in `.antigravity/`:

- **[CONSTITUTION.md](.antigravity/CONSTITUTION.md)**: System laws, governance rules, Absolute Agnosticism mandates.
- **[rules.json](.antigravity/rules.json)**: Machine-readable governance rules (override task-completion urges).
- **[tools.md](.antigravity/tools.md)**: MCP tool inventory and capabilities.
- **[topography.md](.antigravity/topography.md)**: Live codebase map (auto-regenerated).
- **[walkthroughs/](.antigravity/walkthroughs/)**: Phase-by-phase execution history.
- **[audit/](.antigravity/audit/)**: Formal audit logs and verification proofs.

---

## 7. Operational Constitution (BA-01 Governance)

**BA-01** defines the communication protocol and security model:

1. **Language Protocol**:
   - L0 chat and user-facing `.md` artifacts: Turkish
   - Code, comments, logs, config, agent internals: English (ASCII-only)

2. **EMOJI_BAN**: Emojis and special decorations strictly prohibited everywhere.

3. **L0 Write Governance**:
   - All code edits, config changes, deletions require explicit L0 consent ("basla" / "yurut")
   - Valid `L0_AUTH_TOKEN` (60-second window, generated via `python scripts/create_l0_token.py`)
   - Pre-write audit: identify 2 potential breaking points before executing

4. **Sovereign Gateway Architecture**:
   - All LLM calls route through `architrave.GatewayArchitrave` (local/hybrid hybrid)
   - Zero external API calls for reasoning or memory operations
   - Provider-agnostic: supports Ollama, Claude, etc. via unified interface

5. **Database-First Persistence**:
   - All memory via Mnemosyne (SQLite + LanceDB), 14 axes
   - No external SaaS memory backends

6. **Formal Verification Pipeline** (Axis 11):
   - 4-stage chain: AST analysis → QWED → SymPy → Z3 SAT solver
   - Triggered for logic-critical or mathematical changes
   - See `scripts/sovereign_audit.py`

7. **VRAM Budget** (Morpheus):
   - Total: 7.0 GB. OS reserve: 1.0 GB.
   - Never load two heavy models (>3 GB) concurrently
   - Every heavy model transition requires `Morpheus.flush()`
   - LocalRuntime uses dynamic `-ngl` for layer offloading

---

## 8. Quick Start

### Automated Installer
To bootstrap the entire environment (venv, dependencies, models, database migrations, and initial seeds), run:
```bash
python scripts/bootstrap.py
```
For options (e.g. skipping model downloads), run `python scripts/bootstrap.py --help`.

See [INSTALLATION.md](INSTALLATION.md) for full details on hardware, Ollama setup, and troubleshooting.

### Key Commands
```bash
# Run all tests
pytest tests/ -v

# Run smoke tests
pytest tests/ -m smoke -v

# Lint & format
ruff check .
ruff format .

# Type check (pyright only)
pyright src/

# Generate L0 auth token (required for write operations)
python scripts/create_l0_token.py

# Health check
python scripts/health_check_14_axes.py

# CLI interface
python scripts/hermes_cli.py

# Database migrations
alembic upgrade head
```

---

## 9. Project Topography

```text
D:\Hank\
  .antigravity/       Sovereign Knowledge Base (Constitution, rules, tools, audit)
  agent/              YAML agent definitions (sophia.yaml, clotho.yaml, lachesis.yaml)
                      Skills in agent/skills/
  alembic/            Database migrations (14-axis Mnemosyne schema)
  bin/                Binary executables (llama-cli, etc.)
  cognition/          Memory (Mnemosyne 14-axis), Sophia strategic layer
  dashboard/          Web UI Operator Console SPA frontend files (index.html, style.css, app.js)
  data/               SQLite + LanceDB stores (gitignored, seed on fresh setup)
  docs/               Auxiliary documentation
  logs/               Execution logs, watchdog events
  models/             Local GGUF models (gitignored)
  scratch/            Temporary workspace
  scripts/            Automation: health checks, token generation, CLI, VRAM flushing
  src/                Core modules (architrave, clotho, atropos, lachesis, ankyra, muscle, tools, utils)
  tests/              Test suite (14 categories, CI/CD integration, formal verification)
  .env.example        Environment configuration template
```

---

## 10. Testing & CI/CD

- **Test Suites**: 14 categories covering security, stability, and pipeline validation.
- **CI**: GitHub Actions (lint + pytest on Python 3.12, ubuntu-latest).
- **Framework**: Pytest with asyncio mode auto.
- **Environment**: `PYTHONPATH=.`, `LLM_BINARY_DIR=./bin`, `LLM_MODEL_DIR=./models`.

---

## 11. References

- [CLAUDE.md](CLAUDE.md) — Developer guide, architecture details, constraints.
- [INSTALLATION.md](INSTALLATION.md) — Installation and setup guide.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines and BA-01 rules.
- [CHANGELOG.md](CHANGELOG.md) — Project changelog (v1.2.1).
- [CONSTITUTION.md](.antigravity/CONSTITUTION.md) — Governance laws.
- [walkthroughs/main_walkthrough.md](.antigravity/walkthroughs/main_walkthrough.md) — Phase execution history.

---

## 12. Operator Dashboard

Phantom Logos provides an interactive, local-only Web UI Dashboard to monitor 14-axis memory, VRAM usage, system health, and real-time logs.

To launch it, run:
```bash
python scripts/dashboard.py
```
Open `http://127.0.0.1:8765` in your browser. See [DASHBOARD.md](docs/DASHBOARD.md) for endpoint specifications and guides.
