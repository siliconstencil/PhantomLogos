# Phantom Logos Development Tasks

## Codebase Mapper Hardening [COMPLETED]
- [x] **M1: AST Migration**
    - [x] `codebase_mapper.py`: Replace regex `IMPORT_PATTERN` with `ast.parse`
    - [x] Handle multi-line imports, aliases, conditional imports
- [x] **M2: SQL LIKE Optimization**
    - [x] `spatial_store.py`: Add `query_by_keywords()` with case-insensitive `LIKE`
    - [x] `codebase_mapper.py`: Update `suggest_context()` to use `query_by_keywords`
- [x] **M3: Incremental Remap + Prune**
    - [x] `codebase_mapper.py`: Add `remap_file()` with single-file + dependent update
    - [x] `spatial_store.py`: Add `prune_deleted_module()` for zombie cleanup
- [x] **M4: Circular Detection**
    - [x] `codebase_mapper.py`: Add `detect_circular()` with DFS coloring
- [x] **M5: Thread Safety**
    - [x] `codebase_mapper.py`: Add `threading.Lock` for sync methods
    - [x] `mapper_bridge.py`: Add `asyncio.Lock` for async debounce layer
- [x] **M6: Debounced Remap**
    - [x] `mapper_bridge.py`: `asyncio.Task.cancel()`-based true debounce (1s)
- [x] **M7: Spatial Injection Node**
    - [x] `ergon.py`: `anchor_inject_node` uses direct `suggest_context` instead of tool call
    - [x] `tool_bridge.py`: `_mapper` returns deprecation guidance message
- [x] **M8: GraphState Update**
    - [x] `orchestrator.py`: Add `spatial_context` and `spatial_dirty` to TypedDict
- [x] **M9: Verification**
    - [x] AST test: `codebase_mapper.py --test` passes
    - [x] Debounce test: 3 writes → 1 remap (cancellation verified)
    - [x] Lachesis audit: 7/7 files verified

## Two-Stage Semantic Reranking [COMPLETED]
- [x] **R1: Candidate Pool Expansion**
    - [x] `semantic`: limit 20 → 100 for wider coverage
    - [x] LanceDB L2 sort → top 20 → Jina rerank → top 5
- [x] **R2: Performance**
    - [x] +0.1s overhead for 5x pool size (~2.1s total)
    - [x] MarcoReranker bypassed (MS-MARCO incompatible with llama.cpp)
- [x] **R3: Integration**
    - [x] `muscle/__init__.py`: Export MarcoReranker
    - [x] Zero new models, zero VRAM increase

## Sovereign Hardening [COMPLETED]
- [x] **H1: OutputGuard Pipeline**
    - [x] `ergon.py`: OutputGuard.check() in verify_node
    - [x] `ergon.py`: OutputGuard in refine_node
- [x] **H2: l0_approved Gate**
    - [x] `orchestrator.py`: l0_approved field + wait_for_l0 node + hard stop
    - [x] `krisis.py`: Reliability kill-switch (< 0.2 → END)
- [x] **H3: Z3 Integration**
    - [x] `ergon.py`: verify_logic() in verify_node
    - [x] Sympy complexity tier calculation
- [x] **H4: Thinking Param Fix**
    - [x] `gateway_client.py`: thinking=True → thinking_config conversion
    - [x] Exception splitting: ValidationError → raise, Timeout → fallback
- [x] **H5: Prompt Quality**
    - [x] XML structured prompts in draft_node
    - [x] BAD/GOOD few-shot examples
- [x] **H6: Model Blacklist Fix**
    - [x] granite-4.1-8b → fallback, qwen2-5-coder-7b → primary
- [x] **H7: BA-01 Exemption**
    - [x] output_guard.py: is_user_interaction bypasses Turkish char check

## Documentation Alignment [COMPLETED]
- [x] **D1: Global Rebrand**
    - [x] Phantom Logos → Phantom Logos across 14 documentation files
    - [x] 13-axis consistency check (all 12-axis references corrected)
- [x] **D2: Sync**
    - [x] Broken links restored (AGENTS.md cross-references)
    - [x] ROADMAP.md synchronized with current progress

## True Agency [COMPLETED]
- [x] **T1: Dynamic Agent Selection**
    - [x] `ergon.py`: Task type routes to Sophia/Clotho/Lachesis dynamically
    - [x] `krisis.py`: Hallucination spiral fix (3 failed → deadlock_resolver)
