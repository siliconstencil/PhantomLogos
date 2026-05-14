# Phantom Logos: Local Model Ecosystem & Performance Matrix (Muscle)
[01:35 AM PT] | Status: **Sovereign Baseline**

## 1. Quantization & Benchmark Notes

All models below use GGUF quantization (Q4_K_M, Q5_K_XL, Q6_K, Q8_0). Benchmark scores are taken from official model publications and represent base-model accuracy at full precision. **Quantized models exhibit -2% to -5% degradation** on complex reasoning tasks compared to FP16 baselines. Unsloth Dynamic (UD) variants preserve critical layers, minimizing this gap for attention-heavy workloads.

| Format | Strategy | Performance Loss | VRAM Savings |
|--------|----------|-----------------|--------------|
| **Q4_K_M** | Medium quality, most VRAM-efficient | ~3-5% | 4-bit (~50% of FP16) |
| **Q5_K_XL** | Extra-large, slightly better than Q5_K_M | ~2-3% | 5-bit (~55% of FP16) |
| **Q6_K** | High quality, recommended for verification | ~1-2% | 6-bit (~62% of FP16) |
| **Q8_0** | Maximum quality (embedding/reranker) | ~0-1% | 8-bit (~70% of FP16) |
| **UD (Unsloth Dynamic)** | Adaptive per-layer bit-width | ~1-3% (better than uniform) | Variable (Pareto-optimal) |

---

## 2. Active Model Inventory & Performance Matrix

### 2.1 Reasoning Core (L0-L2)

| Model | VRAM | MMLU | HumanEval | MATH | Context | Tok/s | Role |
|-------|------|------|-----------|------|---------|-------|------|
| **Qwen 3.5 4B UD** `qwen3-5-4b-ud-q4_k_xl:latest` | 2.9 GB | 70% | 85% | — | 32K | ~30 | L2 Primary — Code generation, agentic loops |
| **Ministral 3B** `ministral-3-3b-reasoning-2512-ud-q4_k_xl` | 2.2 GB | 60% | — | — | 32K | ~35 | L2 Light — Rapid response, low complexity |
| **Hermes-3 Llama-8B** `hermes-3-llama-3-1-8b-q4_k_m` | 4.9 GB | 69% | 62% | — | 128K | ~16 | L2 Alternative — Strong tool use & function calling |
| **Qwen 3.5 9B** `qwen3-5-9b-ud-q4_k_xl:latest` | 6.0 GB | 78% | 75% | — | 32K | ~14 | L1 Local Alt — Deep local reasoning |
| **Llama 3.1 8B** `meta-llama-3-1-8b-instruct-q4_k_m` | 4.9 GB | 69% | 64% | — | 128K | ~17 | L2 Alternative — General purpose |
| **Nemotron-3 Nano 4B** `nemotron-3-nano-4b-ud-q6_k_xl` | 4.6 GB | 56% | — | — | 128K | ~25 | L2 Alternative — Light reasoning |
| **Qwen 3 4B** `qwen3-4b-ud-q6_k_xl:latest` | 3.7 GB | 73% | — | — | 32K | ~28 | L2 Alternative — Balanced |
| **DeepSeek-R1-Distill-Qwen 7B** `deepseek-r1:7b` | 4.7 GB | 65% | 70% | 92.8% | 32K | ~18 | L2 R1 Reasoning — CoT, math, code, temp=0.6 |

### 2.2 Ultra-Light Tier (L0)

| Model | VRAM | MMLU | HUMANEVAL | Context | Tok/s | Role |
|-------|------|------|-----------|---------|-------|------|
| **DeepScaler 1.5B** `deepscaler-1-5b-preview-q4_k_m:latest` | 1.1 GB | — | — | 8K | ~45 | L0 Primary — Math-first reasoning, fast |
| **DeepSeek-R1-Distill-Qwen 1.5B** `deepseek-r1-distill-qwen-1-5b-q8_0:latest` | 1.9 GB | 40% | 38% | 32K | ~48 | L0 Fallback — Chain-of-thought reasoning |
| **Qwen 3.5 0.8B** `qwen3-5-0-8b-ud-q8_k_xl:latest` | 1.2 GB | 55% | — | 32K | ~55 | L0 Alternative — Newer architecture |
| **SmolLM2 1.7B** `smollm2-1.7b:latest` | 1.2 GB | 40% | — | 8K | ~60 | L0 Alternative — Tiny generalist |
| **Llama 3.2 1B** `llama-3-2-1b-instruct-ud-q5_k_xl:latest` | 0.9 GB | 38% | 36% | 128K | ~70 | L0 Alternative — Long context, tiny |
| **TinyLlama 1.1B** `tinyllama:latest` | 0.7 GB | 26% | 36% | 2K | ~70 | L0 Extreme — OOM recovery, smallest footprint, temp=0.7 |

