---
name: local-runtime
description: Managing llama.cpp subprocess runtime, dynamic NGL offloading, and local model lifecycle.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Running VLM models via llama.cpp subprocess.
  - Dynamic GPU layer offloading (-ngl) for VRAM stability.
  - Model loading/unloading in LocalRuntime.
  - Vision pipeline execution for MiMo-VL-7B-RL.
metadata:
  audience: developers
  tier: L2-Runner
  workflow: runtime
allowed-tools:
  - ls
  - shell
  - report
---
# Local Runtime (Muscle)

Manages the llama.cpp subprocess-based local inference runtime for models that cannot run via Ollama.

## Architecture

### Subprocess Management
- `LocalRuntime` spawns llama.cpp server as a child process.
- Dynamic `-ngl` parameter adjustment based on available VRAM.
- Automatic process cleanup on shutdown.

### Supported Models
- **MiMo-VL-7B-RL** (Flagship VLM, 5.7 GB)
- **Qwen2-VL OCR 2B** (Dedicated OCR, 1.1 GB)

### VRAM Safety
- Dry-run prediction before loading: `local_runtime.predict_vram(model_name)`.
- Automatic fallback to CPU-only if VRAM insufficient.
- `Morpheus.flush()` called before all heavy model transitions.

## Best Practices
- Always call `predict_vram()` before loading a model.
- Monitor subprocess health with `is_alive()`.
- Use `force_kill()` for unresponsive processes.