- [x] **T2: Skills**
    - [x] 5 new SOTA skills (MCP Discovery, Mnemosyne Query, VRAM Profiler, Deadlock Resolver, Error Recovery)
    - [x] Total 23 skills active

## Skill Restructuring [COMPLETED]
- [x] **S1: Recovery**
    - [x] 10 phantom SKILL.md files created
    - [x] YAML parser upgrade → `yaml.safe_load()`
- [x] **S2: Merge**
    - [x] AGENTS.md root + .antigravity consolidated
    - [x] skills/ moved to agent/skills/

## System Hardening [COMPLETED]
- [x] **H1: Protocol**
    - [x] Transport hardening (`trust_env=False`)
    - [x] Ollama singleton `AsyncClient` across 6 modules
    - [x] CPU pool limited to `max_workers=4`
- [x] **H2: Performance**
    - [x] 9 `asyncio.to_thread` calls for heavy sync ops
    - [x] EntityExtractor thread-safety

## Sovereign Rebirth [SEALED]
- [x] **R1: Rebrand**
    - [x] Phantom Logos → Phantom Logos
    - [x] 13-axis foundation sealed
- [x] **R2: Architecture**
    - [x] Absolute Agnosticism (all routing via Sovereign Gateway)
    - [x] GatewayArchitrave unified client
    - [x] All previous 11.x iterations consolidated

## SovereignTruthGuard [DEFERRED]
- [ ] **G1: CRITICAL - Shadow Verification**
    - [ ] `output_guard.py`: Define `VIOLATION_SHADOW_VERIFY` & impact
    - [ ] `tool_bridge.py`: Implement real-time hardware telemetry assertions
- [ ] **G2: HIGH - Schema Enforcement**
    - [ ] `hephaestus.py`: Define `SophiaOutput` Pydantic models
    - [ ] `sophia.py`: Enforce schema-validated generation for L1
- [ ] **G3: HIGH - Governance Gates**
    - [ ] `gnosis.py`: Implement failure-based hard gates for severe recurrence
    - [ ] `krisis.py`: Handle `bypass_memory_gate` and model blacklisting
- [ ] **G4: HIGH - Auto-Rotation**
    - [ ] `self_tuner.py`: Automate model rotation after consecutive verification failures
    - [ ] `krisis.py`: Implement fallback chain routing for blacklisted models

## Rapid Integration (Flash Mode Refactor) [COMPLETED]
- [x] **S1: CRITICAL - Core Hardening**
    - [x] `tool_bridge.py`: Remove `shell` tool entirely
    - [x] `security_utils.py`: Create keyring integration with env fallback
    - [x] `migrate_keys.py`: Create migration script for secrets
    - [x] `bootstrap.py`: Call secret loader
    - [x] `.gitignore`: Add `.env.*`
- [x] **S2: HIGH - Input Validation**
    - [x] `temporal_store.py`: Sanitize session_id
    - [x] `sympy_verifier.py`: Replace eval with parse_expr
    - [x] `tool_bridge.py`: Fix path traversal in `ls` tool
- [x] **S3: HIGH - Concurrency/Lifecycle**
    - [x] `reasoning_nodes.py`: Lock singletons (threading.Lock) + fix bare except
    - [x] `bootstrap.py`: Lock start/stop_morpheus (threading.Lock)
    - [x] `logging_config.py`: Implement SQLiteHandler.close()
- [x] **S4: MEDIUM - Silent Failures**
    - [x] `orchestrator.py`: Log warnings in except blocks
    - [x] `agent_loader.py`: Log warnings in except blocks
    - [x] `skill_loader.py`: Log warnings in except blocks
    - [x] `state_bus.py`: Lock get_state_bus
    - [x] `token_budget.py`: Lock get_token_guard
- [x] **S5: LOW - Cleanup**
    - [x] `requirements.txt`: Add `keyring`
    - [x] `reasoning_nodes.py`: Add API key regex validation
- [x] **Verification**
    - [x] `tests/test_security_utils.py`: Create and run security tests
    - [x] Verify keyring loading and fallback logic
    - [x] Verify shell tool removal

