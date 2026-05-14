---
name: vram-monitoring
description: Real-time tracking of hardware VRAM usage to maintain the 7.0 GB hygiene.
version: 1.1.0
license: MIT
compatibility: opencode
when_to_use:
  - Before any heavy model inference.
  - During periodic system health checks.
metadata:
  audience: developers
  tier: L1-Morpheus
  workflow: monitoring
allowed-tools:
  - vram
  - report
---

# Skill: VRAM Monitoring

Ensures system stability by enforcing the 7.0 GB VRAM hard boundary.

## Workflow
1.  **Query**: Fetch telemetry data from the `vram` tool.
2.  **Verify**: Perform `_shadow_verify_claim` to ensure model-reported VRAM matches hardware state.
3.  **Alert**: If free VRAM < 500 MB, trigger an immediate `Morpheus.flush()`.
4.  **Log**: Record usage patterns to the operational store (Axis 2).

## Guardrails
- Never ignore a VRAM overflow warning.
- Maintain the 1.0 GB Windows OS reservation at all costs.
- Report any persistent leaks (>100MB/min) to L0 immediately.

## Output Format
- Allocated vs. Free VRAM in GB.
- Integrity status (Shadow Verification Result).
- Recommended actions (None, Flush, or Terminate).
