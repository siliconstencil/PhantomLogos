---
name: resource-scheduling
description: Optimizing task execution based on available hardware and token budgets.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- vram
- report
- mcp_slm_remember
- ls
tier: 2
---
# Skill: Resource Scheduling (Sovereign Edition)

Orchestrates the distribution of computational load based on real-time hardware constraints and RuFlow tiers.

## Workflow
1.  **VRAM Audit**: Query `vram` tool for current Morpheus cache status.
2.  **Tier Mapping**: Assign task to a RuFlow Tier (0-3) based on complexity and VRAM headroom.
3.  **Schedule**: Determine if a model flush/load is required for the chosen tier.

## Guardrails
- **7.0 GB Hygiene**: Never exceed 7.0 GB total VRAM usage.
- **OS Reservation**: Maintain 1.0 GB VRAM free for Windows system stability.
- **Eviction**: Follow LRU (Least Recently Used) order for model offloading.

## Output Format
- `selected_tier`: RuFlow tier (0, 1, 2, or 3).
- `vram_headroom_gb`: Remaining VRAM after operation.
- `load_action`: Action taken (LOAD, FLUSH, or REUSE).
