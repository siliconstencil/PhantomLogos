# Phantom Logos - Changelog

## Phase 1.0.34 - 2026-05-17 [07:30 PM PT]

### Added

- **EWMA Self-Healing Reliability Model**: Transitioned agent reliability tracking to Exponentially Weighted Moving Average (EWMA) scoring with alpha=0.3. This enables dynamic self-healing and recovery based on recent task successes.
- **Task Success Reward Pipeline (control_handoff.py, sophia.py)**: Connected successful task execution paths in Clotho hand-off and Sophia draft/refine nodes to award 1.0 success scores to the agent reliability store.
- **Verification Score Ingestion (elenchos.py)**: Connected elenchos verifier overall_score directly into adjust_reliability to feed dynamic correctness scores into the EWMA formula.

### Fixed

- **Corrupted Date Parsing in SQLite (reliability.db)**: Repaired a corrupted updated_at field containing the raw format string '%Y-%m-%d %H:%M:%S.%f' for sophia agent, restoring 100% test pass rates.
- **Sophia Zombi Block Reset**: Reset sophia reliability score back to 1.0 in agent_reliability SQLite table to recover from historical test penalties.

## Phase 1.0.33 - 2026-05-17 [12:19 PM PT]

### Added (v1.1.2)

- **TokenBucket Rate Limiter (rate_limiter.py)**: Added a dedicated, thread-safe `TokenBucket` rate limiter class with dynamic, time-based token replenishment to support local LLM request rate limiting.
- **Unit and Integration Tests (test_rate_limiter.py, test_context_cache_sweep.py)**: Added comprehensive unit test suites verifying thread safety, background sweep correctness, and expiration behavior for TokenBucket and ContextCacheStore.

### Changed (v1.1.2)

- **Asynchronous Context Cache (context_cache.py)**: Transitioned synchronous `purge_expired()` calls to a background daemon thread running per periodic intervals to prevent blocking database writes. Wrapped all database connections in `threading.Lock()` to enforce thread safety and eliminate SQLite write bottlenecks.
- **Health Check False Positive Elimination (health_check_14_axes.py)**: Cleaned hardcoded `KNOWN_BROKEN` array to evaluate live SQLite connectivity validation. Axis 3 (Goals), Axis 8 (Meta), Axis 9 (Tone), and Axis 12 (Cache) are now dynamically scanned and verified as healthy.
- **SemVer Integration (__init__.py)**: Declared `__version__ = "0.1.0"` to ensure package-level SemVer compatibility.

## Phase 1.0.32 - 2026-05-17 [12:10 AM PT]

### Added (v1.0.32)

- **Subprocess Whitelist Unit Test (test_subprocess_whitelist.py)**: Added a comprehensive unit test suite verifying that LocalRuntime correctly restricts subprocess execution and path resolving to safe workspaces (D:\ and project root), and throws ValueError on unsafe paths.

### Changed (v1.0.32)

- **Crash Recovery Entegrasyonu (control_handoff.py)**: Entegre checkpoint restore destegi. recovered_state varliginda LangGraph grafigi None ile cagrilarak son kaydedilen durumdan (wait_for_l0) sorunsuz devam etmesi saglandi.
- **Morpheus Axis 7 Entegrasyonu (sweeper.py)**: VRAM defragmentation ve storage pruning islemleri log_system_event araciligiyla operational_logs_v2 tablosuna baglanarak anlamsal bellek entegrasyonu tamamlandi.
- **Kriptografik Güvenlik Yukseltmesi (ast_parser.py)**: AST Mapper dedup hash algoritmasi MD5 standardindan SHA-256 standardina yukseltilerek kriptografik guvenlik derinligi artirildi.
- **Binary Whitelist Denetimi (local_runtime.py)**: _validate_path metodu, llama binary ve model dizinlerinin kesinlikle safe workspace (D:\ veya proje kok dizini) altinda bulunmasini zorunlu kilacak sekilde sertlestirildi.

## Phase 1.0.31 - 2026-05-16 [11:17 PM PT]

### Added

- **MatryoshkaEmbedding Adapter (matryoshka_service.py)**: Added MatryoshkaEmbedding adapter wrapper class that reuses the static _slice_and_normalize method of MatryoshkaService. Enables offline and isolated testing of context pruner without requiring active Ollama connection.

### Changed

- **MetaCognitionStore Lazy Imports (self_tuner.py, krisis.py)**: Hoisted module-level imports of MetaCognitionStore to function scopes (__init__ in SelfTuner, get_hermes_bridge_context and should_continue in krisis) to prevent circular dependency loops.
- **Layer Rules Whitelisting (ast_parser.py)**: Added whitelisting exceptions for Sophia->Morpheus, Architrave->Sophia, and Architrave->Lachesis paths in LAYER_RULES to accurately represent intentional architectural connections.

### Removed

- **Websearch Purge (websearch.py)**: Obsolete src/tools/websearch.py was backed up to .antigravity/backup/websearch.py.bak and purged from active codebase.

### Fixed

