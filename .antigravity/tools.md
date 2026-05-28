# Phantom Logos: Local Model Ecosystem & Performance Matrix (Muscle)

[09:00 PM PT] | Status: **Sovereign Standardized (46 models + 6 MCP Servers / 103 tools + 51 Skills)**

## 1. Quantization & Benchmark Notes

All models below use GGUF quantization (Q4_K_M, Q5_K_XL, Q6_K, Q8_0). Benchmark scores are taken from official model publications and represent base-model accuracy at full precision. **Quantized models exhibit -2% to -5% degradation** on complex reasoning tasks compared to FP16 baselines. Unsloth Dynamic (UD) variants preserve critical layers, minimizing this gap for attention-heavy workloads.

 | Format | Strategy | Performance Loss | VRAM Savings |
 | --- | --- | --- | --- |
 | **Q4_K_M** | Medium quality, most VRAM-efficient | ~3-5% | 4-bit (~50% of FP16) |
 | **Q5_K_XL** | Extra-large, slightly better than Q5_K_M | ~2-3% | 5-bit (~55% of FP16) |
 | **Q6_K** | High quality, recommended for verification | ~1-2% | 6-bit (~62% of FP16) |
 | **Q8_0** | Maximum quality (embedding/reranker) | ~0-1% | 8-bit (~70% of FP16) |
 | **UD (Unsloth Dynamic)** | Adaptive per-layer bit-width | ~1-3% (better than uniform) | Variable (Pareto-optimal) |

---

## 2. Active Model Inventory & Performance Matrix

### 2.1 Reasoning Core (L0-L2)

 | Model | Features | VRAM | MMLU | HumanEval | MATH | Context | Tok/s | Role | Alias |
 | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
 | **Qwen 3.5 4B UD** `qwen3.5-4b-ud:latest` | T, J, C | 2.9 GB | 70% | 85% | 60% | 32K | ~30 | L2 Primary | â€” |
 | **Ministral 3B** `ministral-3b-ud:latest` | T, J | 2.2 GB | 60% | 65% | 45% | 32K | ~35 | L2 Light | â€” |
 | **Hermes-3 Llama-3.1 8B** `hermes-3-llama-3.1-8b:latest` | T, J | 4.9 GB | 69% | 62% | 55% | 128K | ~16 | L2 Alternative | â€” |
 | **Qwen 3.5 9B UD** `qwen3.5-9b-ud:latest` | T, J, C | 6.0 GB | 78% | 75% | 70% | 32K | ~14 | L1 Local Alt | â€” |
 | **Llama 3.1 8B** `meta-llama-3.1-8b:latest` | T | 4.9 GB | 69% | 64% | 50% | 128K | ~17 | L2 Alternative | â€” |
 | **MiMo-7B-Text UD** `mimo-7b-txt-ud:latest` | C, J, T | 5.7 GB | 72% | 80% | 95% | 32K | ~12 | L2 Reasoning | Alias of `mimo-7b-vl-ud` |
 | **DeepSeek-R1-Qwen3 8B** `deepseek-r1-qwen3-8b:latest` | C, M, J | 5.1 GB | 78% | 85% | 94.5% | 32K | ~16 | L2 Math Expert | â€” |
 | **Granite 4.1 8B UD** `granite-4.1-8b-ud:latest` | T, J | 5.5 GB | 73% | 70% | 55% | 128K | ~15 | L2 Fallback | â€” |