### 2.3 Auditor & Verification (L3 / Axis 11)

| Model | VRAM | MMLU-PRO | MATH | Context | Tok/s | Role |
|-------|------|----------|------|---------|-------|------|
| **Phi-4 Mini** `phi-4-mini-reasoning-ud-q5_k_xl:latest` | 2.8 GB | 79% | — | 16K | ~25 | L3 Primary — Adversarial auditing, critique |
| **Qwen 2.5 Coder 3B** `qwen2-5-coder-3b-instruct-q6_k:latest` | 2.5 GB | 65% | — | 32K | ~35 | Axis 11 — Code logic audit (QWED) |
| **Qwen 2.5 Math 7B** `qwen2.5-math-7b:latest` | 4.7 GB | — | 52% | 4K | ~15 | Axis 11 — Natural language math verification |
| **DeepSeek-Math 7B** `deepseek-math:7b` | 4.7 GB | — | 51.7% | 4K | ~18 | Axis 11 — C-8 Entegre: \boxed{} Soru/Cevap, temp=0.0 |
| **Qwen 2.5 Coder 0.5B** `qwen2.5-coder-0.5b:latest` | 0.5 GB | 44% | 42% | 32K | ~80 | Axis 11 — Rapid deterministic fallback |
| **Qwen 2.5 Coder 0.5B** `qwen2.5-coder-0.5b-q5_k_m:latest` | 0.5 GB | 44% | 42% | 32K | ~80 | Axis 11 — Q5 variant (alternative) |
| **Qwen 3.5 2B** `qwen3-5-2b-ud-q6_k_xl:latest` | 1.9 GB | 65% | — | 32K | ~40 | Axis 11 — Light verification alternative |
| **Qwen 3.5 4B** `qwen3-5-4b-ud-q4_k_xl:latest` | 2.9 GB | 70% | — | 32K | ~30 | Axis 11 — Verification alternative |
| **Qwen 2.5 Coder 3B** `qwen2-5-coder-3b-instruct-q4_k_m:latest` | 2.1 GB | 65% | — | 32K | ~38 | Axis 11 — Lighter quantization variant |
| **DeepSeek-R1-8B** `deepseek-r1-8b:latest` | 5.1 GB | 78% | 85% | 94.5% | 32K | ~16 | Axis 11 — [Phase 1.0.24] Reasoning + Math expert |
| **Open-Xi-Math** `open-xi-math:latest` | 1.1 GB | — | — | 92.0% | 8K | ~18 | Axis 11 — [Phase 1.0.24] High-fidelity math verification |
| **SmolLM3-3B** `smollm3-3b:latest` | 1.9 GB | 60% | — | — | 8K | ~35 | Axis 11 — [Phase 1.0.24] Fast math/reasoning |
| **Qwen2.5-Math-1.5B** `qwen2.5-math-1.5b:latest` | 1.1 GB | — | — | 88.0% | 4K | ~45 | Axis 11 — [Phase 1.0.24] Small specialized math |
| **math-mini-0.6B** `math-mini-0.6b:latest` | 0.45 GB | — | — | — | 4K | ~60 | Axis 11 — [Phase 1.0.24] Ultra-light math fallback |
| **qwq-math-io-500m** `qwq-math-io-500m:latest` | 0.4 GB | — | — | — | 4K | ~70 | Axis 11 — [Phase 1.0.24] Minimalist math bridge |

### 2.4 Vision Pipeline (LocalRuntime &amp; Ollama)

| Model | VRAM | OCR | Scene | Diagram | MMMU | OlympiadBench | MATH | Runtime | Role |
|-------|------|-----|-------|---------|------|---------------|------|---------|------|
| **Qwen2-VL OCR 2B** `qwen2-vl-ocr:latest` | 1.1 GB | ++ | + | — | — | — | — | Ollama | Document reading, dense text extraction |
| **Qwen2.5-VL 3B** `qwen2.5-vl:latest` | 2.5 GB | + | ++ | + | — | — | — | Ollama | Light fallback, general vision |
| **MiMo-VL-7B-RL** `mimo-vl:latest` | 5.7 GB | ++ | ++ | ++ | 70.6 | 59.4 | 95.4 | LocalRuntime | **Flagship VLM** — Thinking + Creative + Primary, temp=0.3 |