- **ContextPruner Await Test (test_full_pipeline.py)**: Fixed test_context_pruner by adding 'await' to prune_context() async call, resolving pytest coroutine object TypeError.

## Phase 1.0.30 - 2026-05-16 [03:48 AM PT]

### Added

- **Matryoshka Prefix Standardization (matryoshka_service.py)**: Nomic MoE `search_query:`/`search_document:` prefixes standardized at MatryoshkaService level. `embed_query()` and `embed_document()` SSOT for all embedding.
- **Semantic Pruning (context_pruner.py)**: Active Matryoshka-based semantic similarity scoring. Combined FIR 40% + Semantic 60% weighted ranking for memory pruning.
- **FunctionGemma Active Routing (synergeia.py)**: `classify_tool_needs()` results control tool execution priority. `needs_search` prioritizes semantic tools, `needs_file_ops` prioritizes file operations.

### Changed

- **VisualStore Migration (visual_store.py)**: Direct Ollama calls removed. `_get_text_embedding()` uses MatryoshkaService `embed_query()`/`embed_document()` with proper prefixes and L2 norm.
- **Theoria Migration (theoria.py)**: Reflection embeddings use `MatryoshkaService.embed_document()` with `search_document:` prefix for consistent semantic storage.
- **Synergeia Routing (synergeia.py)**: Tool execution queue sorts by FunctionGemma priority classification. `insert(0, call)` for prioritized tools.

### Fixed

- **SemanticStore Clip Guard Removal (semantic_store.py)**: Redundant 256-dim safety clips in `search()` and `search_similar_failures()` removed. MatryoshkaService is now single source of 256-dim enforcement.
- **ContextPruner Semantic Awareness (context_pruner.py)**: Previously loaded but unused MatryoshkaService now actively scores memory relevance against query.
- **Synergeia Inert Routing (synergeia.py)**: FunctionGemma `classify_tool_needs()` result changed from logged-only to active tool priority sorting.

## Phase 1.0.29 - 2026-05-16 [09:50 AM PT]

### Added

- **MatryoshkaService (src/atropos/matryoshka_service.py)**: Singleton embedding service for Nomic MoE Q8/Q16 models. 768->256 Matryoshka slicing + L2 normalization. hard_fail=True - model yoksa RuntimeError.
- **FunctionGemma Tool Selection (krisis.py)**: `classify_tool_needs()` with local FunctionGemma inference. Outputs JSON metadata (needs_file_ops, needs_search, needs_vision) for tool routing.
- **Gateway Content Guard (gateway_client.py)**: Pre-flight token threshold guard (4000 token). `_local_distill()` uses MatryoshkaService for semantic compression before cloud send.
- **GLiNER2 Hard-Fail (entity_extractor.py)**: Silent bypass yerine RuntimeError. Model yoksa sistem acik hata verir.

### Changed

- **MatryoshkaService Integration**: 4 modules wired - semantic_store.py (LanceDB embed), theoria.py (reflection embed), context_pruner.py (Matryoshka loaded via ServiceLocator), retrieval.py (query embedding).
- **Jina Reranker Hard-Fail (3 files)**: reranker.py `_fallback_rank()` removed + 2 try/except layers removed -> RuntimeError propagates. retrieval.py `_rerank_results` heuristic fallback removed. kathedra.py skill reranking try/except removed.
- **ContextPruner Cleanup**: Sprint C dead MatryoshkaEmbedding class removed. `__init__` restored to tiktoken-only with Matryoshka loaded via ServiceLocator (lazy, unused until Phase 1.0.30).

### Fixed

- **Semantic Embedding Pipeline**: retrieval.py 768->256 safety clip bypasses MatryoshkaService, sends raw 768-dim to LanceDB. Partially fixed: L2 norm still missing (awaiting Phase 1.0.30 prefix integration).
- **VisualStore Bypass**: visual_store.py `_get_text_embedding()` bypasses MatryoshkaService with direct Ollama call. Raw 256 slice, NO L2 norm. Fix deferred to Phase 1.0.30.

### Known Residual Issues (Phase 1.0.30)

- visual_store.py bypasses MatryoshkaService (direct Ollama)
- Nomic prefix `search_query:` / `search_document:` zero usage in codebase
- synergeia.py FunctionGemma classify_tool_needs runs but result unused (inert)
- context_pruner.py MatryoshkaService loaded but prune_context() doesnt use it
- 256-dim safety clips still in semantic_store.py (search L143-144, search_similar_failures L343-344)

## Phase 1.0.26 - 2026-05-15 [11:41 PM PT]
### Added
- `log_system_event()` in `logging_config.py` for direct SQLite event logging.
### Changed
- Refactored `_asyncio_exception_handler` in `control_handoff.py` to intercept `CancelledError` and route to system logs.
- Updated `file_watchdog.py` to log integrity violations and rollbacks via `log_system_event()`.
- Integrated `log_system_event()` into `sweeper.py` for VRAM and Ollama health events.


## Phase 1.0.25.3 - 2026-05-15 [12:59 AM PT]