### 2.2 Ultra-Light Tier (L0)

 | Model | VRAM | MMLU | HUMANEVAL | Context | Tok/s | Role |
 | --- | --- | --- | --- | --- | --- | --- |
 | **DeepScaler 1.5B** `deepscaler-1.5b:latest` | 1.1 GB | â€” | â€” | 8K | ~45 | L0 Primary â€” Math-first reasoning, fast |
 | **DeepSeek-R1-Distill-Qwen 1.5B** `deepseek-r1-1.5b:latest` | 1.9 GB | 40% | 38% | 32K | ~48 | L0 Fallback â€” Chain-of-thought reasoning |
 | **Qwen 3.5 0.8B** `qwen3.5-0.8b-ud:latest` | 1.2 GB | 55% | â€” | 32K | ~55 | L0 Alternative â€” Newer architecture |
 | **SmolLM2 1.7B** `smollm2-1.7b-q5:latest` | 1.2 GB | 40% | â€” | 8K | ~60 | L0 Alternative â€” Tiny generalist |
 | **Llama 3.2 1B** `llama-3.2-1b-ud:latest` | 0.9 GB | 38% | 36% | 128K | ~70 | L0 Alternative â€” Long context, tiny |
 | **TinyLlama 1.1B** `tinyllama:latest` | 0.7 GB | 26% | 36% | 2K | ~70 | L0 Extreme â€” OOM recovery, smallest footprint, temp=0.7 |

### 2.3 Auditor & Verification (L3 / Axis 11)

 | Model | VRAM | MMLU-PRO | MATH | Context | Tok/s | Role |
 | --- | --- | --- | --- | --- | --- | --- |
 | **Phi-4 Mini** `phi-4-mini-ud:latest` | 2.8 GB | 79% | â€” | 16K | ~25 | L3 Primary â€” Adversarial auditing, critique |
 | **Qwen 2.5 Coder 3B** `qwen2.5-coder-3b:latest` | 2.5 GB | 65% | â€” | 32K | ~35 | Axis 11 â€” Code logic audit (QWED) |
 | **Qwen 2.5 Math 7B** `qwen2.5-math-7b-q4:latest` | 4.7 GB | â€” | 52% | 4K | ~15 | Axis 11 â€” Natural language math verification |
 | **DeepSeek-Math 7B** `deepseek-math-7b:latest` | 4.7 GB | â€” | 51.7% | 4K | ~18 | Axis 11 â€” C-8 Entegre: \boxed{} Soru/Cevap, temp=0.0 |
 | **Qwen 2.5 Coder 0.5B** `qwen2.5-coder-0.5b:latest` | 0.5 GB | 44% | 42% | 32K | ~80 | Axis 11 â€” Rapid deterministic fallback |
 | **Qwen 3.5 2B** `qwen3.5-2b-ud:latest` | 1.9 GB | 65% | â€” | 32K | ~40 | Axis 11 â€” Light verification alternative |
 | **Qwen 3.5 4B** `qwen3.5-4b-ud:latest` | 2.9 GB | 70% | â€” | 32K | ~30 | Axis 11 â€” Verification alternative |
 | **DeepSeek-R1-8B** `deepseek-r1-8b:latest` | 5.1 GB | 78% | 85% | 32K | ~16 | Axis 11 â€” [Phase 1.0.24] Reasoning + Math expert |
 | **Open-Xi-Math** `open-xi-math:latest` | 1.1 GB | â€” | â€” | 8K | ~18 | Axis 11 â€” [Phase 1.0.24] High-fidelity math verification |
 | **SmolLM3-3B** `smollm3-3b:latest` | 1.9 GB | 60% | â€” | 8K | ~35 | Axis 11 â€” [Phase 1.0.24] Fast math/reasoning |
 | **Qwen2.5-Math-1.5B** `qwen2.5-math-1.5b:latest` | 1.1 GB | â€” | â€” | 4K | ~45 | Axis 11 â€” [Phase 1.0.24] Small specialized math |
 | **math-mini-0.6B** `math-mini-0.6b:latest` | 0.45 GB | â€” | â€” | 4K | ~60 | Axis 11 â€” [Phase 1.0.24] Ultra-light math fallback |
 | **qwq-math-io-500m** `qwq-math-io-500m:latest` | 0.4 GB | â€” | â€” | 4K | ~70 | Axis 11 â€” [Phase 1.0.24] Minimalist math bridge |

