---
name: system-vram-profiler
description: Predictive VRAM and NGL analysis for local model optimization.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- vram
- report
- mcp_slm_remember
- run_code
tier: 2
---
# Skill: System VRAM Profiler (Sovereign Edition)

Profiles task complexity against hardware headroom to prevent Out-Of-Memory (OOM) errors via predictive NGL analysis.

## Workflow
1.  **Baseline**: Get current VRAM usage from Morpheus telemetry.
2.  **Predict**: Estimate the VRAM delta for the target model tier based on parameter count.
3.  **Validate**: Verify that the proposed NGL (Offloading) level does not exceed 7.0 GB total usage.

## Guardrails
- **NGL Safety**: Never recommend an NGL level that leaves < 500MB headroom during peak inference.
- **OOM Block**: Trigger a hard-block if the predicted usage exceeds 7.5 GB (Critical limit).
- **Stability**: Ensure the system preserves 1.0 GB for the OS at all times.

## Output Format
- `predicted_vram_gb`: Estimated memory footprint.
- `ngl_recommendation`: Optimized NGL value for llama.cpp.
- `oom_risk`: Risk level (LOW, MEDIUM, HIGH, CRITICAL).