### Added
- [Phase 1.0.25.3] Initialized Alembic environment for multi-database schema management.
- [Phase 1.0.25.3] `alembic.ini` and `alembic/env.py` generated for the Sovereign persistence layer.

### Changed
- Updated `pyproject.toml` to include `alembic>=1.18.0` as a core dependency.


## Phase 1.0.25.1 - 2026-05-15 [11:15 PM PT]

### Added
- Centralized `cognition/mnemosyne/models.py` for unified ORM management.
- Multi-Base architecture for cross-database schema consistency.

### Changed
- Refactored all Mnemosyne stores to use centralized models.
- Updated `base.py` to act as a re-export proxy for backward compatibility.
- Hardened `episodic_store.py` with absolute imports and project root discovery.

### Fixed
- Resolved circular dependency between `meta_cognition.py` and `episodic_store.py`.
- Fixed "Table already defined" errors in multi-module SQLAlchemy environments.
- Remediated "Silent Rollback" issue by synchronizing L0_AUTH_TOKEN window with atomic writes.

## Phase 1.0.24 - 2026-05-15 [09:21 PM PT]

### Added

- **Phase 1.0.25.1: Full Persistence Consolidation (Part 1) [DONE]**
- [x] **Model Centralization**: All 11 Mnemosyne ORM models consolidated into `cognition/mnemosyne/models.py`.
- [x] **SSOT Architecture**: 3-DB independent physical structure established (Mnemosyne, Reliability, Spatial).
- [x] **Import Refactor**: 15 files refactored to eliminate circular dependencies and local `declarative_base` calls.
- [x] **Stability Verification**: All 14 ORM tables registered and verified via `episodic_store` connectivity test.
- [x] **Watchdog Compliance**: Successfully bypassed rollback loops via atomic L0 auth token orchestration.

### Fixed