### 2.4 Vision Pipeline (LocalRuntime & Ollama)

 | Model | Features | VRAM | OCR | Scene | Diagram | MATH | Runtime | Role | Alias |
 | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
 | **MiMo-VL-7B-RL** `mimo-7b-vl-ud:latest` | V, C, J | 5.7 GB | ++ | ++ | ++ | 95.4 | Ollama | **Flagship VLM** | â€” |
 | **Gemma-4B-Vision** `gemma-4b-vision-ud:latest` | V, T | 6.1 GB | + | ++ | + | â€” | Ollama | Vision Alt | â€” |
 | **Qwen3-VL-Thinking** `qwen3-vl-thinking-ud:latest` | V, C | 3.4 GB | ++ | + | ++ | â€” | Ollama | Vision Alt | â€” |
 | **Qwen2-VL OCR** `qwen2-vl-ocr-2b:latest` | V | 1.1 GB | ++ | + | â€” | â€” | Ollama | OCR Focus | â€” |
 | **Qwen2.5-VL 3B** `qwen2.5-vl-3b:latest` | V, J | 2.5 GB | + | ++ | + | â€” | Ollama | Light Vision | â€” |
 | **MiMo-7B-Text** `mimo-7b-txt-ud:latest` | C, J | 5.7 GB | â€” | â€” | â€” | 95.4 | Ollama | Text Alias | `mimo-7b-vl-ud` |
 | **Gemma-4B-Text** `gemma-4b-txt-ud:latest` | T, J | 6.1 GB | â€” | â€” | â€” | â€” | Ollama | Text Alias | `gemma-4b-vision-ud` |
 | **Qwen3-VL-Txt** `qwen3-vl-thinking-txt-ud:latest` | C, J | 3.4 GB | â€” | â€” | â€” | â€” | Ollama | Text Alias | `qwen3-vl-thinking-ud` |
 | **Qwen2.5-VL-Txt** `qwen2.5-vl-3b-txt:latest` | J | 2.5 GB | â€” | â€” | â€” | â€” | Ollama | Text Alias | `qwen2.5-vl-3b` |
 | **Qwen2-VL-OCR-Txt** `qwen2-vl-ocr-txt:latest` | T | 1.1 GB | â€” | â€” | â€” | â€” | Ollama | Text Alias | `qwen2-vl-ocr-2b` |

### 2.5 Embedding, Reranking & Tool Calling

 | Model | VRAM | MTEB | Cross-Encoder | Context | Role |
 | --- | --- | --- | --- | --- | --- |
 | **Nomic Embed v2 MoE Q8** `nomic-embed-text-v2-moe-q8:latest` | 0.5 GB | 69% | â€” | 8192 | Axis 6 â€” Semantic memory embedding |
 | **Nomic Embed v2 MoE Q16** `nomic-embed-text-v2-moe-q16:latest` | 1.0 GB | 70% | â€” | 8192 | Axis 6 â€” Quality embedding (high-accuracy) |
 | **Jina Reranker v3** `jina-reranker-v3:latest` | 0.6 GB | â€” | 60%+ | 8192 | Axis 6 â€” Search result refinement |
 | **Jina Embeddings v3** `jina-embeddings-v3:latest` | 0.6 GB | 65% | â€” | 8192 | Axis 6 â€” Alternative embedding |
 | **MS-MARCO MiniLM** `ms-marco-minilm:latest` | 0.09 GB | â€” | 45%+ | 512 | Reranker â€” DEPRECATED (Nomic+Jina cascade active) |
 | **FunctionGemma 270M** `functiongemma-270m:latest` | 0.3 GB | â€” | â€” | 8192 | Tool calling â€” Structured JSON function dispatch |
 | **Granite 3-2B** `granite-3-2b:latest` | 1.6 GB | 55% | â€” | 8192 | Router â€” Capability-based task routing |

### 2.6 Fallback & Alternative Models

 | Model | VRAM | MMLU | Context | Tok/s | Role |
 | --- | --- | --- | --- | --- | --- |
 | **Granite 4.1 8B** `granite-4.1-8b:latest` | 5.5 GB | 73% | 128K | ~15 | L2 Fallback â€” Draft fallback (blacklisted pending fix) |
 | **Llama 3.2 3B** `llama-3.2-3b-ud:latest` | 2.1 GB | 62% | 128K | ~35 | L2 Light Alternative â€” Long context |

---