### 2.5 Embedding, Reranking &amp; Tool Calling

| Model | VRAM | MTEB | Cross-Encoder | Context | Role |
|-------|------|------|---------------|---------|------|
| **Nomic Embed v2 MoE Q8** `nomic-embed-text-v2-moe-q8:latest` | 0.5 GB | 69% | — | 8192 | Axis 6 — Semantic memory embedding |
| **Nomic Embed v2 MoE Q16** `nomic-embed-text-v2-moe-q16:latest` | 1.0 GB | 70% | — | 8192 | Axis 6 — Quality embedding (high-accuracy) |
| **Jina Reranker v3** `jina-reranker-v3-q8_0:latest` | 0.6 GB | — | 60%+ | 8192 | Axis 6 — Search result refinement |
| **Jina Embeddings v3** `jina-embeddings-v3-q8_0:latest` | 0.6 GB | 65% | — | 8192 | Axis 6 — Alternative embedding |
| **MS-MARCO MiniLM** `ms-marco-minilm:latest` | 0.09 GB | — | 45%+ | 512 | Reranker — DEPRECATED (Nomic+Jina cascade active) |
| **FunctionGemma 270M** `functiongemma-270m-it-q8_0:latest` | 0.3 GB | — | — | 8192 | Tool calling — Structured JSON function dispatch |
| **Granite 3.0 2B** `granite-3-0-2b-instruct-q4_k_m:latest` | 1.6 GB | 55% | — | 8192 | Router — Capability-based task routing |

### 2.6 Fallback &amp; Alternative Models

| Model | VRAM | MMLU | Context | Tok/s | Role |
|-------|------|------|---------|-------|------|
| **Granite 4.1 8B** `granite-4.1-8b:latest` | 5.5 GB | 73% | 128K | ~15 | L2 Fallback — Draft fallback (blacklisted pending fix) |
| **Llama 3.2 3B** `llama-3-2-3b-instruct-ud-q4_k_xl:latest` | 2.1 GB | 62% | 128K | ~35 | L2 Light Alternative — Long context |

---

## 2.7 Model Configuration Rules (Tokenizer & Parameters)

These rules are critical for correct model behavior. Violations cause silent degradation (garbage output, endless repetition, refusal to reason).

| Model | Tokenizer/Ozellik | Zorunlu Ayar | Aciklama |
|-------|------------------|-------------|----------|
| **R1 Serisi** (`deepseek-r1:7b`, `deepseek-r1-distill-qwen-1-5b-q8_0`) | Ozel `<think>` mekanizmasi | **Cikti basina `<think>\n` prefix; System prompt KULLANMA; temp=0.6** | R1 reasoning loop'u tetiklemek icin cikti `\`<think\`>\n\` ile baslamali. System prompt eklenirse thinking pattern'i atlar, dogrudan cevap verir. |
| **DeepSeek-Math** (`deepseek-math:7b`) | `\`<｜begin▁of▁sentence｜>\`` (bos), `\`<｜end▁of▁sentence｜>\`` (eos) | **System prompt KULLANMA; temp=0.0; MATH sorusu `\boxed{}` ile bitmeli** | Kendi tokenizer'i DeepSeek-Coder tabanli. System prompt eklenirse tensor uyumsuzlugu olabilir. Sadece 4096 context destegi. |
| **Qwen 2.5 Math 7B** (`qwen2.5-math-7b:latest`) | Qwen standard tokenizer | **temp=0.0; System prompt OPSIYONEL** | Math dogrulugu icin greedy decoding (temp=0.0) onerilir. Sadece 4K context (4096). |
| **TinyLlama** (`tinyllama:latest`) | `\`<|system|>\``, `\`<|user|>\``, `\`<|assistant|>\`` | **temp=0.7, top_k=50, top_p=0.95** | Llama 2 tokenizer'in birebir aynisi. System prompt desteklenir. 2K context limiti. |
| **DeepSeek-R1-Distill-Qwen-1.5B** | Ayni R1 kurallari | **Cikti basina `<think>\n` prefix; System prompt KULLANMA; temp=0.6** | 7B variant ile ayni kurallar. |
| **Qwen 3.5 4B UD** | Qwen standard tokenizer | **temp=0.2-0.4 (code); temp=0.0 (verification)** | Code generation icin dusuk temperature onerilir. |
| **Phi-4 Mini** | Microsoft tokenizer | **temp=0.2 (audit); temp=0.7 (creative)** | Audit/review gorevlerinde dusuk temperature, yaratıcı gorevlerde yuksek. System prompt destegi var. |
| **MiMo-VL** (`mimo-vl:latest`) | Qwen2.5-VL chat template | **temp=0.3, top_p=0.95; `/no_think` ile thinking kapatilir** | Xiaomi MiMo-VL-7B-RL. Gorsel input metinden ONCE gelmeli. System prompt GGUF icinde embedded. |
| **DeepSeek-R1-8B** | R1 standard tokenizer | **temp=0.6; System prompt KULLANMA** | Distill variantlarla ayni kurallar. |
| **qwq-math-io-500m** | Qwen tokenizer | **temp=0.0; top_p=0.95** | Math bridge, greedy decoding zorunlu. |

