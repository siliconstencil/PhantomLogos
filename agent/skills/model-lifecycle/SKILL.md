---
name: model-lifecycle
description: Managing local model loading, offloading, and flushing to optimize VRAM.
version: 1.1.0
license: MIT
compatibility: opencode
when_to_use:
  - Switching between heavy models (e.g., Vision to Reasoning).
  - VRAM usage exceeds 6.0 GB threshold.
metadata:
  audience: developers
  tier: L1-Morpheus
  workflow: resource-management
---

# Skill: Model Lifecycle

Optimizes VRAM usage through proactive loading and offloading of local models.

## Workflow
1.  **Monitor**: Check current VRAM usage via `vram` tool.
2.  **Evaluate**: Determine if the requested model fits within the 7.0 GB budget.
3.  **Flush**: Call `Morpheus.flush()` before loading a heavy model (>3 GB).
4.  **Load**: Initialize the model via Ollama with dynamic NGL offloading.

## Guardrails
- 1.0 GB VRAM MUST be reserved for system stability.
- Consecutive heavy model loads WITHOUT a flush are strictly forbidden.
- Use `nvidia-smi` (via run_code) as secondary verification if `vram` tool is ambiguous.

## Output Format
- Current VRAM status.
- Load/Unload action log.
- Confirmation of successful model transition.