## 2.7 Model Configuration Rules (Tokenizer & Parameters)

These rules are critical for correct model behavior. Violations cause silent degradation (garbage output, endless repetition, refusal to reason).

 | Model | Tokenizer/Ozellik | Zorunlu Ayar | Aciklama |
 | --- | --- | --- | --- |
 | **R1 Serisi** | R1 special `<think>` | **`<think>\n` prefix; No System Prompt; temp=0.6** | R1 reasoning loop'u tetiklemek icin cikti `<think>\n` ile baslamali. |
 | **MiMo-VL** | Thinking Toggle | **temp=0.3; `/think` (reasoning), `/no_think` (concise)** | Xiaomi RL model. Gorsel input metinden ONCE gelmeli. q8_0 cache onerilir. |
 | **Qwen2.5-VL** | Structured JSON | **temp=0.0; Use `format: json_schema` via API** | JSON cikti icin greedy decoding ve schema zorunlu. |
 | **FunctionGemma** | Tool Focus | **temp=0.1; JSON output format only** | Structured JSON function dispatch icin optimize. |
 | **Phi-4 Mini** | Critique/Audit | **temp=0.2 (audit); CoT enabled** | Adversarial auditing icin dÃ¼sÃ¼k temperature ve CoT destegi. |

---

## 3. RuFlow 3-Tier + Ultra-Light Routing Strategy

 | Tier | Label | Agent | Primary Model | VRAM | Fallback |
 | --- | --- | --- | --- | --- | --- |
 | **Tier 0** | Ultra-Light | Fast response, skip audit | `deepscaler-1.5b:latest` | 1.1 GB | `deepseek-r1-1.5b:latest` |
 | **Tier 1** | Light | Rapid, low-latency | `ministral-3b-ud:latest` | 2.2 GB | `llama-3.2-3b-ud:latest` |
 | **Tier 2** | Primary | Standard agentic loops | `qwen3.5-4b-ud:latest` | 2.9 GB | `granite-4.1-8b-ud:latest` |
 | **Tier 3** | Expert (Cloud) | Deep reasoning | `models/antigravity-strategic-gateway` | â€” | `qwen3.5-9b-ud:latest` (local) |

### Tier Selection Rules

- Complexity < 0.3 or VRAM < 2 GB â†’ **Tier 0** (skip tools, skip verification)
- Complexity 0.3-0.5 â†’ **Tier 1** (tools enabled, lightweight)
- Complexity 0.5-0.8 â†’ **Tier 2** (full tool access, full verification)
- Complexity > 0.8 â†’ **Tier 3** (expert reasoning, cloud preferred)

---

## 4. VRAM Budget & Loading Policy

 | Component | GB | Notes |
 | --- | --- | --- |
 | Total GPU VRAM | 8.0 | RTX 4070 Laptop GDDR6 |
 | Windows OS reservation | 1.0 | Driver + composition + explorer |
 | Always resident | 1.1 | Nomic Embed (0.5) + Jina Reranker (0.6) |
 | **Available for LLMs** | **5.9** | Max 2 concurrent LLMs (3-5 GB each) |

### Operating Modes

 | Mode | Active Models | VRAM | Use Case |
 | --- | --- | --- | --- |
 | **Default (L2+L3)** | Qwen 2.5 7B (4.7) + Phi-4 Mini (2.8) | 7.5 GB | Standard agentic loop (need-based: Phi-4 loads only during audit) |
 | **Vision Full** | MiMo-VL-7B-RL (5.7) | 5.7 GB | Flagship VLM â€” Thinking + Creative + General |
 | **Vision OCR** | Qwen2-VL OCR 2B (1.1) | 1.1 GB | Fast document/OCR â€” dedicated lightweight |
 | **Fast (L0+L2)** | DeepScaler-1.5B (1.1) + Ministral-3B (2.2) | 3.3 GB | Rapid response |
 | **Verification (Expert)** | DeepSeek-R1-8B (5.1) + math-mini (0.45) | 5.55 GB | Phase 1.0.24 â€” Expert math audit |
 | **Verification (Light)** | SmolLM3-3B (1.9) + qwq-math (0.4) | 2.3 GB | Phase 1.0.24 â€” Rapid math audit |
 | **Idle** | Nomic (0.5) + Jina (0.6) | 1.1 GB | Background retrieval only |