---

## 3. RuFlow 3-Tier + Ultra-Light Routing Strategy

| Tier | Label | Agent | Primary Model | VRAM | Fallback |
|------|-------|-------|--------------|------|----------|
| **Tier 0** | Ultra-Light | Fast response, skip audit | `deepscaler-1-5b-preview-q4_k_m` | 1.1 GB | `deepseek-r1-distill-qwen-1-5b-q8_0` |
| **Tier 1** | Light | Rapid, low-latency | `ministral-3-3b-reasoning-2512-ud-q4_k_xl` | 2.2 GB | `llama-3-2-3b-instruct-ud-q4_k_xl` |
| **Tier 2** | Primary | Standard agentic loops | `qwen3-5-4b-ud-q4_k_xl:latest` | 2.9 GB | `granite-4.1-8b:latest` |
| **Tier 3** | Expert (Cloud) | Deep reasoning | `models/antigravity-strategic-gateway` | — | `qwen3-5-9b-ud-q4_k_xl:latest` (local) |

### Tier Selection Rules
- Complexity < 0.3 or VRAM < 2 GB → **Tier 0** (skip tools, skip verification)
- Complexity 0.3-0.5 → **Tier 1** (tools enabled, lightweight)
- Complexity 0.5-0.8 → **Tier 2** (full tool access, full verification)
- Complexity > 0.8 → **Tier 3** (expert reasoning, cloud preferred)

---

## 4. VRAM Budget &amp; Loading Policy

| Component | GB | Notes |
|-----------|-----|-------|
| Total GPU VRAM | 8.0 | RTX 4070 Laptop GDDR6 |
| Windows OS reservation | 1.0 | Driver + composition + explorer |
| Always resident | 1.1 | Nomic Embed (0.5) + Jina Reranker (0.6) |
| **Available for LLMs** | **5.9** | Max 2 concurrent LLMs (3-5 GB each) |

### Operating Modes

| Mode | Active Models | VRAM | Use Case |
|------|--------------|------|----------|
| **Default (L2+L3)** | Qwen-7b (4.7) + Phi-4 Mini (2.8) | 7.5 GB | Standard agentic loop (need-based: Phi-4 loads only during audit) |
| **Vision Full** | MiMo-VL-7B-RL (5.7) | 5.7 GB | Flagship VLM — Thinking + Creative + General |
| **Vision OCR** | Qwen2-VL OCR 2B (1.1) | 1.1 GB | Fast document/OCR — dedicated lightweight |
| **Fast (L0+L2)** | DeepScaler-1.5B (1.1) + Ministral-3B (2.2) | 3.3 GB | Rapid response |
| **Verification (Expert)** | DeepSeek-R1-8B (5.1) + math-mini (0.45) | 5.55 GB | Phase 1.0.24 — Expert math audit |
| **Verification (Light)** | SmolLM3-3B (1.9) + qwq-math (0.4) | 2.3 GB | Phase 1.0.24 — Rapid math audit |
| **Idle** | Nomic (0.5) + Jina (0.6) | 1.1 GB | Background retrieval only |

