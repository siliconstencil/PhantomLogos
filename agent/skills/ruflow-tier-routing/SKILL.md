---
name: ruflow-tier-routing
description: Complexity-based model routing (Tier 0-3) logic following the RuFlow architecture.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Determining the optimal model for a specific sub-task.
  - Balancing VRAM efficiency vs reasoning depth.
  - Escalating a failing Tier 2/3 task to Tier 1 (Sophia).
metadata:
  audience: architects
  tier: L1-Sophia
  workflow: routing
---
# Skill: RuFlow Tier Routing

Orchestrates task distribution across the 4-tier model architecture to maximize reasoning quality while adhering to the 7.0 GB VRAM hygiene limit.

## Workflow
1.  **Complexity Analysis**: Evaluate the task based on Axis 11 (Math/Logic) and Axis 5 (Spatial) requirements.
2.  **Tier Assignment**:
    - **Tier 0 (Ultra-Light)**: Routine tasks, syntax checks (e.g., DeepSeek-1.5B).
    - **Tier 1 (Light)**: Fast reasoning, template generation (e.g., Ministral-3B).
    - **Tier 2 (Primary/Runner)**: Standard coding and tool execution (e.g., Qwen-7B / Clotho).
    - **Tier 3 (Expert)**: Complex architectural decisions and high-logic verification (e.g., Cloud Gateway / Qwen-3.5-9B).
3.  **Lachesis Audit**: Tasks requiring formal verification are routed for a need-based audit by the L3-Auditor layer (Lachesis).
4.  **VRAM Check**: Consult `resource-scheduling` to ensure the selected model can be loaded within the 7GB budget.
5.  **Telemetry**: Log the routing decision and outcome to Axis 7.

## Guardrails
- **Hardware Boundary**: Never route to a heavy model if current VRAM usage is > 6.0 GB unless a flush is scheduled.
- **Sovereignty**: Strategic changes to the plan (Implementation Plan edits) MUST be routed to Tier 1.
- **Deterministic**: Always use temperature=0 for Tier 3 verification tasks.

## Output Format
- `assigned_tier`: Integer (0, 1, 2, or 3).
- `reasoning_model`: Name of the selected model.
- `complexity_score`: Floating point (0.0 - 1.0) based on task analysis.
- `escalation_triggered`: Boolean indicating if this was an upgrade from a lower tier.
