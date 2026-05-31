# Phantom Logos - Local and Hybrid Operation Guide

This document provides instructions on how to configure, switch, and run Phantom Logos in either Cloud-Hybrid mode or Pure Local (offline) mode, including external CLI configurations such as OpenCode CLI.

---

## 1. Overview of Modes

Phantom Logos is designed with a dual-path architecture ("Cloud Brain + Local Brain + Local Muscle").

1. **Cloud-Hybrid Mode (Default)**: Strategic planning and high-complexity reasoning tasks are routed to the cloud gateway via the local proxy, while local tools, memory indexes, and verifiers run locally on your machine.
2. **Pure Local (Offline) Mode**: 100% of the reasoning, code generation, embedding, and tool execution runs locally on your machine (via Ollama and local binaries). No internet connection or cloud API keys are required.

---

## 2. Configuration & Switching Modes

### Setting up Pure Local Mode

To run in 100% offline local-only mode, configure your `.env` file at the project root as follows:

1. **Remove or comment out all Cloud API keys**:
   ```env
   # Leave these keys blank or delete them to disable cloud routing
   GEMINI_API_KEY=
   DEEPSEEK_API_KEY=
   HF_TOKEN=
   GITHUB_PERSONAL_ACCESS_TOKEN=
   ```

2. **Configure Ollama and local models**:
   Ensure Ollama is running locally (`http://localhost:11434`) and that you have downloaded the required local models.

3. **Configure Local Model Directory**:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL_DIR=D:/Google/AntiGravity/General Tools/OllamaModels
   GPU_TOTAL_VRAM_GB=7.0
   ```

---

## 3. The Automatic Fallback Architecture

Even if Cloud-Hybrid mode is enabled, the system is designed to gracefully handle network failures or API rate limits:

* **Circuit Breaker**: If the primary cloud gateway times out (90s) or returns connection errors (refused, remote protocol), the system's `CircuitBreaker` triggers.
* **Local Failover**: The async gateway (`AriadneAsyncGateway`) immediately redirects the prompt to `_local_fallback` which runs the request on the local Ollama instance using the reasoning model (`qwen3.5-4b-ud:latest`).
* **Matryoshka Retrieval & Reranker Fallback**: If the SLM MCP server is down, memory retrieval and reranking automatically fall back to local LanceDB + Ollama Embeddings (`nomic-embed-text-v2-moe-q8:latest`) and local Jina Reranker models.

---

## 4. OpenCode CLI Pure Local Integration

OpenCode CLI serves as the primary external developer command-line interface. It can be fully connected to your local model setup to enable 100% offline terminal development without depending on any IDE.

### opencode.json Configuration
The `opencode.json` configuration file at the project root defines the local MCP servers and default settings:
* All tools (such as `filesystem`, `slm`, `fetch`, `github`, `playwright`) run locally via `.venv` or npm.
* OpenCode sessions and cross-session pattern recognition data are saved to the local SQLite database (`opencode.db` via Axis 13 `OpenCodeStore`).

### Connecting OpenCode CLI to Local Models
To run OpenCode CLI without external API calls, you can point the client to your local endpoints:

1. **OpenAI / DeepSeek Local Redirect**:
   If OpenCode is configured to use DeepSeek or OpenAI providers, you can set the environment variables in your terminal before running it:
   ```powershell
   $env:DEEPSEEK_API_BASE="http://localhost:11434/v1"
   $env:DEEPSEEK_API_KEY="ollama" # Ollama does not validate keys, any string works
   ```
   Or set the OpenAI endpoint to redirect to the local Sovereign Gateway proxy:
   ```powershell
   $env:OPENAI_API_BASE="http://localhost:32553/v1"
   $env:OPENAI_API_KEY="antigravity-native"
   ```

2. **Model Selection**:
   Update `opencode.json` to target a model available in your local Ollama registry:
   ```json
   "model": "ollama/qwen3.5-4b-ud:latest"
   ```

---

## 5. VRAM & Hardware Resource Management

When running purely locally, managing your GPU memory (VRAM) is crucial to avoid out-of-memory (OOM) errors and system freezes:

* **VRAMUsable Limit**: The system enforces a strict usable limit (Total VRAM - 1.0 GB safety margin for OS). For a 8 GB GPU, the limit is set to 7.0 GB.
* **Dynamic Offloading**: Models are loaded and unloaded dynamically by `ModelLoader`.
* **VRAM Sweeper**: The `VRAMSweeper` daemon runs in the background to detect VRAM fragmentation.
* **Manual Purge**: You can manually clear all models from the GPU VRAM by running:
  ```powershell
  .venv\Scripts\python scripts/morpheus_flush.py
  ```

---

## 6. Verification and Testing

### Verify Local Ollama Connection
To verify that your local Ollama daemon is active and responding, run:
```powershell
ollama list
```

### Run Local Fallback Verification Tests
You can run the automated unit and integration tests that validate offline fallback mechanisms:
```powershell
.venv\Scripts\pytest tests/test_gateway_circuit_breaker.py tests/test_slm_fallback.py
```
If these tests pass, the fallback architecture is functioning correctly.
