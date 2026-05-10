# Changelog

## Phase 11.19.9 - 2026-05-10
### Added
- **Model Registry SSOT**: Unified model resolution via `model_registry.py` with flagship MiMo-VL (5.7GB) integration.
- **Registry Helpers**: `get_embedding_model()`, `get_qwed_models()`, and `resolve_local_model()` for dynamic variant switching.

### Fixed
- **QWED Pipeline**: Resolved 404-producing hardcoded strings in `deigma.py` and `qwed_engine.py`.
- **Tool Bridge**: Synchronized `LOCAL_MODEL_MAP` with correct Ollama model identifiers to eliminate silent failures.
- **IDE Imports**: Fixed false-positive "Cannot find module" errors by refining `pyrightconfig.json` `extraPaths`.

### Changed
- **Embedding De-Hardcoding**: Replaced hardcoded `nomic-embed` strings with registry lookups across 5 core modules (`hermes_cli.py`, `sprint_contract.py`, `visual_store.py`, `theoria.py`, `retrieval.py`).
- **LocalRuntime Cleanup**: Updated vision flagship documentation and removed stale Qwen3-VL references.

## Phase 11.19.7 - 2026-05-10
### Changed
- **Document Synchronization**: Cross-reference compatibility audit across all `.antigravity/` documents.
- **14-Axis Hardening**: All stale "13-axis" references corrected to 14 across topography.md, CONTRIBUTING.md, AGENTS.md, opencode agent files.
- **Vision Flow Update**: Replaced Qwen3-VL + Gemma4 references with MiMo-VL-7B-RL as single flagship VLM across topography.md, AGENTS.md, .antigravity/README.md.
- **Model Reference Cleanup**: restoration.md Gemini Flash Thinking → Sovereign Gateway. opencode agents model fields updated.
- **Version Headers**: SECURITY.md, schema.sql, .antigravity/README.md version/phase headers updated to Phase 11.19.7.
- **Stale Path Fix**: schema.sql, CONTRIBUTING.md updated to reflect post-refactoring package paths.
- **GEMINI.md Sync**: Harmonized with IDENTITY.md (14-axis, Sovereign Gateway terminology).

## Phase 11.19.6 - 2026-05-09
### Changed
- **Gateway Hardening**: Circuit breaker (60s cooldown), local fallback timeout 30s→60s, MockResponse on failure.
- **CORE_MODELS Protection**: `sync_from_ollama()` + `keep_alive=-1` prevents model eviction.
- **Adaptive Draft**: krisis.py: skip refine_node if confidence > 0.9.

### Fixed
- **Embedding Pydantic Fix**: ReasoningState.error_message field.
- **TemporalStore Singleton**: Module-level `_initialized` flag, ~43K daily redundant SQL queries eliminated.
- **Watchdog Optimization**: Polling interval 2s→30s, mtime-based change detection (~90% CPU reduction).

## Phase 11.19.5 - 2026-05-09
### Changed
- **Modular Refactoring**: `ergon.py` → 12-file `ergon/` package. `tool_bridge.py` → 6-file `bridge/` package.
- **Gnosis Package**: `gnosis.py` → 16-file `gnosis/` package with stable/dynamic context split + JSON minification.
- **Verifier Package**: `sympy_verifier.py` → 6-file `verifiers/` package (SymPy, Z3, QWED, LLM).
- **Mapper Package**: `codebase_mapper.py` → 3-file `mapper/` package (ASTParser, GraphManager).
- **Schema Extraction**: `eidos.py` with 5 Pydantic models.

## Phase 11.19.1 - 2026-05-08
### Added
- **Temporal Validity**: event_key + supersede() + get_fact_at() for temporal graph queries.
- **Axis 14 Visual**: visual_store.py with Nomic text embedding, 50-entry LRU retention, 30-day TTL.
- **Sovereign Shield Docs**: snapshot_manager.py + file_watchdog.py integrated.
- **MODEL_BENCHMARKS**: 23 models with MMLU/HumanEval/MATH loaded in model_registry.py.

### Changed
- **tools.md Sync**: Full model inventory alignment with topography.md.
- **opencode.json**: Agents see tools.md and DEEPSEEK_CMD.md for context.

## Phase 11.18.10 - 2026-05-07
### Changed
- **AST Migration**: Codebase Mapper regex parser replaced with `ast.parse` for 100% import accuracy.
- **SQL LIKE Optimization**: `suggest_context()` uses `query_by_keywords()` with case-insensitive SQL `LIKE` + `limit(30)`.
- **Incremental Remap**: `remap_file()` updates single files + dependents. Deleted files auto-pruned.
- **Debounced Remap**: `mapper_bridge.py` with `asyncio.Task.cancel()` — 3 writes → 1 remap.
- **Spatial Injection**: `anchor_inject_node` injects spatial context directly into state.
- **Thread Safety**: `threading.Lock` + `asyncio.Lock` separation.

### Added
- **Circular Dependency Detection**: DFS coloring algorithm.
- **GraphState**: `spatial_context` and `spatial_dirty` fields.

## Phase 11.18.9 - 2026-05-07
### Changed
- **Two-Stage Reranking**: Nomic (100 candidates) → Jina (top 5). 5x pool at +0.1s.
- **MS-MARCO Bypass**: Ollama HTTP bottleneck eliminated.