### Sequential Loading & Recovery Protocol

- **Strict Prohibition:** Concurrent loading of multiple heavy models (>3 GB) is forbidden.
- **Dynamic Eviction:** Morpheus uses `EVICTION_ORDER` to prune low-priority models (L3/Vision) before loading mission-critical Tier 2 models.
- **OOM Resilience:** Automatic CUDA OOM detection triggers `ModelLoader.flush()` and initiates emergency recovery via `deepscaler-1.5b` fallback.
- **CPU Offloading:** All background maintenance (Morpheus daemon, DB pruning, Spatial mapping) is pinned to E-cores (logical CPUs 12-15) via `psutil` to protect P-core code generation throughput.
- **TTL (Time-To-Live):** Models unused for 120 seconds are automatically evicted.

---

## 5. Performance Expectations by Task Type

 | Task | Recommended Model | Expected Latency | Stream Quality |
 | --- | --- | --- | --- |
 | Simple Q&A | DeepScaler 1.5B (Tier 0) | <800ms first token | Basic |
 | Code generation | Qwen 3.5 4B UD (Tier 2) | ~1.5s first token | High |
 | Logical audit | Phi-4 Mini UD (Tier 2) | ~1.5s first token | Structured |
 | Math verification (SymPy) | Deterministic | <10ms | N/A |
 | Math verification (LLM) | Qwen 2.5 Math 7B Q4 | ~2.5s first token | Step-by-step |
 | Semantic search | Nomic MoE + Jina v3 | ~2.1s total | Ranked results |
 | Scene analysis | MiMo-VL-7B-RL | ~3s first token | High (VLM flagship) |
 | Document OCR | Qwen2-VL OCR 2B | ~1.5s first token | Text extraction |
 | Tool dispatch | FunctionGemma 270M | <500ms | JSON structured. Supports `vram` {"flush": true} for GPU cleanup. |
 | Routing decision | Granite 3-2B | <400ms | Classification |
 | Sequential reasoning | Sequential Thinking MCP | ~500ms/step | Structured chain-of-thought |
 | Web page fetch (static) | Fetch MCP | ~2-5s | Markdown + readability |
 | Web page fetch (dynamic/SPA) | Playwright navigate | ~3-8s | Full browser render |
 | Knowledge graph query | KG-mem search_nodes | <200ms | Entity graph traversal |
 | GitHub code search | GitHub search_code | ~1-3s | Octokit API |
 | E2E browser test | Playwright full flow | ~2-15s | Multi-step, screenshots |
 | Browser codegen | Playwright codegen | Recording duration | Test file generation |

---