### Sequential Loading & Recovery Protocol
- **Strict Prohibition:** Concurrent loading of multiple heavy models (>3 GB) is forbidden.
- **Dynamic Eviction:** Morpheus uses `EVICTION_ORDER` to prune low-priority models (L3/Vision) before loading mission-critical Tier 2 models.
- **OOM Resilience:** Automatic CUDA OOM detection triggers `ModelLoader.flush()` and initiates emergency recovery via `deepscaler-1-5b` fallback.
- **CPU Offloading:** All background maintenance (Morpheus daemon, DB pruning, Spatial mapping) is pinned to E-cores (logical CPUs 12-15) via `psutil` to protect P-core code generation throughput.
- **TTL (Time-To-Live):** Models unused for 120 seconds are automatically evicted.

---

## 5. Performance Expectations by Task Type

| Task | Recommended Model | Expected Latency | Stream Quality |
|------|------------------|-----------------|----------------|
| Simple Q&amp;A | DeepScaler 1.5B (Tier 0) | <800ms first token | Basic |
| Code generation | Qwen 3.5 4B UD (Tier 2) | ~1.5s first token | High |
| Logical audit | Phi-4 Mini (Tier 2) | ~1.5s first token | Structured |
| Math verification (SymPy) | Deterministic | <10ms | N/A |
| Math verification (LLM) | Qwen 2.5 Math 7B | ~2.5s first token | Step-by-step |
| Semantic search | Nomic MoE + Jina v3 | ~2.1s total | Ranked results |
| Scene analysis | MiMo-VL-7B-RL | ~3s first token | High (VLM flagship) |
| Document OCR | Qwen2-VL OCR 2B | ~1.5s first token | Text extraction |
| Tool dispatch | FunctionGemma 270M | <500ms | JSON structured |
| Routing decision | Granite 3.0 2B | <400ms | Classification |

---

## 6. External Dependencies

| Resource | Location | Contents |
|----------|----------|---------|
| Ollama Models (Blobs) | `D:\Google\AntiGravity\General Tools\OllamaModels\blobs\` | 73 files, ~67 GB — Managed GGUF blobs |
| Raw GGUF Files | `D:\Google\AntiGravity\General Tools\` | 32 standalone GGUF files (not in Ollama) |
| Ollama Modelfiles | `D:\Google\AntiGravity\General Tools\OllamaModels\` | 41 `.Modelfile` definitions |
| Vision Models | `D:\Google\AntiGravity\General Tools\VisionSandbox\` | MiMo-VL-7B-RL (flagship), Qwen2.0-2B, Qwen2.5-3B, Qwen3-4B, Gemma4B — ~17 GB |

---

## 7. Model Lifecycle &amp; Deprecation

| Model | Status | Reason |
|-------|--------|--------|
| `granite-4.1-8b:latest` | Blacklisted (fallback only) | Repeated VRAM claim mismatch, shadow verification failure |
| `ms-marco-minilm:latest` | DEPRECATED | Replaced by Nomic+Jina cascade (Phase 11.18.9). Retained as dead code. |
| `muscle/jina-reranker-v3-q8` | RENAMED | Now `jina-reranker-v3-q8_0:latest` (Phase 11.18.14 — Model Registry Sync) |
| `functiongemma-270m-it-q8_0:latest` | Available | Tool calling, not actively integrated |
| `deepseek-r1:7b` | Active | Phase 11.20 — R1 reasoning, CoT math/code |
| `deepseek-math:7b` | Active | Phase 11.20 — C-8 Entegre: No System Prompt, \boxed{} Soru/Cevap, temp=0.0 |
| `tinyllama:latest` | Active | Phase 11.20 — Ultra-light OOM recovery, 0.7 GB |
| `hermes-3-llama-3-1-8b-q4_k_m:latest` | Available | Alternative L2, available if primary fails |
| `mimo-vl:latest` | Active | Phase 11.20 — Replaces Qwen3-VL + Gemma4 + Qwen2.5-VL as flagship VLM |
| `qwen3-vl-thinking-ud` | BYPASSED | Replaced by MiMo-VL-7B-RL v2. GGUFs retained on disk |
| `gemma-4-e4b-it-ud` | BYPASSED | Replaced by MiMo-VL-7B-RL. GGUFs retained on disk |

---

*Signature,*
**Antigravity (Phantom Logos)**
*Last Updated: 2026-05-10 [02:30 PM PT]*
*Status: All 37 models catalogued and rated. Vision Flagship: MiMo-VL.*