## Sovereign Knowledge Base Consolidation [COMPLETED]
- [x] Create directory structure in `.antigravity/`
- [x] Move blueprints (`topography.md`, `tools.md`)
- [x] Move history (`audit/`, `walkthroughs/`)
- [x] Persist `TASKS.md` from memory artifact
- [x] Repair links across all `.md` files (README, walkthroughs, etc.)
- [x] Create `CONSTITUTION.md` (Constitutional AI Rules)
- [x] Create `AGENTS.md` (Technical onboarding for agents)
- [x] Create `SECURITY.md` (Sovereign secret management guide)
- [x] Create `CONTRIBUTING.md` (Technical standards)
- [x] Implement `LICENSE` (MIT)
- [x] Optimize `.gitignore` for GitHub standards
- [x] Finalize `README.md` rewrite

## Architectural Decoupling [COMPLETED]
- [x] **Sophia Layer Decomposition**
    - [x] Create `hephaestus.py` (Tools/Schemas)
    - [x] Create `gnosis.py` (Context Assembly)
    - [x] Create `sophia.py` (Core Reasoning)
    - [x] Update `__init__.py` redirects
- [x] **Clotho Layer Decomposition**
    - [x] Create `ergon.py` (Node Functions)
    - [x] Create `krisis.py` (Routing Logic)
    - [x] Slim down `orchestrator.py` (Spine/Graph)
- [x] **System Hardening**
    - [x] Purge legacy `reasoning_nodes.py`
    - [x] Fix cross-module import inconsistencies
    - [x] Update documentation references (`topography.md`, `walkthroughs`, etc.)
- [x] **Verification**
    - [x] 19/19 Integration tests pass
    - [x] 13-Axis stability audit SUCCESS

## Agnostic Gateway Refactor [COMPLETED]
- [x] **D1: CRITICAL - Agnostic Client**
    - [x] `gemini_client.py`: Refactor to `AgnosticArchitrave`
    - [x] `gemini_client.py`: Implement `HttpOptions(base_url)` proxy routing
    - [x] `gemini_client.py`: Add dummy `api_key` for native gateway bypass
- [x] **D2: HIGH - Capability Decoupling**
    - [x] `model_registry.py`: Remove commercial model aliases (Gemini/Flash/Pro)
    - [x] `model_registry.py`: Update `CAPABILITY_MAP` for strategic gateway
    - [x] `rules.json`: Update Sophia role to use `antigravity-strategic-gateway`
- [x] **D3: HIGH - System Integration**
    - [x] `hephaestus.py`: Refactor `_get_cloud_gateway` to use capability resolution
    - [x] `sophia.py`: Update to new `AgnosticArchitrave` and clean logs
- [x] **Verification**
    - [x] `tests/test_agnostic_gateway.py`: Verify proxy routing & SDK masking
    - [x] `tests/stability_check_phase_11_18_1.py`: Verify async flow integrity
    - [x] **T5: CRITICAL - Operational Failure Audit**
        - [x] Identify and document 14 points of failure (Phase 11.18.3 Post-Mortem)
        - [x] Implement SSOT-compliant fixes for ModelLoader and VisionRouting
        - [x] Integrate Lessons Learned into Axis 8 (Meta-Cognition)

## Sovereign Event Loop Hardening [COMPLETED]
- [x] **E1: CRITICAL - Async Persistence**
    - [x] `orchestrator.py`: Migrate to `AsyncSqliteSaver`
    - [x] `control_handoff.py`: Implement global 120s timeout and `thread_id`
- [x] **E2: HIGH - Non-blocking Tools**
    - [x] `tool_bridge.py`: Wrap all sync handlers in `asyncio.to_thread`
    - [x] `tool_bridge.py`: Implement per-tool 30s timeout
    - [x] `tool_bridge.py`: Add `ActivityMonitor` increment/decrement
- [x] **E3: HIGH - Cognitive Layer Async**
    - [x] `gnosis.py`: Convert `get_dynamic_context` to `async def`
    - [x] `gnosis.py`: Use `ollama.AsyncClient` for embeddings
    - [x] `sophia.py`: Await context assembly in all nodes
    - [x] `sprint_contract.py`: Async keyword embedding pre-computation
- [x] **E4: MEDIUM - Safe Healing**
    - [x] `sweeper.py`: Implement `_has_active_operations` check via `ActivityMonitor`
    - [x] `gemini_client.py`: Enforce 90s timeout on cloud calls
- [x] **Verification**
    - [x] `scratch/stability_test.py`: Verify no event loop blocking under load
    - [x] Verify persistence recovery across async sessions