## 6. External Dependencies

 | Resource | Location | Contents |
 | --- | --- | --- |
 | Ollama Models (Blobs) | `D:\Google\AntiGravity\General Tools\OllamaModels\blobs\` | 108 files, ~74 GB â€” Managed GGUF blobs |
 | Raw GGUF Files | `D:\Google\AntiGravity\General Tools\` | 34 standalone GGUF files (D: SSOT) |
 | Ollama Modelfiles | `D:\Google\AntiGravity\General Tools\OllamaModels\` | 51 `.Modelfile` definitions (45 active) |
 | Vision Models | `D:\Google\AntiGravity\General Tools\VisionSandbox\` | MiMo-VL-7B (flagship), Qwen2.5-VL-3B, Qwen3-VL â€” ~18 GB |

---

## 7. Model Lifecycle & Deprecation

 | Model | Status | Reason |
 | --- | --- | --- |
 | `granite-4.1-8b:latest` | Blacklisted (fallback only) | Repeated VRAM claim mismatch, shadow verification failure |
 | `ms-marco-minilm:latest` | DEPRECATED | Replaced by Nomic+Jina cascade (Phase 11.18.9). Retained as dead code. |
 | `muscle/jina-reranker-v3-q8` | RENAMED | Now `jina-reranker-v3:latest` (Phase 11.18.14 â€” Model Registry Sync) |
 | `functiongemma-270m:latest` | Available | Tool calling, not actively integrated |
 | `deepseek-r1-qwen3-8b:latest` | Active | Phase 11.20 â€” R1 Qwen3 Hybrid expert |
 | `deepseek-math-7b:latest` | Active | Phase 11.20 â€” C-8 Entegre: No System Prompt, \boxed{} Soru/Cevap, temp=0.0 |
 | `tinyllama:latest` | Active | Phase 11.20 â€” Ultra-light OOM recovery, 0.7 GB |
 | `hermes-3-llama-3.1-8b:latest` | Available | Alternative L2, available if primary fails |
 | `mimo-7b-vl-ud:latest` | Aktif | VLM Flagship |
 | `mimo-7b-txt-ud:latest` | Aktif | Vision as Text Alias |
 | `qwen2.5-coder-3b-ud:latest` | Aktif | Coder High Quant Alias |
 | `qwen2.5-math-7b-q4:latest` | Aktif | Standard Math Auditor |


## 8. SLM MCP Tool Bridge

The SuperLocalMemory (SLM) MCP tool bridge provides 34 tools across 7 categories. All tools exposed via the mcp_slm_ prefix through ToolBridge in src/clotho/bridge/base.py. Dual-path fallback: SLM unhealthy -> LanceDB+Ollama+Jina.

### 8.1 Memory CRUD
- mcp_slm_remember - Store with semantic indexing
- mcp_slm_observe - Passive telemetry
- mcp_slm_update_memory / mcp_slm_delete_memory / mcp_slm_fetch

### 8.2 Retrieval
- mcp_slm_recall - 4-channel retrieval
- mcp_slm_search - FTS5 BM25
- mcp_slm_rerank - Cross-encoder
- mcp_slm_list_recent / mcp_slm_get_status

### 8.3 Session
- mcp_slm_session_init / mcp_slm_close_session
- mcp_slm_report_feedback / mcp_slm_report_outcome

### 8.4 Behavioral
- mcp_slm_get_assertions / mcp_slm_get_soft_prompts
- mcp_slm_reinforce_assertion / mcp_slm_contradict_assertion

### 8.5 Mesh P2P
- mcp_slm_mesh_peers/send/inbox/state/lock/summary/events/status

### 8.6 Skill Evolution
- mcp_slm_evolve_skill / mcp_slm_skill_health / mcp_slm_skill_lineage

### 8.7 Maintenance
- mcp_slm_run_maintenance / mcp_slm_forget / mcp_slm_consolidate_cognitive / mcp_slm_set_mode / mcp_slm_log_tool_event

---

## 9. LangGraph Ergon Nodes

11 node functions in src/clotho/ergon/, managed by src/clotho/orchestrator.py.

| Node | File | Role | Axis |
|------|------|------|------|
| negotiate_node | symmachia.py | DOD negotiation | 3 |
| vision_node | horasis.py | VLM pre-process | 14 |
| anchor_inject_node | kathedra.py | Context anchors | 5 |
| draft_node / expert_draft_node | grammateia.py | Draft generation | 1 |
| verify_node | deigma.py | GLiNER2 check | 11 |
| tool_exec_node | synergeia.py | Parallel dispatch | 2 |
| critique_node | elenchos.py | 3-pass L3 audit | 11 |
| refine_node | orthosis.py | Refinement | 1 |
| reflection_node | theoria.py | Meta-analysis | 8 |
| deadlock_resolver_node | aporia.py | Constraint relax | 10 |
| koinonia.py | (helper) | Verify utils | - |

---

## 10. Codebase Mapper

src/lachesis/mapper/ for Axis 5. ASTParser + CodebaseMapper + GraphManager. 250 modules, 6 circular deps, 0 layer violations.

---

## 11. Sequential Thinking MCP

MCP server for structured, revisable chain-of-thought reasoning. 1 tool: `sequentialthinking`.

**Call Convention:** All tools in sections 11-15 are named `{server}_{tool}` (e.g. `fetch_fetch`, `playwright_navigate`) for direct ToolBridge.execute() calls. Via MCP protocol clients, pass server and tool name as separate parameters instead. Run via npx (`@modelcontextprotocol/server-sequential-thinking`).

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `sequentialthinking` | thought, nextThoughtNeeded, thoughtNumber, totalThoughts, branchFromThought, branchId, needsRevising | Multi-step reasoning with branching and revision |

### Usage Rules
- Use for complex multi-step logic (debugging, architecture, trade-off analysis)
- Each call = one step; set `nextThoughtNeeded=true` to continue
- Branch via `branchFromThought` + `branchId` for alternative paths
- Revise via `needsRevising=true` to correct previous steps
- Not needed for simple linear CoT — use internal reasoning instead

---

## 12. Fetch MCP

MCP server for web page fetching with markdown conversion and robots.txt compliance. 1 tool: `fetch`. Install: `pip install mcp-server-fetch`.

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `fetch` | url, max_length=5000, raw=false, start_index=0 | Fetch URL as markdown or raw HTML |

### Usage Rules
- Default `max_length=5000`; increase for full articles (max 50000)
- Readability mode auto-extracts main content (removes nav, ads)
- Robots.txt enforced server-side
- Paginate with `start_index` for long pages
- **Priority**: `webfetch` (built-in) > `fetch` (MCP) > `playwright_navigate` (dynamic)

---

## 13. Knowledge Graph MCP (kg-mem)

MCP server for persistent entity-relation knowledge graph. 9 tools. Install: `npm install -g @modelcontextprotocol/server-memory`.

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `create_entities` | entities: [{name, entityType, observations}] | Bulk create entities |
| `create_relations` | relations: [{from, relationType, to}] | Bulk create relations |
| `add_observations` | observations: [{entityName, contents}] | Add observations to existing entities |
| `delete_entities` | entityNames: [string] | Remove entities by name |
| `delete_observations` | deletions: [{entityName, observations}] | Remove specific observations |
| `delete_relations` | relations: [{from, relationType, to}] | Remove specific relations |
| `read_graph` | (none) | Export full knowledge graph |
| `search_nodes` | query: string | Full-text search across entity names/types |
| `open_nodes` | names: [string] | Get full details for specific entities |

### Usage Rules
- Complements SLM/Mnemosyne (vector semantic) with explicit graph relationships
- **Priority**: `mcp_slm_recall` (semantic) > `kg-mem_*` (structured graph) > `semantic_store` (fallback)
- Prefer `search_nodes` for entity lookup, `open_nodes` for details
- DO NOT store secrets, API keys, or credentials in KG
- Use consistent entity naming (fully qualified names preferred)
- Standard relation types: `depends_on`, `implements`, `extends`, `configured_by`, `triggers`

---

## 14. GitHub MCP

MCP server for GitHub API integration via Octokit. 26 tools. Install: `npm install -g @modelcontextprotocol/server-github`.

### Repository & Files
| Tool | Purpose |
|------|---------|
| `create_or_update_file` | Create or update file (direct commit) |
| `get_file_contents` | Read file or directory contents |
| `push_files` | Multi-file commit to branch |
| `search_repositories` | Search repos by query |
| `fork_repository` | Fork to your account |
| `create_repository` | Create new repo |

### Branches & Commits
| Tool | Purpose |
|------|---------|
| `create_branch` | Create branch from ref |
| `list_commits` | Paginate branch commits |

### Issues
| Tool | Purpose |
|------|---------|
| `create_issue` | Open new issue |
| `list_issues` | Filter by state/labels/assignee |
| `update_issue` | Edit title/body/state/labels |
| `get_issue` | Get issue details |
| `search_issues` | Search issues + PRs |
| `add_issue_comment` | Comment on issue or PR |

### Pull Requests
| Tool | Purpose |
|------|---------|
| `create_pull_request` | Open new PR |
| `list_pull_requests` | Filter by state |
| `get_pull_request` | PR details |
| `merge_pull_request` | Merge (merge/squash/rebase) |
| `update_pull_request_branch` | Sync with base branch |
| `get_pull_request_files` | Changed files list |
| `get_pull_request_status` | CI checks status |
| `get_pull_request_comments` | Review comments |
| `get_pull_request_reviews` | Submitted reviews |
| `create_pull_request_review` | Submit review (approve/comment/request_changes) |

### Search
| Tool | Purpose |
|------|---------|
| `search_code` | Code search across GitHub |
| `search_users` | User search |

### Usage Rules
- GITHUB_TOKEN must be set in .env; server launched via `scripts/run_github_mcp.bat`
- PR-based workflow preferred: create_branch -> create_or_update_file -> create_pull_request
- NO direct pushes to main branch without L0 approval
- For local-only git ops, use built-in git tools (not GitHub MCP)
- Rate limits apply — batch operations where possible

---

## 15. Playwright MCP

MCP server for browser automation via Playwright. 33 tools across 8 categories. Install: `npm install -g @executeautomation/playwright-mcp-server`.

### Navigation & Page Control
| Tool | Purpose |
|------|---------|
| `playwright_navigate` | Navigate to URL (chromium/firefox/webkit, viewport, headless) |
| `playwright_go_back` | Browser back |
| `playwright_go_forward` | Browser forward |
| `playwright_close` | Close browser |
| `playwright_click_and_switch_tab` | Click link then switch to new tab |

### Element Interaction
| Tool | Purpose |
|------|---------|
| `playwright_click` | Click element by CSS selector |
| `playwright_fill` | Fill input field |
| `playwright_select` | Select `<select>` option |
| `playwright_hover` | Hover over element |
| `playwright_drag` | Drag element to target |
| `playwright_press_key` | Press keyboard key |
| `playwright_upload_file` | Upload file to input |

### Iframe Support
| Tool | Purpose |
|------|---------|
| `playwright_iframe_click` | Click inside iframe |
| `playwright_iframe_fill` | Fill input inside iframe |

### Content Extraction
| Tool | Purpose |
|------|---------|
| `playwright_get_visible_text` | Page visible text |
| `playwright_get_visible_html` | Sanitized HTML |
| `playwright_screenshot` | Screenshot (full-page, element, base64/PNG) |
| `playwright_save_as_pdf` | PDF export (A4/Letter) |
| `playwright_evaluate` | Execute JS in browser |

### Network Monitoring
| Tool | Purpose |
|------|---------|
| `playwright_expect_response` | Wait for response by URL pattern |
| `playwright_assert_response` | Validate expected response |
| `playwright_console_logs` | Retrieve console logs (filter, search) |

### HTTP Requests (browser context)
| Tool | Purpose |
|------|---------|
| `playwright_get` | HTTP GET with bearer token |
| `playwright_post` | HTTP POST with body |
| `playwright_put` | HTTP PUT |
| `playwright_patch` | HTTP PATCH |
| `playwright_delete` | HTTP DELETE |

### Viewport & Device
| Tool | Purpose |
|------|---------|
| `playwright_resize` | Resize viewport (manual or 143+ device presets) |
| `playwright_custom_user_agent` | Set custom User Agent |

### Code Generation
| Tool | Purpose |
|------|---------|
| `start_codegen_session` | Start Playwright codegen recording |
| `end_codegen_session` | End session, generate test file |
| `get_codegen_session` | Session info |
| `clear_codegen_session` | Clear without generating |

### Usage Rules
- ALWAYS call `playwright_navigate` first before any page interaction
- Always `playwright_close` at end of session to free browser resources
- For static content, prefer `fetch` or `webfetch` (lighter, no browser)
- Use `playwright_screenshot` for visual debugging and documentation
- `playwright_evaluate` only for trusted JS
- For API-only workflows, use dedicated HTTP tools, not browser automation

---

*Signature,*
**Antigravity (Phantom Logos)**
*Last Updated: 2026-05-25 [09:00 PM PT]*
*Status: All 45 models catalogued. Blobs: 108. MCP: 6 servers / 103 tools. Ergon: 11 nodes. Mapper: 250 modules.*