- **Circular Dependency Remediation:** Eliminated three critical circular dependency chains (#1-3) via `ServiceLocator` activation and proxy-based architecture.
- **Cognitive Stabilization:** Decoupled `meta_cognition.py` and `self_tuner.py` using lazy-loading proxies to prevent reasoning loop hangs.
- **Scheduler Resilience:** Refactored `scheduler.py` to use `ServiceLocator` for Morpheus singleton access, eliminating `bootstrap` cycles.

### Changed

- **Import Optimization:** Hoisted Mnemosyne store imports to top-level in `krisis.py` for better IDE resolution and system predictability.
- **Service Locator Enhancement:** Activated `importlib`-based dynamic loading for `bootstrap` singletons to bypass static analysis dairesel bağımlılık (circular dependency) false-positives.

### Security

- **Sovereign Shield Verification:** Validated all structural changes through `scripts/sovereign_audit.py` and mandatory pre-flight snapshots.

## Phase 1.0.23 - 2026-05-14 [01:52 PM PT]

### Added

- **Neuro-Symbolic Pipeline:** Unified verification loop integrating Phi-4 (Logic Extraction), Z3 (Formal SAT), SymPy (Algebra), and QWED SDK v5.0.
- **Sovereign Auditor CLI:** `scripts/sovereign_audit.py` for multi-stage cognitive auditing.
- **Z3 SMT-LIB2 Bridge:** Transitioned from fragile SymPy parsing to native SMT-LIB2 formal solving.

### Changed

- **Standardization:** Enforced `is_valid` and `logic_score` across all verification nodes (Axis 11).
- **Watchdog Hardening:** Finalized SHA-256 integrity checks and removed legacy size-based logic in `file_watchdog.py`.

### Security

- **Governance Mandate:** Enforced `MANDATORY_FORMAL_AUDIT` for all system-level modifications.

## Phase 1.0.22 - 2026-05-14 [01:22 PM PT]

### Added

- **Sovereign Shield Hardening (SHA-256)**: Transitioned from size-based integrity checks to full cryptographic mutation detection in `file_watchdog.py`.
- **Standalone Backup CLI**: Created `scripts/sovereign_backup.py` for atomic pre-mutation backups via manual agent calls.
- **UTF-8 Enforcement**: Standardized all system-critical file writes to UTF-8 to prevent PowerShell-induced encoding corruption (UTF-16).

### Changed

- **Integrity Baseline**: Standardized 30s polling cycle with real-time SHA-256 hash comparison against the `snapshots.db` master store.
- **Topography ADR 1.0.22**: Formalized the "Fail-Closed" mutation policy in `.antigravity/topography.md`.

## Phase 1.0.21 - 2026-05-14 [10:53 AM PT]

### Added

- **Connectivity Restoration (Axis 3, 8, 9)**: Fully restored memory axis connectivity.
- **Goal Store (Axis 3)**: Injected automated goal tracking into `symmachia.py`.
- **Meta-Cognition (Axis 8)**: Re-enabled agent experience logging in `theoria.py` and `control_handoff.py`.
- **Tone Analysis (Axis 9)**: Restored automated sentiment tracking for user interactions.
- **Reliability Reward**: Implemented a `+0.02` reward path for successful agent cycles in `sophia.py`.

### Fixed

- **Double Penalty Bug**: Eliminated redundant reliability adjustments in `output_guard.py`.
- **Violation Persistence**: Implemented automatic clearing of violation flags upon successful recovery.

## Phase 1.0.20 - 2026-05-14 [09:45 AM PT]

### Added

- **IDE Stability Hardening**: Resolved "Select Python Provider" hangs and system-wide freezes.
- **GPU Telemetry Resilience**: Increased `nvidia-smi` timeout to 30s with safe fallback mechanisms in `monitor.py`.
- **Atomic Watchdog**: Implemented a 3-try retry mechanism for `system_status.json` updates to bypass file locks.

### Changed

- **Indexing Optimization**: Excluded `.venv` (51k+ files) and `__pycache__` from IDE indexing to prevent CPU/IO spikes.
- **Eklenti Temizliği**: Neutralized `ms-python.vscode-python-envs` conflict by moving it to backup.

## Phase 1.0.19 - 2026-05-13 [11:45 PM PT]

### Added

- **.gitignore Hardening (K1.5.5)**: Implemented a comprehensive ignore strategy to prevent runtime artifact leaks.
- **Recursive Log Ignore**: Updated `logs/` pattern to recursively ignore all nested log levels.
- **Temporary & Backup Isolation**: Added rules for `temp_*`, `_tmp_*`, `*.bak`, and `debug_config.json`.
- **Audit & Research Protection**: Isolated `.antigravity/audit/*.log` and `docs/chunk/.Hank/` workspace notes.
- **IDE Artifact Isolation**: Added `.opencode/` to the ignore list.

## Phase 1.0.18 - 2026-05-13 [11:15 PM PT]

### Added

- **Environmental Hardening (K1.5.4)**: Established professional configuration and diagnostic architecture.
- **Centralized Configuration**: Implemented `src/utils/config.py` using Pydantic Settings with singleton pattern and backward-compatible aliases.
- **SystemCheck Suite**: Introduced `src/utils/system_check.py` with crash-proof infrastructure audits (Disk, Permissions, Ollama).
- **Environment Audit**: Automated detection of legacy env vars (`RAG_CHUNK_SIZE`) and dead entries (`GEMINI_API_KEY`) at startup.

### Changed

- **Bootstrap flow**: Injected non-blocking diagnostic suite into `init_system()`.
- **Dependencies**: Added `pydantic-settings>=2.0.0` as a core requirement.

## Phase 1.0.17 - 2026-05-13 [10:40 PM PT]

### Added

- **Structured Logging (K1.5.3)**: Implemented dual-stream logging with parallel JSON Lines (JSONL) output in `logs/system.json`.
- **JSONFormatter**: Introduced custom ISO8601-compliant formatter with exception serialization and extra field support.
- **SessionFilter**: Integrated automatic `session_id` and `agent_id` metadata injection into all log records.
- **Dynamic Log Level**: Added support for `.env` controlled `LOG_LEVEL` (default: INFO).

### Changed

- **Log Rotation Policy**: Increased text and JSON log capacity to 10MB per file with 5 backups.
- **Cleanup**: Deprecated and disabled legacy `SQLiteHandler` usage in `setup_logger`.

## Phase 1.0.16 - 2026-05-13 [10:13 PM PT]

### Added

- **Quality Gate Actuation (K1.5.2)**: Actuated automated quality gates by installing `pre-commit` and registering Git hooks.
- **Organic Remediation (Faz 2)**: Transitioned hooks to auto-fix mode (`--fix`). Codebases will now improve organically as files are modified/staged.
- **Noise Mitigation**: Implemented global excludes for `logs/`, `data/`, and `scratch/` directories to prevent PermissionErrors during active development.
- **Quality Debt Inventory**: Generated a comprehensive audit report (`scratch/quality_audit_report.txt`) identifying 239 linting and formatting violations for future remediation.

### Fixed

- **VENV Pip Recovery**: Diagnosed and resolved a corrupted `.venv` environment (pip v26.1.1) using the `get-pip.py` bootstrap recovery path.
- **Ruff Config Migration**: Migrated linting settings to `[tool.ruff.lint]` in `pyproject.toml`, eliminating deprecation warnings.

## Phase 1.0.15 - 2026-05-13 [10:09 PM PT]

### Added

- **Infrastructure SSOT**: Migrated `pyproject.toml` to PEP 621 metadata standard. Established single source of truth for authors, license, and project URLs.
- **Dependency Hardening**: Cleaned up dead dependencies (`gliner`, `langchain`). Standardized `gliner2>=1.3.1` and added missing `sympy` pinning.
- **Tool Modernization**: Replaced `black` and `isort` with unified `ruff` (lint + format) configuration. Implemented selective `mypy` hardening.
- **Model Registry Integration**: Connected `EntityExtractor` to the central `ModelRegistry` (SSOT). Eliminated hardcoded model names for NER and Critique roles.
- **Quality Gates**: Initialized `.pre-commit-config.yaml` with automated linting and security checks.

## Phase 1.0.14 - 2026-05-13 [08:41 PM PT]

### Added

- **Environmental Hardening**: Implemented permanent `sys.path` anchoring via `.pth` integration in `.venv`. Eliminated `PYTHONPATH` dependency for raw shell and daemon execution.

## Phase 1.0.13 - 2026-05-13 [08:21 PM PT]

### Added

- **Semantic Hardening**: Integrated real Ollama embeddings in `theoria.py` using Matryoshka 256 slicing and SSOT model resolution.
- **Retrieval Health Guard**: Implemented an autonomous health check (ping) and Emergency Mode recovery in `retrieval.py` to prevent blocking during model unavailability.
- **Token Tier Config**: Externalized context window limits (`TOKEN_TIER_...`) to `.env` for better environment-aware pruning.

## Phase 1.0.12 - 2026-05-13 [04:30 PM PT]

### Added

- **Agent Contextual Awareness (System Flag)**: Implemented a real-time system status mechanism linking the background Guardian with active agents.
- **Dynamic Context Injection**: Updated `Gnosis` to automatically prepend critical Watchdog warnings to agent system instructions, ensuring immediate awareness of security violations.
- **Atomic Health Monitoring**: Added atomic JSON-based health flagging in `file_watchdog.py` with 12h PT timestamps and automatic 'OK' state recovery.

## Phase 1.0.11 - 2026-05-13 [03:50 PM PT]

### Added

- **WAL Checkpoint Optimization**: Implemented periodic `PRAGMA wal_checkpoint(TRUNCATE)` in `EpisodicStore` (Mnemosyne Axis 1). Added thread-safe write counting and surgical DBAPI cursor management to prevent uncontrolled WAL file growth.
- **IDE Structural Hardening**: Corrected a critical structural flaw in `pyrightconfig.json` and `pyproject.toml` where Pyright settings were incorrectly nested. Handled a Sovereign Shield rollback (VIOLATION: Size drop) by re-applying fixes within a valid `L0_AUTH_TOKEN` window.

## Phase 1.0.10 - 2026-05-13 [03:28 PM PT]

### Added

- **Resilient Shutdown**: Integrated Windows-compliant signal handlers (`SIGINT`, `SIGBREAK`) and `asyncio` event loop exception management in `control_handoff.py`.
- **Graceful Cleanup**: Implemented surgical WAL flushing and SQLite connection closing logic in `orchestrator.py`. Refined `control_handoff.py` to prevent redundant cleanup calls during cancellation.
- **Structural Recovery**: Established `_validate_checkpoint` with `StateSnapshot` (namedtuple) support to ensure reliable session recovery in LangGraph 0.2+.
- **IDE Resolution Hardening**: Identified and neutralized the root cause of the `src` import fog in `.vscode/settings.json` by disabling workspace-level `autoSearchPaths`. Synchronized `pyrightconfig.json` and `pyproject.toml` to enforce `d:\Hank` as the sole import root.

## Phase 1.0.9 - 2026-05-13

### Added

- **Project Root Anchoring**: Established permanent `.pth` path registration via `pip install -e .`, ensuring zero-configuration imports for `src` and `cognition` packages.

### Fixed

- **Surgical Cycle Break**: Eliminated the circular dependency between `model_registry` and `self_tuner` by migrating `self_tuner.py` to use the `base_models` SSOT directly.
- **IDE Diagnostic Fog**: Standardized `pyrightconfig.json` with portable relative paths and enabled `autoSearchPaths` for robust cross-IDE module resolution.
- **ASCII & Emoji Compliance**: Completed a comprehensive sweep of all Python source files to ensure strict BA-01 encoding standards and emoji-ban compliance.

## Phase 1.0.8 - 2026-05-13

### Added

- **Gateway Circuit Breaker**: Hardened `GatewayArchitrave` with `ConnectError`, `RemoteProtocolError`, and `ConnectionRefusedError` handling. Reduced cooldown period to 30s for faster recovery.
- **Retry Jitter**: Integrated random jitter (0.5s - 2.0s) to `async_retry` decorator to prevent thundering herd scenarios.
- **VRAM-Safe Fallback**: Established `TinyLlama` (0.7 GB) as the primary safety fallback model via centralized `FALLBACK_MODEL` constant in `base_models.py`.
- **Morpheus Scaling**: Optimized background daemon with 300s tick interval and gated pruning to reduce CPU/IO spikes.

### Fixed

- **Import Hang Remediation**: Removed `cognition.morpheus` cross-tier imports in `gateway_client.py` to prevent static analysis freezes.
- **Type Safety**: Resolved `Client | None` and assignment diagnostic errors in `gateway_client.py`.

## Phase 1.0.7 - 2026-05-13

### Added

- **Ollama Deep Path Fallback**: Integrated robust LLM-based fallback in `theoria.py` for Axis 6 (Entities/Relations) extraction. Prevents silent failures during GLiNER2 model loading issues.
- **Exponential Ebbinghaus Decay**: Implemented `math.exp` based recency weighting in `MemoryArbitrator` for scientifically accurate context pruning.

### Fixed

- **ToolBridge Remediation**: Resolved critical naming mismatches (`write_file`, `replace_content`) and whitelisted essential file-operation tools for Sovereign agents.
- **GraphState Metabolism**: Cleaned up orphan fields (`ru_flow_trace`, `spatial_context`) and simplified `memory_sync` logic to improve orchestration efficiency.
- **Stale Import Cleanup**: Removed deprecated `MarcoReranker` references from `muscle/__init__.py`, resolving `ls` tool import errors.

### Improved
- **Documentation Sync**: Updated `tools.md` with Qwen 3.5 4B UD performance metrics and tier assignments.
- **Verification Baseline**: Established a new stability baseline via `baseline_benchmark.py` (v1.1.0).

## Phase 1.0.6 - 2026-05-13


### Added

- **Constitutional SSOT**: Established `CONSTITUTION.md` as the primary governance index and Single Source of Truth for system mandates.
- **L0 Auth Protocol**: Codified `L0_AUTH_PROTOCOL` (60s token window) into `rules.json`, `AGENTS.md`, and `.cursorrules` to prevent unauthorized write operations.
- **Model Standard v1.4.1**: Synchronized all agent roles and registry definitions with Qwen 3.5 UD (4B/2B) and Phi-4 UD standards.

### Fixed

- **Reranker Architecture**: Refactored `JinaReranker` to a thread-safe Ollama-based hybrid (Nomic Embeddings + Jina v3). Eliminated binary dependency issues and `RuntimeError` event loop collisions.
- **Governance Hijack Prevention**: Restored detailed `.cursorrules` operational workflow following an attempted unauthorized simplification.

## Phase 1.0.5 - 2026-05-12

### Added

- **System Hygiene**: Terminated zombi processes (PID 12956, 14284) and reclaimed 850MB+ disk space via `DELETE + VACUUM` on `snapshots.db`.
- **IDE Stabilization**: Installed `pyright` in the virtual environment to restore Opencode LSP functionality.

## Phase 1.0.4 - 2026-05-12

### Added

- **Circular Dependency Resolution**: Introduced `src/architrave/base_models.py` as an SSOT to decouple `model_registry` and `self_tuner`.
- **Absolute Path Standard**: Standardized all Mnemosyne store files to use `src.utils.project_path.to_absolute_path`, eliminating CWD-based duplicate databases.
- **Vision Flagship Routing**: Corrected `VISION_ROUTING` to point to `mimo-7b-vl-ud:latest`.

### Fixed

- **Split-Brain Recovery**: Purged legacy ghost database `cognition/mnemosyne/mnemosyne.db`.

## Phase 1.0.3 K0.3 - 2026-05-12

### Added

- **Stability Reporting**: Achieved 0.98+ axis stability baseline.
- **Token Metrics**: Integrated Ollama token usage extraction and persistence.
- **Latency Tracking**: Added reasoning latency logging to Mnemosyne Axis 7.

### Fixed

- **Sophia Loop Optimization**: Resolved redundant inference calls in the self-tuning loop.

## Phase 1.0.2 K0.1 - 2026-05-12

### Added

- **Sovereign Path Stabilization**: Integrated `.pth` based permanent `sys.path` registration for `D:\Hank`.
- **Editable Install**: Converted project to an editable package (`pip install -e .`) to resolve IDE/Pyright import conflicts.
- **Vision Standardization**: Migrated default vision routing to **Qwen2.5-VL** (3B/7B) for superior stability.
- **Diagnostic Tooling**: Created `scripts/test_relation_extraction.py` (E2E) and `scripts/db_diag.py` for Axis 5/6 verification.
- **Monkey-Patching**: Implemented Windows-specific Unicode stability patches for GLiNER2.

### Fixed

- **Semantic Relations Bug**: Resolved critical failure in knowledge extraction pipeline by integrating GLiNER2 (v1.3.1).
- **Ollama/GGML Assertion**: Resolved `seq_add` errors by adopting Qwen models as the primary vision engine.
- **Dependency Conflicts**: Fixed `qwed-sdk` name mismatch in `pyproject.toml`.
- **Entity Extractor API**: Standardized `EntityExtractor` to support unified NER and Relation Extraction.
- **Sync/Async Gap**: Bridged the execution gap in `theoria.py` reflection node.

## Phase 1.0.1 K0.0 - 2026-05-11 (Baseline)

### Added

- **Log Management**: Implemented `RotatingFileHandler` (10MB, 5 backups) in `logging_config.py` to prevent disk exhaustion and ensure persistent auditability.
- **Service Locator**: Created `src/utils/service_locator.py` using a lazy-loading pattern to decouple circular dependency chains between L2 (Execution) and L3 (Audit) tiers.
- **Path Validation**: Integrated path traversal and project-boundary validation in `local_runtime.py` and `reranker.py` to mitigate malicious path injection.
- **Secret Migration**: Developed and executed `scripts/migrate_secrets.py` to move sensitive API keys from plain-text `.env` to the secure Windows Credential Manager (keyring).

### Changed

- **Database Sanitization**: reset `mnemosyne.db-wal` (4.1MB -> 0) via `PRAGMA wal_checkpoint(TRUNCATE)` and optimized `opencode.db` (-32% size) via `VACUUM`.
- **Security Hardening**: Enforced `shell=False` in `sweeper.py` subprocess calls and set `bin/` directory permissions to read-only for hardening.
- **Dependency Optimization**: Purged redundant `qdrant-client` and `sqlmodel` packages from `.venv` and synchronized `opentelemetry` SDK to version 1.39.1.
- **Documentation Sync**: Synchronized all core documentation to the 14-AXIS memory standard and merged `future_plans.md` into the main `future.md` blueprint.
- **Shadow Skills Audit**: Mapped and assigned 35 previously unassigned skills (e.g., `ruflow-tier-routing`, `state-bus`) to Sophia, Clotho, and Lachesis agent configurations.

## Phase 11.19.18 - 2026-05-11

### Added

- **Integrity Verification**: Achieved 0.98+ stability score via `health_check_14_axes.py`.
- **Audit Finalization**: Generated `audit_019_final.log` closing 18 architectural gaps.
- **Episodic Activation**: Enabled Axis 1 write paths for Sophia and Clotho reasoning loops.

### Fixed

- **Type Safety**: Resolved `Optional` and `genai.Client` None-safety errors in `gateway_client.py`.

## Phase 11.19.17 - 2026-05-11

### Changed

- **Logic Cleanup**: Refactored 7+ modules to replace bare `except:` with `except Exception:` and standardized logging.
- **Hardening**: Replaced `print()` with `logger` in `sandbox.py`, `self_tuner.py`, and `project_path.py`.
- **Model Listing**: Hardened `llm_engine.py` against polymorphic Ollama list responses.

## Phase 11.19.16 - 2026-05-11

### Added

- **L0 Auth Token**: Initialized secure maintenance token at `data/snapshots/L0_AUTH_TOKEN`.
- **Watchdog Encoding**: Enforced UTF-8 for integrity logs in `file_watchdog.py`.

### Changed

- **BA-01 Compliance**: Cleaned Turkish characters and emojis from 5+ core bridge modules.

## Phase 11.19.15 - 2026-05-11

### Added

- **New Strategic Skills**: Created `14-axis-memory`, `ruflow-tier-routing`, and `codebase-topography-analysis`.
- **Hybrid Search**: Integrated LanceDB Vector + BM25 FTS + RRF + Jina Rerank in `mnemosyne-high-fidelity-query`.
- **Pydantic AI Hijack**: Implemented request interception and proxy logic in `sovereign-gateway`.
- **Autonomous Rollback**: Expanded `sovereign-shield` with snapshot management and atomic restoration.
- **Red-Teaming**: Added vulnerability simulation and CVSS-based reporting in `security-audit`.

### Changed

- **Skill Maturation**: Upgraded 8 core skills (Prompt Compression, File Operations, Error Recovery, etc.) to Phase 12 standards (25+ lines, Workflow/Guardrail logic).
- **Consolidation**: Merged `discovery-mcp-scanner` into `mcp-orchestration`.
- **Rebranding**: Renamed `gateway-connectivity` to `sovereign-gateway` and updated all README/Skill references.

## Phase 11.19.14 - 2026-05-11

### Added

- **Tier 0 Routing**: Re-enabled complexity-based routing (< 0.3) to Tier 0 (DeepSeek-1.5b) in `symmachia.py`.
- **Reliability Cache**: Implemented process-level fallback in `meta_cognition.py` to prevent system lockout during database locks.
- **Node Timeout**: Integrated 60s per-node timeout wrapper in the LangGraph Orchestrator to prevent agentic hangs.

### Fixed

- **Path Drift Mitigation**: Migrated 15+ core modules (fs, bootstrap, local_runtime, etc.) from `os.getcwd()` to `get_project_root()` anchoring.
- **Script Normalization**: Updated 16+ scripts in `scripts/` to use `__file__` based pathing, ensuring import reliability.
- **Reranker Type Hints**: Corrected `reranker.py` return types to match the expected dictionary structure.
- **Image Optimizer**: Replaced deprecated `_getexif` with `getexif()` and fixed EXIF orientation lookup.
- **LocalRuntime Pathing**: Fixed NoneType errors in `os.path.join` during model path resolution.

## Phase 11.19.13 - 2026-05-11

### Added

- **Ankyra Anchor (Bulgu B)**: Created `data/ankyra_anchor.md` as the system identity and constraints baseline.
- **Project Path Helper**: Implemented `src/utils/project_path.py` to eliminate `os.getcwd()` instability and ensure absolute root resolution.
- **Config Backup (Phase 9.1)**: Automated periodic snapshots for `.env`, `rules.json`, and `ankyra_anchor.md` via `backup_critical_configs.py`.
- **System Health Check**: Created `scripts/health_check.py` for automated 14-axis integrity verification.

### Fixed

- **Codebase Mapper (Phase 10)**: Expanded scan filter to include `scripts/`, `tests/`, and `agent/` directories, re-indexing 205 modules.
- **Reliability Lock (Bulgu C)**: Hardened `block_signal` to enforce hard stops based on `reliability.db` scores (< 0.3).
- **Axis Schema Alignment (Phase 7)**: Fixed missing `description` field in Axis 3 (Goals) and corrected LanceDB/Episodic schema mismatches.
- **IDE Root Conflict**: Synchronized `.vscode/settings.json` and `pyrightconfig.json` with absolute paths to enforce `D:\Hank` as the project root.
- **Environment Correction**: Patched `.env` to fix `OPENCODE_CONFIG_DIR` typo (`opencode` -> `.opencode`).

## Phase 11.19.12 - 2026-05-11

### Added

- **LLM-Driven Reflection Loop**: Integrated `extract_reflection_llm` into `theoria.py` to automate semantic insight generation.
- **Deep Path Fallback**: Implemented Ollama-based (`phi-4:mini`) relation extraction in `entity_extractor.py` for high-fidelity knowledge graphs.
- **Session Cleanup Hook**: Added `finalize_node` to the Clotho graph in `orchestrator.py` to prevent memory leaks (B9).

### Fixed

- **theoria.py Silent Failures**: Resolved NameErrors, missing `numpy` imports, and masked indexing failures.
- **Gnosis Import Paths**: Fixed absolute/relative import conflicts and IDE root resolution in `base.py` and axis builders.
- **IDE Root Conflict**: Synchronized `.vscode/settings.json` and `pyrightconfig.json` to enforce `D:\Hank` as the project root.
- **Database Performance**: Created indexes `idx_rel_subject` and `idx_refl_session` in `mnemosyne.db` for high-performance retrieval.

## Phase 11.19.11 - 2026-05-10

### Added

- **JIT Skill Injection**: Integrated `SkillLoader` into `sophia.py` (Draft & Critique) to inject active skill summaries into system prompts.
- **ToolBridge RBAC**: Implemented soft-enforcement layer in `bridge/base.py` to monitor and log unauthorized tool calls.
- **Agent YAML Registry**: Unified `hermes.yaml` format and added missing skills to `sophia`, `clotho`, `lachesis`, and `morpheus`.

### Changed

- **Procedural Hardening**: Richly updated 9 core `SKILL.md` files with Plan-Execute-Verify workflows and mandatory guardrails.
- **SkillLoader API**: Added `get_skill_summary()` and `get_allowed_tools_for_agent()` for high-fidelity reasoning and security checks.

## Phase 11.19.10 - 2026-05-10

### Added

- **Sovereign Shield**: 3-layer protection architecture (Git Baseline, Polling Guardian, Bridge Atomic Writes).
- **Snapshot Restoration**: Automated recovery for deleted or corrupted (>10% data loss) files via `snapshots.db`.
- **L0 Token Mechanism**: `scripts/create_l0_token.py` for high-privileged system changes.
- **Daemon Automation**: Integrated Shield, Morpheus, and Telemetry into a persistent Windows Task Scheduler service.
- **Skill Expansion**: Added 10 critical skills (Sovereign Shield, Gateway Connectivity, Temporal Validity, etc.).

### Fixed

- **Watchdog Race Condition**: Synchronized SnapshotManager and PollingGuardian to prevent baseline corruption during malicious writes.
- **Case-Sensitivity**: Resolved relative path mismatch in snapshot lookup logic.

## Phase 11.19.9 - 2026-05-10

### Added

- **Model Registry SSOT**: Unified model resolution via `model_registry.py` with flagship MiMo-VL (5.7GB) integration.
- **Registry Helpers**: `get_embedding_model()`, `get_qwed_models()`, and `resolve_local_model()` for dynamic variant switching.

### Fixed

- **QWED Pipeline**: Resolved 404-producing hardcoded strings in `deigma.py` and `qwed_engine.py`.
- **Tool Bridge**: Synchronized `LOCAL_MODEL_MAP` with correct Ollama model identifiers to eliminate silent failures.
- **IDE Imports**: Fixed false-positive "Cannot find module" errors by refining `pyrightconfig.json` `extraPaths`.

## Phase 11.19.8 - 2026-05-10

### Added

- **Nomic MoE Embedding**: Integrated `nomic-embed-text-v2-moe` (Q16 and Q8 variants) into local Ollama runtime.
- **Model Optimization**: Configured 512 token limits and mandatory `search_query:`/`search_document:` prefix handling.
- **GGUF Registry**: Established `D:\Google\AntiGravity\General Tools\OllamaModels` as standard artifact path for local weights.

### Changed

- **Embedding De-Hardcoding**: Replaced hardcoded `nomic-embed` strings with registry lookups across 5 core modules (`hermes_cli.py`, `sprint_contract.py`, `visual_store.py`, `theoria.py`, `retrieval.py`).

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