## Phase 11.18.8 - 2026-05-07
### Added
- **OutputGuard Pipeline**: verify_node + refine_node. BA-01 exemption.
- **l0_approved Gate**: Hard stop + reliability kill-switch.
- **Z3 Verification**: `verify_logic()` in verify_node.
- **XML+Few-Shot Prompts**: Structured templates in draft_node.

### Changed
- **Thinking Param Fix**: `thinking=True` → `thinking_config` conversion.
- **Model Swap**: granite→fallback, qwen2-5-coder-7b→primary.

### Fixed
- **Root Cause** (0.47 Sophia quality): Thinking param ValidationError → silent Ollama fallback spiral.

## Phase 11.18.7 - 2026-05-07
### Changed
- **Global Rebrand**: "Phantom Opus" → "Phantom Logos" across 14 files.
- **13-Axis Sync**: All "12-axis" references corrected.

### Fixed
- **Broken Links**: AGENTS.md cross-references restored.

## Phase 11.18.6 - 2026-05-07
### Added
- **Dynamic Agent Selection**: Task type routes to Sophia/Clotho/Lachesis.
- **5 New SOTA Skills**: MCP Discovery, Mnemosyne Query, VRAM Profiler, Deadlock Resolver, Error Recovery.

### Changed
- **Hallucination Spiral Fix**: 3 failed audits → deadlock_resolver.

## Phase 11.19 - 2026-05-07
### Added
- **10 Phantom SKILL.md Files**: Created missing skill definitions.
- **SOTA Power Skills**: 5 advanced agent capabilities.

### Changed
- **Parser Upgrade**: YAML frontmatter parser → `yaml.safe_load()`.
- **AGENTS.md Merge**: Root + .antigravity/AGENTS.md consolidated.

## Phase 11.18.5 - 2026-05-07
### Changed
- **Transport Hardening**: `trust_env=False` on httpx.
- **Ollama Singleton**: Shared `AsyncClient` across 6 modules.
- **CPU Pool**: `max_workers=4` to prevent saturation.
- **Event Loop Offloading**: 9 `asyncio.to_thread` calls.

## Phantom Logos v1.0.0 - 2026-05-07
### Sovereign Rebirth
- **Project Rebranding**: Phantom Opus → **Phantom Logos v1.0.0**.
- **13-Axis Foundation**: Sealed 13-axis Mnemosyne baseline.
- **Absolute Agnosticism**: All routing via Sovereign Strategic Gateway.
- **Unified Client**: GatewayArchitrave for all reasoning and tools.

## Phase 11.18.4 - 2026-05-07
### Added
- **13-Axis Mnemosyne**: Standardized MNEMOSYNE AXIS N tagging.
- **Sovereign Citation**: Mandatory `[SRC:axis_N]` for all reasoning.
- **Sophia Write Path**: Auto-logging to Axis 1 (Episodic).
- **Spatial Expansion**: Dependency-aware context expansion.

### Changed
- **Absolute Agnosticism**: Purged "Gemini" cosmetic references.
- **Security**: `GATEWAY_API_KEY` aliasing with backward compatibility.

## Phase 11.18.3 - 2026-05-07
### Added
- **Sovereign Provider**: Custom Pydantic AI provider for local-hybrid routing.
- **Unified Client**: GatewayArchitrave as single truth source.

### Removed
- **Cloud Dependency**: Eliminated `gateway.pydantic.dev` proxy calls.

## Phase 11.18.2 - 2026-05-07
### Added
- **Async Persistence**: AsyncSqliteSaver checkpointer.
- **ActivityMonitor**: Prevent Morpheus from killing active operations.
- **Timeout Layer**: Global 120s, Tool 30s, Cloud 90s.

### Changed
- **Event Loop Hardening**: All sync handlers → `asyncio.to_thread`.
- **Gnosis Refactor**: `get_dynamic_context` fully async.
- **Cognitive Isolation**: CPU/IO ops thread-offloaded.

### Fixed
- **Event Loop Blocking**: Freezes from synchronous Ollama/LanceDB calls.
- **VRAMSweeper Reliability**: Race conditions in heal_ollama.

## Phase 11.18.1 - 2026-05-07
### Added
- **Agnostic Gateway**: AgnosticArchitrave with custom base_url routing.
- **Capability Mapping**: Agent roles decoupled from model names.
- **SDK Masking**: models/ prefix for GenAI SDK compatibility.

### Changed
- **Model Purge**: Removed commercial model aliases from registry.
- **Sophia Integration**: Cloud Gateway provider instead of direct Gemini.
- **Thinking Preservation**: CoT metadata preserved through gateway.

## Phase 11.13 - 2026-05-05
### Added
- **Knowledge Base**: Created `.antigravity/` directory structure (topography.md, tools.md).
- **Governance Docs**: CONSTITUTION.md, AGENTS.md, SECURITY.md, CONTRIBUTING.md.
- **LICENSE**: MIT.

### Changed
- **Migration**: Moved history files to `audit/` and `walkthroughs/`.
- **Persistence**: Persisted TASKS.md from memory artifact to disk.
- **Documentation**: Repaired links across all `.md` files, rewrote README.md.
- **Optimization**: Updated `.gitignore` for GitHub standards.

---

> **Note:** Entries below this line are retrospective reconstructions compiled from memory artifacts and system traces.

## [1.0.0] - 2026-05-03
### Initial Release
- Baseline Phase 10 implementation of the Phantom Opus Agentic OS.
- 12-axis memory architecture (Initial Blueprint).
- RuFlow 3-Tier Hierarchical Orchestration.
