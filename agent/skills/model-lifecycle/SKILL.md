---
name: model-lifecycle
description: Managing local model loading, offloading, and flushing to optimize VRAM.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Transitioning between heavy models (e.g., Qwen 7B to Phi-4).
  - Explicitly clearing memory before critical operations.
metadata:
  audience: system-admins
  tier: Morpheus
  workflow: lifecycle
---
# Skill: Model Lifecycle
Ensures deterministic model management and OOM prevention.
