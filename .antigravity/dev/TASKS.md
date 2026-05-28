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


Refactoring Plan: Nihai Yol Haritasi
On Kosullar (GO/NO-GO Gate)
#	Aksiyon	Sure	Gerekce
1	pip install pytest-cov	2dk	Coverage baseline olmadan split = blind refactor
2	test_schema_enforcement_fail -> @pytest.mark.skip	1dk	60s timeout regression her test run'inda asiliyor
3	test_sophia_run_draft_prefix_alignment -> @pytest.mark.skip	1dk	Mock API uyumsuz, known P1
Isimlendirme Kararlari
Modul	Isim	Anlami	Gerekce
Async gateway	ariadne	Ariadne (ip yumagi)	Async zincirleme cagrilar icin dogal metafor
MCP sutunu	hermes_mcp	Hermes (ulak)	Mevcut Hermes bridge ile tutarli
Circuit breaker	kratos	Kratos (guc/kisitlama)	Sinirlama/kontrol mekanizmasi icin uygun
Sync gateway	nomos	Nomos (yasa/kural)	Senkron kurallar icin
Cache modulu	context_cache.py	Mevcut	Zaten var, sadece gateway'den tasinacak
Bootstrap sutunu	ananke	Ananke (zorunluluk)	Startup sirasi dogasi icin
Faz 1: gateway_client Ayristirmasi (3 alt modul)
src/architrave/
├── kratos.py              ~120 satir - circuit breaker + retry
├── nomos.py               ~250 satir - sync generate suite
├── ariadne.py             ~350 satir - async generate suite
└── gateway_client.py      ~220 satir (kalan: provider classes + facade)
Etkilenen dosyalar: ~23 import guncellemesi (gateway_client import eden 12 test + 11 source module)
Risk	Sebep	Mitigasyon
Dusuk	kratos (circuit breaker) tamamen izole, hicbir module bagli degil	Once bunu yap
Orta	nomos + ariadne ortak sekilde SovereignProvider ve MockResponse kullaniyor	Base class facade olarak kalsin
Orta	23 dosyada import yolu degisecek	__init__.py re-export ile backwards compat
Faz 2: bootstrap + MCP Sutunu
src/clotho/
├── ananke.py              ~250 satir - startup pipeline (bootstrap'tan cikar)
├── krisis.py (mevcut)     - zaten Greek, dokunma
src/architrave/mcp/
├── hermes_mcp.py          ~200 satir - SLM MCP servis yonetimi (slm_client'tan cikar)
├── mcp_session.py         ~250 satir (kalan: stdio protocol)
├── slm_client.py          ~150 satir (kalan: client wrapper)
Risk: bootstrap 18 outward dep -> yeni modul ayni dep'lere sahip olacak. Kritik degil ama dikkatli import path yonetimi gerek.
Faz 3: hephaestus + sophia
cognition/sophia/
├── telos.py               ~200 satir - strategic reasoner (sophia.py'den cikar)
├── sophia.py              ~400 satir (kalan: draft/critique/refine orchestration)
├── hephaestus.py          ~200 satir (kalan: singleton getters)
├── eidos.py               (mevcut, dokunma)
└── gnosis/                (mevcut, dokunma)
Risk: En yuksek. hephaestus 29 inc + 20 out edge. Bu faza dokunmadan once Faz 1+2 stabil oldugu dogrulanmali.
Zaman Cizelgesi (Gercekci)
Hazirlik (15dk):
├── pip install pytest-cov             2dk
├── 2 teste @skip ekle                 2dk
├── coverage baseline al                5dk
└── import haritasi cikar               6dk
Faz 1 (6-8 saat):
├── 1a: kratos - circuit breaker        1-2 saat
│   ├── yeni dosya + func tasima
│   └── import guncelle + test
├── 1b: nomos - sync generate          2-3 saat
│   ├── yeni dosya + func tasima
│   └── import guncelle + test
├── 1c: ariadne - async generate       2-3 saat
│   ├── yeni dosya + func tasima
│   └── import guncelle + test
└── regression: full test suite        30dk
Faz 2 (4-6 saat):
├── 2a: ananke - bootstrap split       2-3 saat
└── 2b: hermes_mcp - MCP sutunu       2-3 saat
Faz 3 (4-6 saat):
├── 3a: telos - sophia split           2-3 saat
└── 3b: hephaestus cleanup             2-3 saat
Toplam: 14-20 saat (tum codebase'e yayilmis, kesintisiz)
Go/No-Go Karari
Sartlar:
[x] 4 Socratic soru cevaplandi
[x] bootstrap -> hephaestus bagimsizligi dogrulandi
[x] Risk skorlari cikarildi
[x] Isimlendirme kararlari verildi
[ ] pytest-cov kurulacak
[ ] 2 test @skip eklenecek
[ ] coverage baseline alinacak
Karar: CONDITIONAL GO
Risk/Clarity: 0.25 (kabul edilebilir)

Goal
- Integrate MCP servers (sequential-thinking, fetch, kg-mem, github, playwright) with sovereign agent infrastructure, fix agent YAML skill bindings, establish MCP tool governance, and complete 3-phase module refactoring (gateway, bootstrap, sophia)
Constraints & Preferences
- Always get L0 auth token before write operations (create_l0_token.py)
- 5 config files must stay in sync (mcp_config.json variants + gemini config)
- SLM MCP active for stateful context, no stateless operation
- PR-based workflow for GitHub (no direct push to main)
- Playwright sessions must close after each use
- EMOJI_BAN, LACONISM_MANDATE, BA-01 still enforced
- Repairs use qwen3.5-2b-ud (no legacy models)
- Mock patch paths must target the actual module where a name is looked up (not where it's re-exported)
Progress
Done
- Refactoring Faz 1 (GatewayArchitrave split): gateway_client.py 919L→276L. Created kratos.py (circuit-breaker, retry, build_safety_settings), nomos.py (sync gateway), ariadne.py (async gateway). 23/23 tests passed.
- Refactoring Faz 2 (bootstrap extraction): bootstrap.py 580L→112L. Created ananke.py (Morpheus daemon manager: shutdown registry, scheduler/sweeper/loader init, start_morpheus/stop_morpheus, telemetry, shield, a2a server), hermes_mcp.py (SLM daemon manager: discover_slm_port, start_slm_server, start_slm). 17/17 tests passed.
- Refactoring Faz 3a (telos - sophia.py split): sophia.py 639L→13L re-export. Created cognition/sophia/telos/ package: draft.py (418L, tier routing + JSON parsing + guard), critique.py (97L), refine.py (109L), _gateway.py (10L mock-safe re-export).
- Refactoring Faz 3b (hestia - hephaestus cleanup): hephaestus.py 330L→47L re-export. Created cognition/sophia/hestia/ package: singletons.py (16 getters + governance sync), text_utils.py (strip_thinking_block, extract_first_json_block, extract_tool_calls), instructions.py (get_sophia_instructions). Fixed circular import: relative ..mnemosyne → absolute cognition.mnemosyne. 21/21 tests passed.
- Mapper update: .venv-linux excluded from scanner, deleted (40.5MB). WSL Ubuntu-22.04 unregistered. Mapper report: 266 modules, 0 layer violations.
- Sovereign Middleware Proxy (Phase 1.1.23): 4 middleware files + genai_manager.py (gemini-3.5-flash). 7/7 tests passed.
- 6 new gstack-inspired skills created: review-pipeline, ship-deploy, autoplan, design-suite, browser-qa, safety-guardrails.
- Audit skill: merged autonomous-qa-evals + review-pipeline into 6-phase pipeline.
- SLM daemon: port 8765, recall 466ms (HTTP), warmup disabled via SLM_DISABLE_WARMUP_SIDE_EFFECTS=1.
- MCP Wave 1+2: sequential-thinking, fetch, kg-mem, github (26 tools), playwright (33 tools) installed and tested.
- 5 config files synced: all MCP servers in all locations.
- Agent YAML fixes: clotho (agent_tools→tools), lachesis, sophia updated with new skills.
- MCP governance: tools.md (Sec 11-15), rules.json (RULE-039), AGENTS.md updated.
- MCP benchmark: 5/6 PASS (83%), SLM stdio timeout.
- CHANGELOG.md: Phase 1.1.23 + 1.1.24 sections added.
In Progress
- (none)
Blocked
- SLM MCP stdio init timeout (30s): slm.exe mcp handshake fails in MCPSession._connect_async. Daemon on port 8765 works fine via HTTP.
- GitHub MCP needs runtime GITHUB_TOKEN (wrapper script exists, no token in .env yet).
Key Decisions
- BRAVE SEARCH SKIPPED: redundant with webfetch + fetch MCP + playwright MCP.
- BROWSE MCP REMOVED: replaced by playwright MCP (33 tools).
- gstack skills adapted to sovereign agent model.
- telos package for sophia draft/critique/refine split provides mock-compatible patch targets.
- hestia package for hephaestus singleton getters avoids circular imports via absolute path imports.
- .venv-linux excluded from mapper scan and deleted; WSL distro unregistered to clean up stale Linux environment artifacts.
Next Steps
- Resolve SLM MCP stdio timeout (Windows MCPSession compatibility).
- Set GITHUB_TOKEN in .env and verify github MCP runtime.
- Run full MCP test plan with 17 measurement tests.
- Update skill files P0-P2 (browse→playwright redirect, mcp-orchestration MCP references).
- Map old autonomous-qa-evals tests to new audit skill pipeline.
Critical Context
- Refactoring totals: gateway_client 276L + kratos 174L + nomos 344L + ariadne 228L + bootstrap 112L + ananke 375L + hermes_mcp 106L + sophia 13L + telos/ 634L + hephaestus 47L + hestia/ 289L = 16 files, ~1598L total (was 2468L in 3 files).
- Mock path gotcha: from cognition.sophia.sophia import X still works (re-export), but @patch("cognition.sophia.sophia.get_dynamic_context") in tests must be updated to cognition.sophia.telos.draft.get_dynamic_context for internal function lookups.
- 104 total MCP tools: 34 SLM + 1 sequential-thinking + 1 fetch + 9 kg-mem + 26 github + 33 playwright.
- 51 total skills (45 SKILL.md dirs + redirects).
- 266 modules, 0 layer violations (verified by mapper after cleanup).
- SLM DB: 8 facts, 11 entities, 17 edges, 4.19 MB, mode=b (Smart Local).
- WSL Ubuntu-22.04 unregistered; .venv-linux deleted.
Relevant Files
- src/architrave/kratos.py: Circuit breaker, retry, build_safety_settings (new, 174L)
- src/architrave/nomos.py: Sync gateway operations (new, 344L)
- src/architrave/ariadne.py: Async gateway operations (new, 228L)
- src/architrave/gateway_client.py: Thin GatewayArchitrave wrapper (thinned to 276L)
- src/clotho/ananke.py: Morpheus daemon manager (new, 375L)
- src/clotho/hermes_mcp.py: SLM daemon manager (new, 106L)
- src/clotho/bootstrap.py: Thin CLI entry point, re-exports from ananke + hermes_mcp (112L)
- cognition/sophia/telos/draft.py: run_draft with tier routing (418L)
- cognition/sophia/telos/critique.py: run_critique via Ollama (97L)
- cognition/sophia/telos/refine.py: run_refine with guard retry (109L)
- cognition/sophia/hestia/singletons.py: 16 get* singleton getters (206L)
- cognition/sophia/hestia/text_utils.py: Text extraction utilities (55L)
- cognition/sophia/hestia/instructions.py: get_sophia_instructions (28L)
- cognition/sophia/sophia.py: Thin re-export (13L)
- cognition/sophia/hephaestus.py: Thin re-export (47L)
- src/lachesis/mapper/graph_manager.py: EXCLUDE_DIRS updated (added .venv-linux)
- src/architrave/mcp/mcp_registry.py, mcp_session.py, mcp_tool_bridge.py: MCP server infrastructure
- agent/skills/*/SKILL.md: 51 skill definition files
- agent/*.yaml: 7 agent YAML definitions
- .antigravity/topography.md, tools.md, rules.json, AGENTS.md: Governance docs
- scripts/update_mapper.py, scripts/run_github_mcp.bat: Utility scripts
